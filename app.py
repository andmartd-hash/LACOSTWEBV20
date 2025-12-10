import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title="LACOST V9 - Data Driven", layout="wide")

# Estilos CSS Compactos
st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h1 { font-size: 1.5rem !important; }
    h2 { font-size: 1.2rem !important; margin-top: 0.5rem !important; }
    .stSelectbox, .stNumberInput, .stDateInput { margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MOTOR DE CARGA DE DATOS (PARSERS)
# ==========================================

@st.cache_data
def load_ui_config():
    """Carga la configuración de la interfaz."""
    try:
        # Ajusta el nombre del archivo si es necesario
        return pd.read_csv("V9-BASE.xlsx - UI_CONGIF.csv")
    except FileNotFoundError:
        st.error("❌ No se encontró 'V9-BASE.xlsx - UI_CONGIF.csv'")
        return pd.DataFrame()

@st.cache_data
def load_databases():
    """
    Lee el archivo Databases.csv y lo divide en múltiples DataFrames
    basado en los marcadores '### TABLE:'
    """
    tables = {}
    current_table_name = None
    current_data = []
    
    try:
        with open("V9-BASE.xlsx - Databases.csv", "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            # Detectar inicio de tabla
            if "### TABLE:" in line:
                # Si ya estábamos leyendo una tabla, guardarla
                if current_table_name and current_data:
                    # Crear DF, la primera fila son headers
                    headers = current_data[0].split(',')
                    # Limpiar headers vacíos
                    headers = [h for h in headers if h] 
                    
                    # Procesar cuerpo
                    rows = []
                    for d in current_data[1:]:
                        row_vals = d.split(',')
                        # Ajustar longitud al header
                        rows.append(row_vals[:len(headers)])
                    
                    df = pd.DataFrame(rows, columns=headers)
                    tables[current_table_name] = df
                
                # Iniciar nueva tabla (Extraer nombre entre parentesis o despues de :)
                current_table_name = line.split("### TABLE:")[1].strip().split('(')[0].strip()
                current_data = [] # Reiniciar buffer
            else:
                if line and current_table_name:
                    current_data.append(line)
        
        # Guardar la última tabla del archivo
        if current_table_name and current_data:
            headers = current_data[0].split(',')
            headers = [h for h in headers if h]
            rows = [d.split(',')[:len(headers)] for d in current_data[1:]]
            tables[current_table_name] = pd.DataFrame(rows, columns=headers)
            
        # --- POST-PROCESAMIENTO DE TIPOS DE DATOS ---
        # Convertir números en COUNTRIES
        if 'COUNTRIES' in tables:
            tables['COUNTRIES']['E/R'] = pd.to_numeric(tables['COUNTRIES']['E/R'], errors='coerce')
        
        # Convertir números en SLC
        if 'SLC' in tables:
            tables['SLC']['UPLF'] = pd.to_numeric(tables['SLC']['UPLF'], errors='coerce')

        return tables

    except FileNotFoundError:
        st.error("❌ No se encontró 'V9-BASE.xlsx - Databases.csv'")
        return {}

# Cargar datos al iniciar
ui_df = load_ui_config()
db_tables = load_databases()

# ==========================================
# 2. FUNCIONES DE LÓGICA DE NEGOCIO
# ==========================================

def get_options_from_source(source_string, selected_country):
    """
    Interpreta strings como '### TABLE: SLC(SLC,UPLF)' y devuelve opciones.
    Aplica lógica de Scope (Brasil vs No Brasil).
    """
    if not isinstance(source_string, str) or "### TABLE:" not in source_string:
        return []

    # Extraer nombre de tabla y columna
    # Ej: ### TABLE: COUNTRIES(Country) -> Tabla: COUNTRIES, Col: Country
    parts = source_string.replace("### TABLE:", "").strip().split('(')
    table_name = parts[0].strip()
    col_name = parts[1].replace(')', '').strip() if len(parts) > 1 else None

    if table_name not in db_tables:
        return []

    df = db_tables[table_name]

    # --- LÓGICA DE FILTRADO (SCOPE) ---
    if 'Scope' in df.columns:
        scope_target = "Brazil" if selected_country == "Brazil" else "no brazil"
        # Filtramos (case insensitive)
        df = df[df['Scope'].str.lower() == scope_target.lower()]

    # Si la columna pedida existe, retornamos lista única
    if col_name and col_name in df.columns:
        return df[col_name].unique().tolist()
    
    # Caso especial: Labor combinada (plat, def)
    if table_name == "LABOR":
        # Retornar una combinación legible para el dropdown
        if 'Item' in df.columns: return df['Item'].unique().tolist() # Ajuste según tu CSV real
        # Si el CSV tiene 'Plat' y 'Def', creamos una columna combinada
        if 'Plat' in df.columns and 'Def' in df.columns:
            return (df['Plat'] + " - " + df['Def']).unique().tolist()
    
    return []

def get_labor_price(item_selection, country, exchange_rate):
    """Busca el precio en la matriz LABOR (Filas=Items, Columnas=Países)"""
    if 'LABOR' not in db_tables: return 0.0
    
    df = db_tables['LABOR']
    
    # 1. Encontrar la fila (Item)
    # Nota: Tu CSV de labor es complejo, asumiremos que 'Plat' - 'Def' o 'Item' es la clave
    # Ajuste para buscar coincidencias parciales o exactas según tu parser
    # Intentamos construir la clave de búsqueda
    
    # Opción A: Si el parser generó columnas simples
    # Buscamos la fila donde alguna columna descriptiva coincida con la selección
    row = df[df.apply(lambda x: item_selection in str(x.values), axis=1)]
    
    if row.empty: return 0.0
    
    # 2. Encontrar la columna (País)
    # El nombre del país debe coincidir con la columna en el CSV de LABOR
    if country not in row.columns:
        return 0.0
    
    try:
        price_local = float(row[country].values[0])
        # Regla: Costo / ER (Si Ecuador, ER es 1, ya manejado afuera)
        return price_local / exchange_rate
    except:
        return 0.0

def get_slc_factor(slc_desc, selected_country):
    """Obtiene el UPLF basado en la descripción del SLC y el país"""
    if 'SLC' not in db_tables: return 1.0
    df = db_tables['SLC']
    
    scope_target = "Brazil" if selected_country == "Brazil" else "no brazil"
    row = df[ (df['Scope'].str.lower() == scope_target.lower()) & (df['Desc'] == slc_desc) ] # Ajustar 'Desc' o columna real
    
    # Fallback si el parser nombró diferente la columna (ej. SLC, ID_Desc)
    if row.empty and 'SLC' in df.columns:
         row = df[ (df['Scope'].str.lower() == scope_target.lower()) & (df['SLC'] == slc_desc) ]

    if not row.empty:
        try:
            return float(row['UPLF'].values[0])
        except:
            return 1.0
    return 1.0

# ==========================================
# 3. INTERFAZ DE USUARIO (RENDER LOOP)
# ==========================================

st.title("💸 LACOST V9: Cotizador Data-Driven")

# Estado de la sesión para guardar inputs
if 'inputs' not in st.session_state: st.session_state.inputs = {}

# Variables globales derivadas (se llenan al procesar la Sec 1)
global_country = "Colombia"
global_er = 3775.0
global_duration = 12

# Agrupar configuración por Secciones
grouped_ui = ui_df.groupby('Section', sort=False)

for section_name, section_df in grouped_ui:
    
    # --- 3.1 DETECCIÓN DE LAYOUT (-slide) ---
    if "-slide" in section_name.lower():
        container = st.sidebar
        clean_title = section_name.lower().replace("-slide", "").title()
    else:
        container = st.container()
        clean_title = section_name
        
    with container:
        st.header(clean_title)
        
        for idx, row in section_df.iterrows():
            label = row['Field Label']
            dtype = row['Data Type']
            source = row['Source / Options']
            mandatory = row['Mandatory']
            
            # Key único
            k = f"{section_name}_{label}"
            
            # --- RENDERIZADO DE WIDGETS ---
            
            # 1. DROPDOWN
            if dtype == 'Dropdown':
                # Si es País, actualizamos global
                if label == 'Country':
                    opts = get_options_from_source(source, None)
                    val = st.selectbox(label, opts, key=k)
                    global_country = val
                    st.session_state.inputs['Country'] = val
                    
                    # Calcular E/R inmediatamente para mostrar
                    if 'COUNTRIES' in db_tables:
                        c_df = db_tables['COUNTRIES']
                        # Buscar fila del país
                        c_row = c_df[c_df['Country'] == global_country]
                        if not c_row.empty:
                            raw_er = float(c_row['E/R'].values[0])
                            # Regla Excepción Ecuador
                            global_er = 1.0 if global_country == "Ecuador" else raw_er
                            currency = c_row['Currency'].values[0]
                            st.caption(f"Moneda: {currency} | Tasa: {global_er}")
                
                else:
                    # Otros dropdowns (Offering, SLC, Labor) dependen del país
                    opts = get_options_from_source(source, global_country)
                    val = st.selectbox(label, opts, key=k)
                    st.session_state.inputs[label] = val

            # 2. FECHAS
            elif dtype == 'Date':
                val = st.date_input(label, date.today(), key=k)
                st.session_state.inputs[label] = val
            
            # 3. NÚMEROS
            elif dtype == 'Number':
                # Si es un campo calculado (Contract Period), lo mostramos como métrica o disabled
                if "Contract Period" in label or "Duration" in label:
                    # Calculamos duración si tenemos las fechas
                    try:
                        d_start = st.session_state.inputs.get('Contract Start Date', date.today())
                        d_end = st.session_state.inputs.get('Contract End Date', date.today())
                        diff = relativedelta(d_end, d_start)
                        calc_months = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
                        st.number_input(label, value=calc_months, disabled=True, key=k)
                        global_duration = calc_months
                    except:
                        st.number_input(label, value=0, key=k)
                else:
                    val = st.number_input(label, min_value=0.0, step=1.0, key=k)
                    st.session_state.inputs[label] = val
            
            # 4. RADIO / TEXTO
            elif dtype == 'Radio':
                opts = source.split(',') if isinstance(source, str) else []
