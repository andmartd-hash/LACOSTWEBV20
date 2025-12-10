import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="LACOST V9 - Auto", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stSelectbox, .stNumberInput { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. CARGA AUTOMÁTICA DE ARCHIVOS (Hardcoded)
# ==========================================
# IMPORTANTE: Los archivos deben llamarse 'ui.csv' y 'db.csv' en tu carpeta
UI_FILE = "ui.csv"
DB_FILE = "db.csv"

@st.cache_data
def load_ui_local():
    try:
        df = pd.read_csv(UI_FILE)
        # Limpiar nombres de columnas por si tienen espacios extra
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error(f"❌ ERROR CRÍTICO: No encuentro el archivo '{UI_FILE}'.")
        st.warning("Por favor, renombra tu archivo 'V9...UI_CONGIF.csv' a 'ui.csv' y súbelo a GitHub junto a app.py")
        return pd.DataFrame()

@st.cache_data
def load_db_local():
    tables = {}
    current_table = None
    buffer = []
    
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if "### TABLE:" in line:
                # Guardar tabla previa
                if current_table and buffer:
                    # Crear DataFrame
                    header = buffer[0].split(',')
                    # Filtrar headers vacíos
                    header = [h.strip() for h in header if h.strip()]
                    
                    data = []
                    for row_str in buffer[1:]:
                        row_vals = row_str.split(',')
                        # Asegurar dimensiones
                        if len(row_vals) >= len(header):
                            data.append(row_vals[:len(header)])
                            
                    tables[current_table] = pd.DataFrame(data, columns=header)
                
                # Nueva tabla
                raw_name = line.split("### TABLE:")[1]
                current_table = raw_name.split('(')[0].strip()
                buffer = []
            else:
                if line and current_table:
                    buffer.append(line)
        
        # Procesar la última tabla del archivo
        if current_table and buffer:
            header = buffer[0].split(',')
            header = [h.strip() for h in header if h.strip()]
            data = [r.split(',')[:len(header)] for r in buffer[1:]]
            tables[current_table] = pd.DataFrame(data, columns=header)
            
        # Conversiones numéricas básicas
        if 'COUNTRIES' in tables:
            tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
        if 'SLC' in tables:
            tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')
            
        return tables

    except FileNotFoundError:
        st.error(f"❌ ERROR CRÍTICO: No encuentro el archivo '{DB_FILE}'.")
        st.warning("Por favor, renombra tu archivo 'V9...Databases.csv' a 'db.csv' y súbelo a GitHub.")
        return {}

# Cargar datos al iniciar
ui_df = load_ui_local()
db_tables = load_db_local()

if ui_df.empty or not db_tables:
    st.stop() # Detener si no hay datos

# ==========================================
# 2. FUNCIONES DE LÓGICA (Parsers V9)
# ==========================================

def get_options(source_str, country_context):
    """Parsea la columna 'Source / Options' del V9"""
    if pd.isna(source_str): return []
    source_str = str(source_str).strip()
    
    # Caso 1: Lista manual separada por comas (USD, Local)
    if "### TABLE:" not in source_str:
        if "," in source_str:
            return [x.strip() for x in source_str.split(',')]
        return []

    # Caso 2: Referencia a Tabla (### TABLE: NOMBRE(Columna))
    parts = source_str.replace("### TABLE:", "").split('(')
    tbl_name = parts[0].strip()
    col_name = parts[1].replace(')', '').strip() if len(parts) > 1 else None
    
    if tbl_name not in db_tables:
        return []
    
    df = db_tables[tbl_name]
    
    # Filtro Scope (Brazil vs No Brazil)
    if 'Scope' in df.columns and country_context:
        target = "Brazil" if country_context == "Brazil" else "no brazil"
        df = df[df['Scope'].str.lower() == target.lower()]
        
    if col_name and col_name in df.columns:
        return df[col_name].unique().tolist()
    
    # Fallback para tablas complejas como LABOR
    if tbl_name == "LABOR":
        # Intentar concatenar Plat + Def para mostrar algo útil
        if 'Plat' in df.columns and 'Def' in df.columns:
            return (df['Plat'] + " - " + df['Def']).unique().tolist()
            
    return []

def get_slc_factor(slc_code, country):
    if 'SLC' not in db_tables: return 1.0
    df = db_tables['SLC']
    target = "Brazil" if country == "Brazil" else "no brazil"
    
    # V9 usa columnas como Scope, ID_Desc, SLC, UPLF
    # Buscamos coincidencia en SLC (código) o ID_Desc
    cols_to_check = ['SLC', 'ID_Desc', 'Desc']
    actual_col = next((c for c in cols_to_check if c in df.columns), None)
    
    if not actual_col: return 1.0
    
    row = df[ (df['Scope'].str.lower() == target.lower()) & (df[actual_col] == slc_code) ]
    if not row.empty:
        return float(row['UPLF'].values[0])
    return 1.0

def get_labor_rate(item_str, country, er):
    if 'LABOR' not in db_tables: return 0.0
    df = db_tables['LABOR']
    
    # Buscar la fila. Como el item puede ser "Plat - Def", buscamos coincidencia parcial
    # OJO: La búsqueda depende de cómo venga el string del dropdown
    try:
        # Simplificación: Buscamos si alguna columna de texto contiene parte del string seleccionado
        mask = df.apply(lambda x: str(item_str).split('-')[0].strip() in str(x.values), axis=1)
        row = df[mask]
        
        if row.empty: return 0.0
        if country not in row.columns: return 0.0
        
        local_val = float(row[country].values[0])
        return local_val / er
    except:
        return 0.0

# ==========================================
# 3. INTERFAZ DINÁMICA
# ==========================================

st.title("💸 Cotizador V9 (File Based)")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
global_vars = {'Country': 'Colombia', 'E/R': 3775.0, 'Duration': 12}

# Validar columna Source/Options
src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

# Agrupar por Sección
for section, group in ui_df.groupby('Section', sort=False):
    
    # Lógica Slide
    if "-slide" in str(section).lower():
        container = st.sidebar
        title = str(section).lower().replace("-slide", "").title()
    else:
        container = st.container()
        title = str(section)
        
    with container:
        st.header(title)
        
        for idx, row in group.iterrows():
            label = row['Field Label']
            dtype = str(row['Data Type']).strip()
            source = row[src_col]
            k = f"{section}_{label}_{idx}"
            
            # --- RENDERIZADO ---
            if dtype == 'Dropdown':
                # País es especial porque controla E/R y Scope
                if label == 'Country':
                    opts = get_options(source, None)
                    val = st.selectbox(label, opts, key=k)
                    global_vars['Country'] = val
                    
                    # Calcular ER al vuelo
                    if 'COUNTRIES' in db_tables:
                        cdf = db_tables['COUNTRIES']
                        crow = cdf[cdf['Country'] == val]
                        if not crow.empty:
                            raw_er = float(crow['E/R'].values[0])
                            # Lógica Ecuador
                            global_vars['E/R'] = 1.0 if val == "Ecuador" else raw_er
                            st.caption(f"Tasa aplicada: {global_vars['E/R']}")
                else:
                    # Otros dropdowns dependen del país seleccionado
                    opts = get_options(source, global_vars['Country'])
                    val = st.selectbox(label, opts, key=k)
                    st.session_state.inputs[label] = val
            
            elif dtype == 'Date':
                val = st.date_input(label, date.today(), key=k)
                st.session_state.inputs[label] = val
                
            elif dtype == 'Number':
                if "Contract Period" in label or "Duration" in label:
                    # Intento de cálculo automático de meses
                    try:
                        d1 = st.session_state.inputs.get('Contract Start Date', date.today())
                        d2 = st.session_state.inputs.get('Contract End Date', date.today())
                        diff = relativedelta(d2, d1)
                        m = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
                        st.number_input(label, value=m, disabled=True, key=k)
                        global_vars['Duration'] = m
                    except:
                        st.number_input(label, value=0, key=k)
                else:
                    val = st.number_input(label, min_value=0.0, step=1.0, key=k)
                    st.session_state.inputs[label] = val
                    
            elif dtype == 'Radio':
                opts = str(source).split(',')
                # Limpiar '### TABLE' si se coló por error en un radio
                opts = [o for o in opts if "###" not in o]
                val = st.radio(label, opts, horizontal=True, key=k)

        if container != st.sidebar: st.divider()

# ==========================================
# 4. CÁLCULOS
# ==========================================
st.header("4. Totales Calculados")

if st.button("Calcular Proyecto"):
    # Recuperamos valores de la sesión
    inputs = st.session_state.inputs
    
    # Mapeo de campos basado en tus nombres del V9
    # (Ajusta estos strings si cambias Labels en el CSV)
    usd_cost = inputs.get('USD Unit Cost', 0.0)
    sqty = inputs.get('SQty', 0)
    slc_sel = inputs.get('SLC', '')
    
    lqty = inputs.get('LQty', 0)
    labor_sel = inputs.get('RR/BR', '')
    
    # 1. Servicios
    uplf = get_slc_factor(slc_sel, global_vars['Country'])
    serv_total = usd_cost * sqty * uplf * global_vars['Duration']
    
    # 2. Labor
    lab_rate = get_labor_rate(labor_sel, global_vars['Country'], global_vars['E/R'])
    lab_total = lab_rate * lqty
    
    grand_total = serv_total + lab_total
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Servicios", f"${serv_total:,.2f}")
    c2.metric("Total Labor", f"${lab_total:,.2f}")
    c3.metric("GRAN TOTAL", f"${grand_total:,.2f}")
    
    with st.expander("Debug de variables"):
        st.write(f"País: {global_vars['Country']} | E/R: {global_vars['E/R']}")
        st.write(f"SLC Factor: {uplf}")
        st.write(f"Labor Rate USD: {lab_rate:,.2f}")
