import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="LACOST V9 - Corregido", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stNumberInput input { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS DE RESPALDO (CORREGIDOS)
# ==========================================
# Nota: He agregado "-slide" a la primera sección para que veas el efecto por defecto.

def get_default_ui():
    csv_data = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. General Info-slide,-,Country,Dropdown,Yes,### TABLE: COUNTRIES(Country)
1. General Info-slide,-,Currency,Radio,Yes,"USD, Local"
1. General Info-slide,-,Contract Start Date,Date,Yes,User imput
1. General Info-slide,-,Contract End Date,Date,Yes,User imput
1. General Info-slide,-,Contract Period,Number,Yes,Calculated
2. Input Costs,-,QA Risk,Dropdown,Yes,### TABLE: QA_RISK (Level)
2. Input Costs,Servicios,Offering,Dropdown,Yes,### TABLE: Offering(Offering)
2. Input Costs,Servicios,SLC,Dropdown,Yes,### TABLE: SLC(Desc)
2. Input Costs,Servicios,USD Unit Cost,Number,Yes,User imput
2. Input Costs,Servicios,SQty,Number,Yes,User imput
3. Input Costs,Labor RR/BR,RR/BR,Dropdown,Yes,### TABLE: LABOR(Item)
3. Input Costs,Labor RR/BR,LQty,Number,Yes,User imput
"""
    return pd.read_csv(io.StringIO(csv_data))

def get_default_db():
    # Simulamos la carga de tus tablas V9
    tables = {}
    tables['COUNTRIES'] = pd.DataFrame({
        'Country': ['Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Peru'],
        'E/R': [1428.95, 5.34, 3775.22, 1.0, 3.37]
    })
    tables['SLC'] = pd.DataFrame([
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival', 'UPLF': 1.0},
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response', 'UPLF': 1.5},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24', 'UPLF': 1.278}
    ])
    tables['LABOR'] = pd.DataFrame([
        {'Item': 'System Z', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Brazil': 2803.85},
        {'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Brazil': 186.82}
    ])
    return tables

# ==========================================
# 2. CARGA DE ARCHIVOS
# ==========================================
@st.cache_data
def load_data(ui_file, db_file):
    # 1. Cargar UI
    if ui_file:
        try:
            df_ui = pd.read_csv(ui_file)
            df_ui.columns = df_ui.columns.str.strip() # Limpiar espacios en headers
        except: df_ui = get_default_ui()
    else:
        df_ui = get_default_ui()

    # 2. Cargar DB
    if db_file:
        try:
            tables = {}
            content = db_file.getvalue().decode("utf-8")
            # Parser simple de ### TABLE:
            current_t = None
            buf = []
            for line in content.splitlines():
                if "### TABLE:" in line:
                    if current_t and buf:
                        h = buf[0].split(','); d = [r.split(',') for r in buf[1:] if r.strip()]
                        # Fix dimensiones
                        d = [r[:len(h)] for r in d if len(r)>=len(h)]
                        tables[current_t] = pd.DataFrame(d, columns=[x.strip() for x in h])
                    current_t = line.split("### TABLE:")[1].split('(')[0].strip()
                    buf = []
                elif line.strip() and current_t:
                    buf.append(line)
            # Ultima tabla
            if current_t and buf:
                h = buf[0].split(','); d = [r.split(',') for r in buf[1:] if r.strip()]
                d = [r[:len(h)] for r in d if len(r)>=len(h)]
                tables[current_t] = pd.DataFrame(d, columns=[x.strip() for x in h])
            
            # Conversiones numericas criticas
            if 'COUNTRIES' in tables: tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
            if 'SLC' in tables: tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')
            if 'LABOR' in tables:
                for c in tables['LABOR'].columns:
                    if c not in ['Scope','Item','Plat','Def']: tables['LABOR'][c] = pd.to_numeric(tables['LABOR'][c], errors='coerce')
        except: tables = get_default_db()
    else:
        tables = get_default_db()
        
    return df_ui, tables

with st.sidebar:
    st.header("📂 Archivos V9")
    up_ui = st.file_uploader("UI_CONFIG.csv", type=['csv'])
    up_db = st.file_uploader("Databases.csv", type=['csv'])
    st.divider()

ui_df, db_tables = load_data(up_ui, up_db)

# ==========================================
# 3. LÓGICA DE NEGOCIO (Lookups)
# ==========================================
def get_options(source, country):
    if pd.isna(source): return []
    s = str(source).strip()
    
    if "### TABLE:" not in s:
        return [x.strip() for x in s.split(',')] if ',' in s else []
    
    # Parse ### TABLE: NOMBRE(Columna)
    parts = s.replace("### TABLE:", "").split('(')
    tname = parts[0].strip()
    cname = parts[1].replace(')', '').strip() if len(parts)>1 else None
    
    if tname not in db_tables: return []
    df = db_tables[tname]
    
    # Filtro Scope
    if 'Scope' in df.columns and country:
        tgt = "Brazil" if country == "Brazil" else "no brazil"
        # Filtro laxo
        df = df[df['Scope'].str.lower().str.contains(tgt.lower(), na=False) | (df['Scope']=='All')]
        
    if cname and cname in df.columns: return df[cname].unique().tolist()
    
    # Fallback Labor
    if tname == "LABOR":
        if 'Item' in df.columns: return df['Item'].unique().tolist()
        if 'Plat' in df.columns: return (df['Plat']+"-"+df['Def']).unique().tolist()
        
    return []

def calculate_duration():
    """Calcula meses entre fechas guardadas en session_state"""
    try:
        s = st.session_state.get('Contract Start Date')
        e = st.session_state.get('Contract End Date')
        if s and e:
            d = relativedelta(e, s)
            return d.years*12 + d.months + (1 if d.days > 0 else 0)
    except: pass
    return 12

# ==========================================
# 4. RENDER UI (Detectar Slide + Formulación)
# ==========================================
st.title("💸 Cotizador V9 - Engine")

if 'inputs' not in st.session_state: st.session_state.inputs = {}

# Variables Globales (Estado)
if 'global_country' not in st.session_state: st.session_state.global_country = "Colombia"
if 'global_er' not in st.session_state: st.session_state.global_er = 3775.0
if 'global_dur' not in st.session_state: st.session_state.global_dur = 12

# Detectar columna source
src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

# Agrupar secciones
for section, group in ui_df.groupby('Section', sort=False):
    
    # --- CORRECCIÓN 1: DETECCIÓN ROBUSTA DE SLIDE ---
    # Convertimos a string y lower para evitar errores
    sec_str = str(section).strip()
    is_slide = "-slide" in sec_str.lower()
    
    if is_slide:
        cont = st.sidebar
        # Limpiar titulo visualmente
        title = sec_str.lower().replace("-slide", "").title()
    else:
        cont = st.container()
        title = sec_str
        
    with cont:
        st.header(title)
        
        for idx, row in group.iterrows():
            lbl = row['Field Label']
            dtype = str(row['Data Type']).strip()
            src = row[src_col]
            k = f"{lbl}_{idx}" # Key único
            
            # --- MANEJO DE CAMPOS ---
            
            # 1. DROPDOWN
            if dtype == 'Dropdown':
                # Si es Country, actualiza globales
                if lbl == 'Country':
                    opts = get_options(src, None)
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.global_country = val
                    st.session_state.inputs[lbl] = val
                    
                    # Buscar Tasa
                    if 'COUNTRIES' in db_tables:
                        cdf = db_tables['COUNTRIES']
                        row = cdf[cdf['Country'] == val]
                        if not row.empty:
                            raw_er = float(row['E/R'].values[0])
                            st.session_state.global_er = 1.0 if val == "Ecuador" else raw_er
                            st.caption(f"Tasa Cambio: {st.session_state.global_er}")
                else:
                    # Otros dropdowns filtrados por país
                    opts = get_options(src, st.session_state.global_country)
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.inputs[lbl] = val

            # 2. FECHAS (Trigger Recalculo Duración)
            elif dtype == 'Date':
                # Usamos el label exacto como key para encontrarlo en calculate_duration
                val = st.date_input(lbl, date.today(), key=lbl) 
                st.session_state.inputs[lbl] = val
                
            # 3. NÚMEROS (Con lógica especial para 'Period')
            elif dtype == 'Number':
                # --- CORRECCIÓN 2: FORMULACIÓN DE DURACIÓN ---
                if "Period" in lbl or "Duration" in lbl:
                    # Calcular automáticamente
                    calc_dur = calculate_duration()
                    st.session_state.global_dur = calc_dur
                    # Mostramos disabled porque es calculado
                    st.number_input(lbl, value=calc_dur, disabled=True, key=k)
                    st.session_state.inputs[lbl] = calc_dur
                else:
                    # Inputs normales (Costos, Cantidades)
                    val = st.number_input(lbl, min_value=0.0, step=1.0, key=k)
                    st.session_state.inputs[lbl] = val
            
            # 4. RADIO
            elif dtype == 'Radio':
                opts = [x.strip() for x in str(src).split(',') if "###" not in x]
                val = st.radio(lbl, opts, horizontal=True, key=k)
                st.session_state.inputs[lbl] = val

        if not is_slide: st.divider()

# ==========================================
# 5. CÁLCULO FINAL (FORMULACIÓN V9)
# ==========================================
st.header("Resultados de Cotización")

if st.button("Calcular Totales"):
    res_cont = st.container()
    inputs = st.session_state.inputs
    country = st.session_state.global_country
    er = st.session_state.global_er
    dur = st.session_state.global_dur
    
    # Recuperar Inputs (Mapeo Flexible)
    # Buscamos keys que contengan palabras clave si no coinciden exacto
    def get_val(key_part, default=0.0):
        for k, v in inputs.items():
            if key_part.lower() in k.lower(): return v
        return default
    
    # SERVICIOS
    usd_cost = get_val("USD Unit", 0.0)
    sqty = get_val("SQty", 0.0)
    slc_sel = get_val("SLC", "")
    
    # LABOR
    lqty = get_val("LQty", 0.0)
    lab_sel = get_val("RR/BR", "")
    
    # --- LOGICA 1: FACTOR SLC ---
    uplf = 1.0
    if 'SLC' in db_tables:
        sdf = db_tables['SLC']
        # Buscar UPLF
        col_desc = next((c for c in ['Desc','SLC','ID_Desc'] if c in sdf.columns), None)
        if col_desc:
            tgt = "Brazil" if country=="Brazil" else "no brazil"
            row = sdf[sdf['Scope'].str.lower().str.contains(tgt.lower(), na=False) & (sdf[col_desc]==slc_sel)]
            if not row.empty: uplf = float(row['UPLF'].values[0])

    # --- LOGICA 2: TARIFA LABOR ---
    lab_rate_usd = 0.0
    if 'LABOR' in db_tables:
        ldf = db_tables['LABOR']
        # Buscar item
        lrow = ldf[ldf.apply(lambda x: str(lab_sel) in str(x.values), axis=1)]
        if not lrow.empty and country in ldf.columns:
            local_rate = float(lrow[country].values[0])
            # FORMULA: LOCAL / ER
            lab_rate_usd = local_rate / er
            
    # --- TOTALES ---
    tot_serv = usd_cost * sqty * uplf * dur
    tot_lab = lab_rate_usd * lqty
    grand_tot = tot_serv + tot_lab
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Servicios", f"${tot_serv:,.2f}", help=f"Cost(${usd_cost}) * Qty({sqty}) * SLC({uplf}) * Meses({dur})")
    c2.metric("Total Labor", f"${tot_lab:,.2f}", help=f"(Tarifa Local / ER {er}) * Qty({lqty})")
    c3.metric("GRAN TOTAL", f"${grand_tot:,.2f}")
