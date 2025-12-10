import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA (V11)
# ==========================================
st.set_page_config(page_title="LACOST V11", layout="wide")

# CSS: TAMAÑO DE LETRA 8PT Y VISTA COMPACTA
st.markdown("""
<style>
    /* Forzar tamaño de letra 11px (~8pt) */
    html, body, [class*="css"], .stTextInput, .stNumberInput, .stSelectbox, .stDateInput {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11px !important;
    }
    
    /* Ajustes de Títulos */
    h1 { font-size: 16px !important; padding: 5px 0 !important; }
    h2 { font-size: 14px !important; padding: 2px 0 !important; border-bottom: 1px solid #ddd; }
    h3 { font-size: 12px !important; font-weight: bold !important; margin-top: 5px !important;}
    
    /* Compactar Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        min-height: 24px !important;
        height: 24px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* Compactar Labels */
    label {
        font-size: 10px !important;
        margin-bottom: 0px !important;
        margin-top: 0px !important;
    }
    
    /* Reducir espacios generales */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    div[data-testid="column"] { padding: 0px 4px !important; }
    div.stButton > button { font-size: 11px !important; padding: 2px 10px !important; height: 28px; }
    
    /* Tabs compactos */
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { padding: 2px 10px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MOTOR DE DATOS UNIFICADO (V11)
# ==========================================

@st.cache_data
def load_v11_data():
    data = {}
    
    # 1. UI_CONFIG (V11 Updated)
    ui_csv = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. Configuracion-slidebar,-,Country,Dropdown,Yes,Sheet Countries
1. Configuracion-slidebar,-,Currency,Radio,Yes,Sheet Countries
1. Configuracion-slidebar,-,Contract Start Date,Date,Yes,User imput
1. Configuracion-slidebar,-,Contract End Date,Date,Yes,User imput
1. Configuracion-slidebar,-,Contract Period,Number,Yes,Calculated
1. Configuracion-slidebar,-,QA Risk,Dropdown,Yes,Sheet Risk
1. Configuracion-slidebar,-,Client Name,string(20),Yes,User imput
1. Configuracion-slidebar,-,Client Number,Number(int),Yes,User imput
2. Servicios-Tab1-main,,Offering,Dropdown,Yes,Sheet Offering
2. Servicios-Tab1-main,,L40,text,Yes,Calculated
2. Servicios-Tab1-main,,Go To Conga,text,Yes,Calculated
2. Servicios-Tab1-main,,DI1,Date,Yes,User imput
2. Servicios-Tab1-main,,DE1,Date,Yes,User imput
2. Servicios-Tab1-main,,Duration1,Number,Yes,Calculated
2. Servicios-Tab1-main,,SLC,Dropdown,Yes,Sheet SLC
2. Servicios-Tab1-main,,USD Unit Cost,Number,Yes,User imput
2. Servicios-Tab1-main,,SQty,Number,Yes,User imput
3. Labor-Tab2-main,,RR/BR,Dropdown,Yes,Sheet Labor
3. Labor-Tab2-main,,RR/BR Cost,Number,Yes,Calculated
3. Labor-Tab2-main,,Monthly Hours,Number,Yes,User imput
3. Labor-Tab2-main,,DI2,Date,Yes,User imput
3. Labor-Tab2-main,,DE2,Date,Yes,User imput
3. Labor-Tab2-main,,Duration2,Number,Yes,Calculated
4. Total Cost-main,,Total Service Cost,Number,Yes,Logic_rules
4. Total Cost-main,,Total Labor Cost,Number,Yes,Logic_rules
4. Total Cost-main,,Total Cost,Number,Yes,Logic_rules"""
    data['UI'] = pd.read_csv(io.StringIO(ui_csv))

    # 2. COUNTRIES (Transformado de Matriz a Tabla Limpia)
    # He unificado la data de tu archivo Countries.csv para que sea legible
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'E/R': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
        'Scope': ['All', 'Brazil', 'All', 'All', 'All', 'All', 'All', 'All', 'All']
    }
    data['Countries'] = pd.DataFrame(countries_data)

    # 3. OFFERING (V11)
    offering_csv = """Offering,L40,Load in conga
IBM Hardware Resell for Server and Storage-Lenovo,6942-1BT,Location Based Services
1-HWMA MVS SPT other Prod,6942-0IC,Conga by CSV
2-HWMA MVS SPT other Prod,6942-0IC,Conga by CSV
SWMA MVS SPT other Prod,6942-76O,Conga by CSV
IBM Support for Red Hat,6948-B73,Conga by CSV
IBM Support for Red Hat - Enterprise Linux Subscription,6942-42T,Location Based Services
Subscription for Red Hat,6948-66J,Location Based Services
Support for Red Hat,6949-66K,Location Based Services
IBM Support for Oracle,6942-42E,Location Based Services
IBM Customized Support for Multivendor Hardware Services,6942-76T,Location Based Services
IBM Customized Support for Multivendor Software Services,6942-76U,Location Based Services
IBM Customized Support for Hardware Services-Logo,6942-76V,Location Based Services
IBM Customized Support for Software Services-Logo,6942-76W,Location Based Services
HWMA MVS SPT other Loc,6942-0ID,Location Based Services
SWMA MVS SPT other Loc,6942-0IG,Location Based Services
Relocation Services - Packaging,6942-54E,Location Based Services
Relocation Services - Movers Charge,6942-54F,Location Based Services
Relocation Services - Travel and Living,6942-54R,Location Based Services
Relocation Services - External Vendor's Charge,6942-78O,Location Based Services
IBM Hardware Resell for Networking and Security Alliances,6942-1GE,Location Based Services
IBM Software Resell for Networking and Security Alliances,6942-1GF,Location Based Services
System Technical Support Service-MVS-STSS,6942-1FN,Location Based Services
System Technical Support Service-Logo-STSS,6942-1KJ,Location Based Services"""
    data['Offering'] = pd.read_csv(io.StringIO(offering_csv))

    # 4. SLC (V11)
    slc_csv = """Scope,SLC,UPLF,Desc
All,M1A,1.0,9X5NBD On-site
All,M16,1.0,9X5SBD On-site
All,M19,1.0,24X7SD On-site
All,M5B,1.05,24X7 1hr Contact
All,M47,1.5,24X7 4hr On-site
All,MJ7,1.1,24X7 72hr Fix
All,M3F,1.15,24X7 48hr Fix
All,M3B,1.2,24X7 24hr Fix
All,M33,1.3,24X7 12hr Fix
All,M2F,1.4,24X7 8hr Fix
All,M2B,1.6,24X7 6hr Fix
All,M23,1.7,24X7 4hr Fix
Brazil,M19,1.0,24X7SD On-site
Brazil,NStd5x9,1.0,NStd 5x9
Brazil,NStdSBD7x24,1.278,NStd SBD 7x24"""
    data['SLC'] = pd.read_csv(io.StringIO(slc_csv))

    # 5. LABOR (V11)
    labor_csv = """Item,Argentina,Brazil,Chile,Colombia,Ecuador,Peru,Mexico,Uruguay,Venezuela
System Z,304504.2,2803.85,2165270.4,2054058.99,991.20,1284.60,12857.25,30167.39,102721.98
Power HE,194856.48,1516.61,486361.26,540008.96,340.52,505.85,5857.95,18987.51,40555.17
Power LE,162675.24,742.22,486361.26,379581.99,283.76,312.87,3860.85,10986.01,36819.82
System X HE,66943.8,0,101090.22,108029.93,153.10,211.05,1054.2,8828.82,112860.77
B7 (Senior),40166.28,186.82,54081.72,126000.0,79.19,216.45,673.05,3581.26,20998.96"""
    data['Labor'] = pd.read_csv(io.StringIO(labor_csv))

    # 6. RISK (V11)
    risk_csv = """Level,Percentage
Low,0.02
Medium,0.05
High,0.08"""
    data['Risk'] = pd.read_csv(io.StringIO(risk_csv))

    return data

