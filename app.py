import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="LACOST V9 - Autónomo", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stSelectbox, .stNumberInput { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS INTEGRADOS (RESPALDO V9)
# ==========================================
# Estos datos se usan si no hay archivos externos. Así la app nunca falla.

DEFAULT_UI = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. General Info,-,Country,Dropdown,Yes,### TABLE: COUNTRIES(Country)
1. General Info,-,Currency,Radio,Yes,"USD, Local,### TABLE: COUNTRIES(E/R)"
1. General Info,-,Contract Start Date,Date,Yes,User imput
1. General Info,-,Contract End Date,Date,Yes,User imput
1. General Info,-,Contract Period,Number,Yes,Calculated
2. Input Costs,-,QA Risk,Dropdown,Yes,### TABLE: QA_RISK (Level)
2. Input Costs,Servicios,Offering,Dropdown,Yes,### TABLE: Offering(Offering)
2. Input Costs,Servicios,SLC,Dropdown,Yes,### TABLE: SLC(SLC)
2. Input Costs,Servicios,USD Unit Cost,Number,Yes,User imput
2. Input Costs,Servicios,SQty,Number,Yes,User imput
3. Input Costs,Labor RR/BR,RR/BR,Dropdown,Yes,### TABLE: LABOR(plat,def)
3. Input Costs,Labor RR/BR,LQty,Number,Yes,User imput
"""

DEFAULT_DB = """
### TABLE: COUNTRIES
Country,Currency,E/R
Argentina,ARS,1428.95
Brazil,BRL,5.34
Chile,CLP,934.70
Colombia,COP,3775.22
Ecuador,USD,1.0
Peru,PEN,3.37
Mexico,MXN,18.42
Uruguay,UYU,39.73
Venezuela,VES,235.28

### TABLE: QA_RISK
Level,Percentage
Low,0.02
Medium,0.05
High,0.08

### TABLE: Offering
Offering,L40
IBM Hardware Resell,6942-1BT
IBM Support for Red Hat,6948-B73
IBM Customized Support HW,6942-76V
IBM Customized Support SW,6942-76W
Relocation Services,6942-54E

### TABLE: SLC
Scope,Desc,SLC,UPLF
no brazil,24X74On-site Response time,M47,1.5
no brazil,24X7SDOn-site arrival time,M19,1.0
no brazil,24X76Fix time,M2B,1.6
Brazil,24X7SDOn-site arrival time,M19,1.0
Brazil,NStd5x9,NStd5x9,1.0
Brazil,NStdSBD7x24,NStdSBD7x24,1.278

### TABLE: LABOR
Scope,Item,Argentina,Brazil,Colombia,Ecuador,Peru
All,System Z,304504.2,2803.85,2054058.99,991.20,1284.60
All,Power HE,194856.48,1516.61,540008.96,340.52,505.85
All,B7 (Senior),40166.28,186.82,126000.0,79.19,216.45
All,B8 (Spec),65472.90,263.20,147000.0,303.04,518.36
"""

# ==========================================
# 2. GESTOR DE CARGA (HÍBRIDO)
# ==========================================

@st.cache_data
def load_data(ui_file, db_file):
    # --- 1. PROCESAR UI ---
    if ui_file:
        df_ui = pd.read_csv(ui_file)
    else:
        # Usar datos integrados
        df_ui = pd.read_csv(io.StringIO(DEFAULT_UI))
    
    # Limpieza headers
    df_ui.columns = df_ui.columns.str.strip()

    # --- 2. PROCESAR DB ---
    tables = {}
    current_content = db_file.getvalue().decode("utf-8") if db_file else DEFAULT_DB
    
    # Parser manual de tablas ### TABLE:
    current_table = None
    buffer = []
    
    for line in current_content.splitlines():
        line = line.strip()
        if "### TABLE:" in line:
            # Guardar anterior
            if current_table and buffer:
                try:
                    # Detectar csv simple
                    header = buffer[0].split(',')
                    rows = [r.split(',') for r in buffer[1:] if r.strip()]
                    # Ajustar filas
                    clean_rows = [r[:len(header)] for r in rows if len(r) >= len(header)]
                    tables[current_table] = pd.DataFrame(clean_rows, columns=header)
                except: pass
            
            # Nueva tabla
            raw_name = line.split("### TABLE:")[1]
            current_table = raw_name.split('(')[0].strip()
            buffer = []
        else:
            if line and current_table:
                buffer.append(line)

    # Guardar última tabla
    if current_table and buffer:
        try:
            header = buffer[0].split(',')
            rows = [r.split(',') for r in buffer[1:] if r.strip()]
            clean_rows = [r[:len(header)] for r in rows if len(r) >= len(header)]
            tables[current_table] = pd.DataFrame(clean_rows, columns=header)
        except: pass

    # Conversiones numéricas críticas
    if 'COUNTRIES' in tables:
        tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
    if 'SLC' in tables:
        tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')
    if 'LABOR' in tables:
        # Intentar convertir todo a numérico excepto las primeras columnas
        cols = tables['LABOR'].columns
        for c in cols:
            if c not in ['Scope', 'Item', 'Plat', 'Def']:
                tables['LABOR'][c] = pd.to_numeric(tables['LABOR'][c], errors='coerce')

    return df_ui, tables

# --- SIDEBAR OPCIONAL ---
with st.sidebar:
    st.header("📂 Datos")
    st.caption("La app ya tiene datos cargados. Si quieres usar tus propios CSV, súbelos aquí:")
    up_ui = st.file_uploader("UI_CONFIG.csv", type=['csv'])
    up_db = st.file_uploader("Databases.csv", type=['csv'])
    st.divider()

# Cargar (Prioridad: Subido > Integrado)
ui_df, db_tables = load_data(up_ui, up_db)

# ==========================================
# 3. LÓGICA V9 (LOOKUPS)
# ==========================================

def get_options(source_str, country_context):
    if pd.isna(source_str): return []
    source_str = str(source_str).strip()
    
    if "### TABLE:" not in source_str:
        return [x.strip() for x in source_str.split(',')] if "," in source_str else []

    parts = source_str.replace("### TABLE:", "").split('(')
    tbl_name = parts[0].strip()
    col_name = parts[1].replace(')', '').strip() if len(parts) > 1 else None
    
    if tbl_name not in db_tables: return []
    df = db_tables[tbl_name]
    
    # Scope Logic
    if 'Scope' in df.columns and country_context:
        target = "Brazil" if country_context == "Brazil" else "no brazil"
        # Filtro relajado (contains)
        df = df[df['Scope'].str.lower().str.contains(target.lower()) | (df['Scope'] == 'All')]

    if col_name and col_name in df.columns:
        return df[col_name].unique().tolist()
    
    # Fallback Labor
    if tbl_name == "LABOR":
        if 'Item' in df.columns: return df['Item'].unique().tolist()
    
    return []

def get_slc_factor(slc_val, country):
    if 'SLC' not in db_tables: return 1.0
    df = db_tables['SLC']
    target = "Brazil" if country == "Brazil" else "no brazil"
    
    # Buscar columna correcta
    col = next((c for c in ['SLC', 'Desc', 'ID_Desc'] if c in df.columns), None)
    if not col: return 1.0
    
    row = df[ 
        (df['Scope'].str.lower().str.contains(target.lower())) & 
        (df[col] == slc_val) 
    ]
    if not row.empty:
        return float(row['UPLF'].values[0])
    return 1.0

def get_labor_rate(item_val, country, er):
    if 'LABOR' not in db_tables: return 0.0
    df = db_tables['LABOR']
    
    # Buscar Item
    row = df[df['Item'] == item_val]
    if row.empty or country not in row.columns: return 0.0
    
    try:
        val = float(row[country].values[0])
        return val / er
    except: return 0.0

# ==========================================
# 4. RENDER UI
# ==========================================
st.title("💸 LACOST V9 (Ready)")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
global_vars = {'Country': 'Colombia', 'E/R': 3775.0, 'Duration': 12}

# Detectar columna source
src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

for section, group in ui_df.groupby('Section', sort=False):
    
    # Slide check
    if "-slide" in str(section).lower():
        cont = st.sidebar
        title = str(section).lower().replace("-slide", "").title()
    else:
        cont = st.container()
        title = str(section)
        
    with cont:
        st.header(title)
        for idx, row in group.iterrows():
            lbl = row['Field Label']
            dtype = str(row['Data Type']).strip()
            src = row[src_col]
            k = f"{section}_{lbl}_{idx}"
            
            if dtype == 'Dropdown':
                if lbl == 'Country':
                    opts = get_options(src, None)
                    val = st.selectbox(lbl, opts, key=k)
                    global_vars['Country'] = val
                    
                    if 'COUNTRIES' in db_tables:
                        c_df = db_tables['COUNTRIES']
                        c_row = c_df[c_df['Country'] == val]
                        if not c_row.empty:
                            raw_er = float(c_row['E/R'].values[0])
                            global_vars['E/R'] = 1.0 if val == "Ecuador" else raw_er
                            st.caption(f"Tasa: {global_vars['E/R']}")
                else:
                    opts = get_options(src, global_vars['Country'])
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.inputs[lbl] = val
            
            elif dtype == 'Date':
                val = st.date_input(lbl, date.today(), key=k)
                st.session_state.inputs[lbl] = val
            
            elif dtype == 'Number':
                if "Contract Period" in lbl or "Duration" in lbl:
                    try:
                        d1 = st.session_state.inputs.get('Contract Start Date', date.today())
                        d2 = st.session_state.inputs.get('Contract End Date', date.today())
                        diff = relativedelta(d2, d1)
                        m = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
                        st.number_input(lbl, value=m, disabled=True, key=k)
                        global_vars['Duration'] = m
                    except: st.number_input(lbl, value=0, key=k)
                else:
                    val = st.number_input(lbl, min_value=0.0, step=1.0, key=k)
                    st.session_state.inputs[lbl] = val
                    
            elif dtype == 'Radio':
                opts = [x.strip() for x in str(src).split(',') if "###" not in x]
                st.radio(lbl, opts, horizontal=True, key=k)

        if cont != st.sidebar: st.divider()

# ==========================================
# 5. CÁLCULO
# ==========================================
st.header("Resultados")
if st.button("Calcular"):
    try:
        inp = st.session_state.inputs
        
        # Mapping V9
        usd_cost = inp.get('USD Unit Cost', 0.0)
        sqty = inp.get('SQty', 0.0)
        slc = inp.get('SLC', '')
        lqty = inp.get('LQty', 0.0)
        labor_item = inp.get('RR/BR', '')
        
        # Calc
        uplf = get_slc_factor(slc, global_vars['Country'])
        serv_tot = usd_cost * sqty * uplf * global_vars['Duration']
        
        lab_rate = get_labor_rate(labor_item, global_vars['Country'], global_vars['E/R'])
        lab_tot = lab_rate * lqty
        
        grand = serv_tot + lab_tot
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Servicios", f"${serv_tot:,.2f}")
        c2.metric("Labor", f"${lab_tot:,.2f}")
        c3.metric("GRAN TOTAL", f"${grand:,.2f}")
        
    except Exception as e:
        st.error(f"Error: {e}")
