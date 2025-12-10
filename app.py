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
# 1. CARGA DE ARCHIVOS (Nombres Exactos)
# ==========================================
# AQUÍ ESTÁ EL ARREGLO: Usamos los nombres exactos de tus archivos
UI_FILE = "V9-BASE.xlsx - UI_CONGIF.csv"   # Nota: Mantenemos tu typo 'CONGIF' para que lo encuentre
DB_FILE = "V9-BASE.xlsx - Databases.csv"

@st.cache_data
def load_ui_local():
    try:
        # Intentamos leer con el nombre largo
        df = pd.read_csv(UI_FILE)
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        # Si falla, intentamos nombres alternativos comunes por si acaso
        try:
            df = pd.read_csv("UI_CONGIF.csv")
            return df
        except:
            st.error(f"❌ ERROR: No encuentro el archivo '{UI_FILE}' en la carpeta.")
            st.warning("Asegúrate de haber subido el archivo CSV a GitHub exactamente con ese nombre.")
            return pd.DataFrame()

@st.cache_data
def load_db_local():
    tables = {}
    current_table = None
    buffer = []
    
    # Intentar abrir el archivo con el nombre largo
    try:
        file_handle = open(DB_FILE, "r", encoding="utf-8")
    except FileNotFoundError:
        try:
            file_handle = open("Databases.csv", "r", encoding="utf-8")
        except:
            st.error(f"❌ ERROR: No encuentro el archivo '{DB_FILE}' en la carpeta.")
            return {}

    try:
        lines = file_handle.readlines()
        file_handle.close()
        
        for line in lines:
            line = line.strip()
            if "### TABLE:" in line:
                # Guardar tabla previa
                if current_table and buffer:
                    # Crear DataFrame
                    header = buffer[0].split(',')
                    header = [h.strip() for h in header if h.strip()]
                    
                    data = []
                    for row_str in buffer[1:]:
                        row_vals = row_str.split(',')
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
        
        # Procesar la última tabla
        if current_table and buffer:
            header = buffer[0].split(',')
            header = [h.strip() for h in header if h.strip()]
            data = [r.split(',')[:len(header)] for r in buffer[1:]]
            tables[current_table] = pd.DataFrame(data, columns=header)
            
        # Conversiones numéricas
        if 'COUNTRIES' in tables and 'E/R' in tables['COUNTRIES'].columns:
            tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
        if 'SLC' in tables and 'UPLF' in tables['SLC'].columns:
            tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')
            
        return tables

    except Exception as e:
        st.error(f"Error procesando Databases: {e}")
        return {}

# Cargar datos
ui_df = load_ui_local()
db_tables = load_db_local()

if ui_df.empty or not db_tables:
    st.stop()

# ==========================================
# 2. FUNCIONES LÓGICAS (Parsers)
# ==========================================

def get_options(source_str, country_context):
    if pd.isna(source_str): return []
    source_str = str(source_str).strip()
    
    # Caso Lista Manual
    if "### TABLE:" not in source_str:
        if "," in source_str:
            return [x.strip() for x in source_str.split(',')]
        return []

    # Caso Tabla
    parts = source_str.replace("### TABLE:", "").split('(')
    tbl_name = parts[0].strip()
    col_name = parts[1].replace(')', '').strip() if len(parts) > 1 else None
    
    if tbl_name not in db_tables: return []
    df = db_tables[tbl_name]
    
    # Filtro Scope
    if 'Scope' in df.columns and country_context:
        target = "Brazil" if country_context == "Brazil" else "no brazil"
        df = df[df['Scope'].str.lower() == target.lower()]
        
    if col_name and col_name in df.columns:
        return df[col_name].unique().tolist()
    
    # Fallback Labor
    if tbl_name == "LABOR":
        if 'Plat' in df.columns and 'Def' in df.columns:
            return (df['Plat'] + " - " + df['Def']).unique().tolist()
    return []

def get_slc_factor(slc_code, country):
    if 'SLC' not in db_tables: return 1.0
    df = db_tables['SLC']
    target = "Brazil" if country == "Brazil" else "no brazil"
    
    # Busca columnas posibles
    cols = ['SLC', 'ID_Desc', 'Desc']
    actual = next((c for c in cols if c in df.columns), None)
    
    if actual:
        row = df[ (df['Scope'].str.lower() == target.lower()) & (df[actual] == slc_code) ]
        if not row.empty: return float(row['UPLF'].values[0])
    return 1.0

def get_labor_rate(item_str, country, er):
    if 'LABOR' not in db_tables: return 0.0
    df = db_tables['LABOR']
    try:
        # Búsqueda laxa
        mask = df.apply(lambda x: str(item_str).split('-')[0].strip() in str(x.values), axis=1)
        row = df[mask]
        if not row.empty and country in row.columns:
            return float(row[country].values[0]) / er
    except: pass
    return 0.0

# ==========================================
# 3. INTERFAZ DINÁMICA
# ==========================================
st.title("💸 Cotizador V9")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
global_vars = {'Country': 'Colombia', 'E/R': 3775.0, 'Duration': 12}

# Validar nombre columna Source
src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

for section, group in ui_df.groupby('Section', sort=False):
    
    # Slide Logic
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

            elif dtype == 'text' or dtype == 'Text':
                st.text_input(lbl, key=k)

        if cont != st.sidebar: st.divider()

# ==========================================
# 4. CÁLCULO
# ==========================================
st.header("4. Totales")
if st.button("Calcular"):
    try:
        inputs = st.session_state.inputs
        
        # Mapeo de campos V9
        usd_cost = inputs.get('USD Unit Cost', 0.0)
        sqty = inputs.get('SQty', 0.0)
        slc_sel = inputs.get('SLC', '')
        lqty = inputs.get('LQty', 0.0)
        labor_sel = inputs.get('RR/BR', '')
        if not labor_sel: labor_sel = inputs.get('Labor RR/BR', '') # Fallback nombre
        
        uplf = get_slc_factor(slc_sel, global_vars['Country'])
        serv_total = usd_cost * sqty * uplf * global_vars['Duration']
        
        lab_rate = get_labor_rate(labor_sel, global_vars['Country'], global_vars['E/R'])
        lab_total = lab_rate * lqty
        
        grand = serv_total + lab_total
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Servicios", f"${serv_total:,.2f}")
        c2.metric("Labor", f"${lab_total:,.2f}")
        c3.metric("GRAN TOTAL", f"${grand:,.2f}")
        
    except Exception as e:
        st.error(f"Error: {e}")