DB = load_v11_data()

# ==========================================
# 2. FUNCIONES LÓGICAS
# ==========================================

def get_country_info(country):
    row = DB['Countries'][DB['Countries']['Country'] == country]
    if not row.empty:
        er = 1.0 if country == "Ecuador" else float(row['E/R'].values[0])
        scope = "Brazil" if country == "Brazil" else "All"
        return er, scope
    return 1.0, "All"

def get_options(source, country_scope):
    if source == "Sheet Countries":
        return DB['Countries']['Country'].unique().tolist()
    elif source == "Sheet Risk":
        return DB['Risk']['Level'].unique().tolist()
    elif source == "Sheet Offering":
        return DB['Offering']['Offering'].unique().tolist()
    elif source == "Sheet SLC":
        df = DB['SLC']
        # Si scope es Brazil, mostramos solo Brazil. Si es All, mostramos All.
        return df[df['Scope'] == country_scope]['SLC'].unique().tolist()
    elif source == "Sheet Labor":
        return DB['Labor']['Item'].unique().tolist()
    return []

def calculate_months(start, end):
    if start and end and end > start:
        d = relativedelta(end, start)
        return d.years * 12 + d.months + (1 if d.days > 0 else 0)
    return 0

# ==========================================
# 3. INTERFAZ DE USUARIO (RENDER LOOP)
# ==========================================
st.title("💸 LACOST V11 - Unificada")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
if 'country' not in st.session_state: st.session_state.country = "Colombia"

