import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="LACOST V9 - Final", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stSelectbox, .stNumberInput { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS INTEGRADOS (A PRUEBA DE FALLOS)
# ==========================================
# En lugar de texto CSV, definimos los datos directamente para evitar errores de lectura.

def get_default_ui():
    data = [
        # Seccion 1
        {"Section": "1. General Info", "Sub-Section": "-", "Field Label": "Country", "Data Type": "Dropdown", "Source / Options": "### TABLE: COUNTRIES(Country)"},
        {"Section": "1. General Info", "Sub-Section": "-", "Field Label": "Currency", "Data Type": "Radio", "Source / Options": "USD, Local, ### TABLE: COUNTRIES(E/R)"},
        {"Section": "1. General Info", "Sub-Section": "-", "Field Label": "Contract Start Date", "Data Type": "Date", "Source / Options": "User imput"},
        {"Section": "1. General Info", "Sub-Section": "-", "Field Label": "Contract End Date", "Data Type": "Date", "Source / Options": "User imput"},
        {"Section": "1. General Info", "Sub-Section": "-", "Field Label": "Contract Period", "Data Type": "Number", "Source / Options": "Calculated"},
        # Seccion 2
        {"Section": "2. Input Costs", "Sub-Section": "-", "Field Label": "QA Risk", "Data Type": "Dropdown", "Source / Options": "### TABLE: QA_RISK (Level)"},
        {"Section": "2. Input Costs", "Sub-Section": "Servicios", "Field Label": "Offering", "Data Type": "Dropdown", "Source / Options": "### TABLE: Offering(Offering)"},
        {"Section": "2. Input Costs", "Sub-Section": "Servicios", "Field Label": "SLC", "Data Type": "Dropdown", "Source / Options": "### TABLE: SLC(SLC)"},
        {"Section": "2. Input Costs", "Sub-Section": "Servicios", "Field Label": "USD Unit Cost", "Data Type": "Number", "Source / Options": "User imput"},
        {"Section": "2. Input Costs", "Sub-Section": "Servicios", "Field Label": "SQty", "Data Type": "Number", "Source / Options": "User imput"},
        # Seccion 3
        {"Section": "3. Input Costs", "Sub-Section": "Labor RR/BR", "Field Label": "RR/BR", "Data Type": "Dropdown", "Source / Options": "### TABLE: LABOR(plat,def)"},
        {"Section": "3. Input Costs", "Sub-Section": "Labor RR/BR", "Field Label": "LQty", "Data Type": "Number", "Source / Options": "User imput"},
    ]
    return pd.DataFrame(data)

def get_default_db():
    tables = {}
    
    # Tabla COUNTRIES
    tables['COUNTRIES'] = pd.DataFrame({
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'E/R': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28]
    })
    
    # Tabla QA_RISK
    tables['QA_RISK'] = pd.DataFrame({
        'Level': ['Low', 'Medium', 'High'],
        'Percentage': [0.02, 0.05, 0.08]
    })
    
    # Tabla OFFERING
    tables['Offering'] = pd.DataFrame({
        'Offering': ['IBM Hardware Resell', 'IBM Support for Red Hat', 'IBM Customized Support HW', 'Relocation Services'],
        'L40': ['6942-1BT', '6948-B73', '6942-76V', '6942-54E']
    })
    
    # Tabla SLC
    tables['SLC'] = pd.DataFrame([
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response', 'SLC': 'M47', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival', 'SLC': 'M19', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival', 'SLC': 'M19', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'SLC': 'NStd5x9', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24', 'SLC': 'NStdSBD7x24', 'UPLF': 1.278}
    ])
    
    # Tabla LABOR
    tables['LABOR'] = pd.DataFrame([
        {'Scope': 'All', 'Item': 'System Z', 'Argentina': 304504.2, 'Brazil': 2803.85, 'Colombia': 2054058.99, 'Ecuador': 991.20},
        {'Scope': 'All', 'Item': 'Power HE', 'Argentina': 194856.48, 'Brazil': 1516.61, 'Colombia': 540008.96, 'Ecuador': 340.52},
        {'Scope': 'All', 'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Brazil': 186.82, 'Colombia': 126000.0, 'Ecuador': 79.19}
    ])
    
    return tables

# ==========================================
# 2. GESTOR DE CARGA
# ==========================================
@st.cache_data
def load_data(ui_file, db_file):
    # --- 1. PROCESAR UI ---
    if ui_file:
        try:
            # Usamos engine='python' para ser más tolerantes con formatos csv complejos
            df_ui = pd.read_csv(ui_file, engine='python')
            df_ui.columns = df_ui.columns.str.strip()
        except Exception as e:
            st.error(f"Error en archivo UI: {e}")
            df_ui = get_default_ui()
    else:
        df_ui = get_default_ui()

    # --- 2. PROCESAR DB ---
    if db_file:
        tables = {}
        try:
            content = db_file.getvalue().decode("utf-8")
            current_table = None
            buffer = []
            
            for line in content.splitlines():
                line = line.strip()
                if "### TABLE:" in line:
                    # Guardar anterior
                    if current_table and buffer:
                        try:
                            header = buffer[0].split(',')
                            # Limpieza headers vacíos
                            header = [h.strip() for h in header if h.strip()]
                            rows = [r.split(',') for r in buffer[1:] if r.strip()]
                            # Ajuste de columnas
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
            
            # Última tabla
            if current_table and buffer:
                try:
                    header = buffer[0].split(',')
                    header = [h.strip() for h in header if h.strip()]
                    rows = [r.split(',') for r in buffer[1:] if r.strip()]
                    clean_rows = [r[:len(header)] for r in rows if len(r) >= len(header)]
                    tables[current_table] = pd.DataFrame(clean_rows, columns=header)
                except: pass
                
            # Conversiones numéricas básicas
            if 'COUNTRIES' in tables:
                tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
            if 'SLC' in tables:
                tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')
            if 'LABOR' in tables:
                # Intentar convertir todo a num except strings conocidos
                for c in tables['LABOR'].columns:
                    if c not in ['Scope', 'Item', 'Plat', 'Def']:
                        tables['LABOR'][c] = pd.to_numeric(tables['LABOR'][c], errors='coerce')
                        
        except Exception as e:
            st.error(f"Error procesando DB File: {e}")
            tables = get_default_db()
    else:
        tables = get_default_db()

    return df_ui, tables

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Datos del Proyecto")
    st.caption("Usa archivos CSV opcionales o los datos por defecto.")
    up_ui = st.file_uploader("UI_CONFIG.csv", type=['csv'])
    up_db = st.file_uploader("Databases.csv", type=['csv'])
    st.divider()

# Cargar
ui_df, db_tables = load_data(up_ui, up_db)

# ==========================================
# 3. LÓGICA V9
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
    
    # Scope
    if 'Scope' in df.columns and country_context:
        target = "Brazil" if country_context == "Brazil" else "no brazil"
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
    
    row = df[df['Item'] == item_val]
    if row.empty or country not in row.columns: return 0.0
    
    try:
        val = float(row[country].values[0])
        return val / er
    except: return 0.0

# ==========================================
# 4. RENDER UI
# ==========================================
st.title("💸 LACOST V9 - Madre Edition")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
global_vars = {'Country': 'Colombia', 'E/R': 3775.0, 'Duration': 12}

# Detectar columna source con flexibilidad
src_cols = [c for c in ui_df.columns if 'Source' in c]
src_col = src_cols[0] if src_cols else 'Source'

for section, group in ui_df.groupby('Section', sort=False):
    
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