# Variables derivadas del estado actual
curr_er, curr_scope = get_country_info(st.session_state.country)

# Agrupamos por secciones de UI_CONFIG
ui_df = DB['UI']
grouped = ui_df.groupby('Section', sort=False)

# Crear estructura de Tabs si es necesario
main_container = st.container()
tabs_created = {} # Para guardar las referencias a los tabs

# Identificar Tabs necesarios
tab_names = []
for name in grouped.groups.keys():
    if "-Tab" in str(name):
        # Extraer nombre del tab (ej: Servicios, Labor)
        t_name = str(name).split('-')[1] # Tab1, Tab2...
        if t_name not in tab_names: tab_names.append(t_name)

if tab_names:
    tabs = st.tabs([t.replace("Tab1", "Servicios").replace("Tab2", "Labor") for t in tab_names])
    for i, t_name in enumerate(tab_names):
        tabs_created[t_name] = tabs[i]

# RENDERIZADO
for section, group in grouped:
    sec_str = str(section).strip()
    
    # Lógica de Ubicación
    if "-slidebar" in sec_str:
        cont = st.sidebar
        title = sec_str.split('-')[0].split('.')[1].strip()
    elif "-Tab" in sec_str:
        # Buscar qué tab es
        t_key = [t for t in tab_names if t in sec_str][0]
        cont = tabs_created[t_key]
        title = sec_str.split('-')[0].split('.')[1].strip()
    else:
        cont = main_container
        title = sec_str.split('-')[0].split('.')[1].strip() if '.' in sec_str else sec_str

    with cont:
        if "-Tab" not in sec_str: st.subheader(title) # No repetir titulo en tabs
        
        for idx, row in group.iterrows():
            lbl = row['Field Label']
            dtype = row['Data Type']
            src = row['Source / Options']
            k = lbl # ID único
            
            # --- WIDGETS ---
            if dtype == 'Dropdown':
                opts = get_options(src, curr_scope)
                val = st.selectbox(lbl, opts, key=k)
                st.session_state.inputs[k] = val
                
                if lbl == 'Country':
                    st.session_state.country = val
                    st.caption(f"Tasa: {get_country_info(val)[0]}")

            elif dtype == 'Date':
                val = st.date_input(lbl, date.today(), key=k)
                st.session_state.inputs[k] = val

            elif dtype in ['text', 'string(20)']:
                # Autocompletado L40 / Conga
                val_disp = ""
                if lbl in ['L40', 'Go To Conga']:
                    off = st.session_state.inputs.get('Offering')
                    if off:
                        row_off = DB['Offering'][DB['Offering']['Offering'] == off]
                        if not row_off.empty:
                            val_disp = row_off['L40'].values[0] if lbl=='L40' else row_off['Load in conga'].values[0]
                
                st.text_input(lbl, value=val_disp, disabled=(lbl in ['L40','Go To Conga']), key=k)
                st.session_state.inputs[k] = val_disp

            elif dtype in ['Number', 'Number(int)']:
                val_num = 0.0
                disabled = False
                
                # Calculados
                if "Contract Period" in lbl:
                    val_num = calculate_months(st.session_state.inputs.get('Contract Start Date'), st.session_state.inputs.get('Contract End Date'))
                    disabled = True
                elif "Duration1" in lbl:
                    val_num = calculate_months(st.session_state.inputs.get('DI1'), st.session_state.inputs.get('DE1'))
                    disabled = True
                elif "Duration2" in lbl:
                    val_num = calculate_months(st.session_state.inputs.get('DI2'), st.session_state.inputs.get('DE2'))
                    disabled = True
                elif lbl == "RR/BR Cost":
                    l_item = st.session_state.inputs.get('RR/BR')
                    if l_item and st.session_state.country in DB['Labor'].columns:
                        r = DB['Labor'][DB['Labor']['Item'] == l_item]
                        if not r.empty:
                            local = float(r[st.session_state.country].values[0])
                            val_num = local / curr_er # Dividido por ER segun regla V11
                    disabled = True
                elif "Total" in lbl:
                    val_num = st.session_state.inputs.get(lbl, 0.0)
                    disabled = True
                
                st.number_input(lbl, value=float(val_num), disabled=disabled, key=k)
                st.session_state.inputs[k] = val_num

            elif dtype == 'Radio':
                opts = get_options(src, curr_scope) # Currency usa Sheet Countries tambien
                if not opts and "," in str(src): opts = src.split(',')
                st.radio(lbl, opts, horizontal=True, key=k)

# ==========================================
# 4. BOTÓN CÁLCULO
# ==========================================
st.markdown("---")
if st.button("CALCULAR TOTALES", type="primary"):
    inp = st.session_state.inputs
    
    # 1. Servicios
    u_cost = inp.get('USD Unit Cost', 0.0)
    sqty = inp.get('SQty', 0.0)
    dur1 = inp.get('Duration1', 0)
    slc = inp.get('SLC')
    
    # Factor SLC
    uplf = 1.0
    if slc:
        rs = DB['SLC'][DB['SLC']['SLC'] == slc]
        # Filtrar por scope tambien si es necesario, pero SLC code deberia ser unico
        if not rs.empty: uplf = float(rs['UPLF'].values[0])
        
    tot_svc = u_cost * sqty * uplf * dur1
    
    # 2. Labor
    l_cost_usd = inp.get('RR/BR Cost', 0.0) # Ya viene dividido por ER
    lqty = inp.get('Monthly Hours', 0.0) # Ojo: Etiqueta V11 cambio a Monthly Hours
    dur2 = inp.get('Duration2', 0)
    
    # Regla V11 Labor: Costo Unitario USD * Horas * Duracion? 
    # Logic Rules dice: Total Labor Cost = Logic_rules. Asumo (Costo * Qty * Duration) o solo (Costo * Qty) si es mensual.
    # Si Monthly Hours es horas por mes, entonces * duracion. Si es Qty total, no.
    # Asumiremos Costo Mensual Total = (Costo Hora * Horas) * Meses ??
    # V10 era Unit * Qty. V11 introduce Monthly Hours y Duration2.
    # FORMULA LOGICA: Costo Unitario (USD) * Monthly Hours * Duration2
    tot_lab = l_cost_usd * lqty * dur2
    
    grand = tot_svc + tot_lab
    
    # Guardar
    st.session_state.inputs['Total Service Cost'] = tot_svc
    st.session_state.inputs['Total Labor Cost'] = tot_lab
    st.session_state.inputs['Total Cost'] = grand
    
    st.success("Cálculo Completado")
    st.rerun()
