import streamlit as st
import pandas as pd
import io
import random
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="LAcostWeb V11", layout="wide")

st.markdown("""
<style>
    /* Estilo Compacto 8pt (11px) */
    html, body, [class*="css"], .stTextInput, .stNumberInput, .stSelectbox, .stDateInput {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 11px !important;
    }
    h1 { font-size: 16px !important; padding: 5px 0 !important; }
    h2 { font-size: 14px !important; padding: 2px 0 !important; border-bottom: 1px solid #ddd; }
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"], .stDateInput input {
        min-height: 24px !important;
        height: 24px !important;
    }
    label { font-size: 10px !important; margin-bottom: 0px !important; }
    
    /* Layout */
    .block-container { padding-top: 1rem !important; padding-bottom: 5rem !important; }
    div[data-testid="column"] { padding: 0px 4px !important; }
    
    /* Totales Flotantes o Fijos al final */
    .total-box {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. MOTOR DE DATOS
# ==========================================
@st.cache_data
def load_data():
    data = {}
    
    # UI CONFIG
    ui = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. Configuracion-slidebar,-,Country,Dropdown,Yes,Sheet Countries
1. Configuracion-slidebar,-,Currency,Radio,Yes,"USD, Local"
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
    data['UI'] = pd.read_csv(io.StringIO(ui))

    # COUNTRIES
    data['Countries'] = pd.DataFrame({
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'E/R': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
        'Scope': ['All', 'Brazil', 'All', 'All', 'All', 'All', 'All', 'All', 'All']
    })

    # OFFERING
    offering = """Offering,L40,Load in conga
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
    data['Offering'] = pd.read_csv(io.StringIO(offering))

    # SLC
    slc = """Scope,SLC,UPLF,Desc
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
    data['SLC'] = pd.read_csv(io.StringIO(slc))

    # LABOR
    labor = """Item,Argentina,Brazil,Chile,Colombia,Ecuador,Peru,Mexico,Uruguay,Venezuela
System Z,304504.2,2803.85,2165270.4,2054058.99,991.20,1284.60,12857.25,30167.39,102721.98
Power HE,194856.48,1516.61,486361.26,540008.96,340.52,505.85,5857.95,18987.51,40555.17
Power LE,162675.24,742.22,486361.26,379581.99,283.76,312.87,3860.85,10986.01,36819.82
System X HE,66943.8,0,101090.22,108029.93,153.10,211.05,1054.2,8828.82,112860.77
B7 (Senior),40166.28,186.82,54081.72,126000.0,79.19,216.45,673.05,3581.26,20998.96"""
    data['Labor'] = pd.read_csv(io.StringIO(labor))

    # RISK
    data['Risk'] = pd.read_csv(io.StringIO("Level,Percentage\nLow,0.02\nMedium,0.05\nHigh,0.08"))
    
    return data

DB = load_data()

# ==========================================
# 2. LÓGICA
# ==========================================

def get_country_info(country):
    row = DB['Countries'][DB['Countries']['Country'] == country]
    if not row.empty:
        er = 1.0 if country == "Ecuador" else float(row['E/R'].values[0])
        scope = "Brazil" if country == "Brazil" else "All"
        return er, scope
    return 1.0, "All"

def get_options(source, country_scope):
    if source == "Sheet Countries": return DB['Countries']['Country'].unique().tolist()
    elif source == "Sheet Risk": return DB['Risk']['Level'].unique().tolist()
    elif source == "Sheet Offering": return DB['Offering']['Offering'].unique().tolist()
    elif source == "Sheet SLC":
        df = DB['SLC']
        return df[df['Scope'] == country_scope]['SLC'].unique().tolist()
    elif source == "Sheet Labor": return DB['Labor']['Item'].unique().tolist()
    return []

def calculate_months_widget(start_lbl, end_lbl):
    """
    Busca el valor DIRECTAMENTE en el session_state del WIDGET.
    Clave del widget = Label + "_wdg"
    """
    try:
        k_start = start_lbl + "_wdg"
        k_end = end_lbl + "_wdg"
        
        # Verificar si existen en el estado actual
        s = st.session_state.get(k_start)
        e = st.session_state.get(k_end)
        
        if s and e and e >= s:
            d = relativedelta(e, s)
            return d.years * 12 + d.months + (1 if d.days > 0 else 0)
    except:
        pass
    return 0

# ==========================================
# 3. INTERFAZ
# ==========================================

if 'inputs' not in st.session_state: st.session_state.inputs = {}
if 'country' not in st.session_state: st.session_state.country = "Colombia"
if 'consecutivo' not in st.session_state: 
    st.session_state.consecutivo = f"LAcostWeb-{random.randint(1001,9999)}"

# SIDEBAR: TITULO + CONFIGURACIÓN
st.sidebar.markdown(f"### {st.session_state.consecutivo}")

curr_er, curr_scope = get_country_info(st.session_state.country)

# Separar secciones
ui_df = DB['UI']
sections_main = ui_df[~ui_df['Section'].str.startswith('4.')] # Todo menos Totales
sections_total = ui_df[ui_df['Section'].str.startswith('4.')] # Solo Totales

grouped = sections_main.groupby('Section', sort=False)

# Tabs
main_container = st.container()
tab_names = []
for name in grouped.groups.keys():
    if "-Tab" in str(name):
        t_name = str(name).split('-')[1]
        if t_name not in tab_names: tab_names.append(t_name)

tabs_obj = {}
if tab_names:
    t_instances = st.tabs([t.replace("Tab1", "1. Servicios").replace("Tab2", "2. Labor") for t in tab_names])
    for i, tn in enumerate(tab_names): tabs_obj[tn] = t_instances[i]

# RENDER LOOP PRINCIPAL
for section, group in grouped:
    sec_str = str(section).strip()
    
    # Ubicación
    if "-slidebar" in sec_str:
        cont = st.sidebar
        title = sec_str.split('-')[0].split('.')[1].strip()
    elif "-Tab" in sec_str:
        t_key = [t for t in tab_names if t in sec_str][0]
        cont = tabs_obj[t_key]
        title = ""
    else:
        cont = main_container
        title = sec_str.split('-')[0].split('.')[1].strip() if '.' in sec_str else sec_str

    with cont:
        if title: st.subheader(title)
        
        for idx, row in group.iterrows():
            lbl = row['Field Label'].strip()
            dtype = row['Data Type']
            src = row['Source / Options']
            
            # ID único del widget
            widget_key = lbl + "_wdg"
            
            # --- DROPDOWN ---
            if dtype == 'Dropdown':
                opts = get_options(src, curr_scope)
                idx_sel = 0
                
                # Restaurar valor previo
                curr_val = st.session_state.inputs.get(lbl)
                if curr_val in opts: idx_sel = opts.index(curr_val)
                
                val = st.selectbox(lbl, opts, index=idx_sel, key=widget_key)
                st.session_state.inputs[lbl] = val # Guardar
                
                if lbl == 'Country':
                    st.session_state.country = val
                    st.caption(f"Tasa: {get_country_info(val)[0]}")

            # --- FECHAS ---
            elif dtype == 'Date':
                # Default 2026
                default_d = date(2026, 1, 1)
                if any(x in lbl for x in ["End", "DE", "Fin"]): default_d = date(2026, 12, 31)
                
                # Si no hay valor en inputs, usar default. Si hay, usar guardado.
                val_init = st.session_state.inputs.get(lbl, default_d)
                
                val = st.date_input(lbl, value=val_init, key=widget_key)
                st.session_state.inputs[lbl] = val

            # --- RADIO ---
            elif dtype == 'Radio':
                opts = str(src).split(',')
                # Caso especial Currency para no mostrar Sheet Countries
                if lbl == "Currency": opts = ["USD", "Local"]
                
                # Restaurar
                idx_sel = 0
                curr_val = st.session_state.inputs.get(lbl)
                if curr_val in opts: idx_sel = opts.index(curr_val)
                
                val = st.radio(lbl, opts, index=idx_sel, horizontal=True, key=widget_key)
                st.session_state.inputs[lbl] = val

            # --- TEXT ---
            elif dtype in ['text', 'string(20)']:
                val_disp = st.session_state.inputs.get(lbl, "")
                
                # Auto-Fill Offering
                if lbl in ['L40', 'Go To Conga']:
                    off = st.session_state.inputs.get('Offering')
                    if off:
                        r = DB['Offering'][DB['Offering']['Offering'] == off]
                        if not r.empty:
                            val_disp = r['L40'].values[0] if lbl=='L40' else r['Load in conga'].values[0]
                
                st.text_input(lbl, value=val_disp, disabled=(lbl in ['L40','Go To Conga']), key=widget_key)
                st.session_state.inputs[lbl] = val_disp

            # --- NUMBERS / CALCULATED ---
            elif dtype in ['Number', 'Number(int)']:
                val_num = 0.0
                is_disabled = False
                
                # --- CALCULOS EN VIVO ---
                if "Contract Period" in lbl:
                    val_num = calculate_months_widget('Contract Start Date', 'Contract End Date')
                    is_disabled = True
                elif "Duration1" in lbl:
                    val_num = calculate_months_widget('DI1', 'DE1')
                    is_disabled = True
                elif "Duration2" in lbl:
                    val_num = calculate_months_widget('DI2', 'DE2')
                    is_disabled = True
                elif lbl == "RR/BR Cost":
                    l_item = st.session_state.inputs.get('RR/BR')
                    if l_item and st.session_state.country in DB['Labor'].columns:
                        r = DB['Labor'][DB['Labor']['Item'] == l_item]
                        if not r.empty:
                            val_num = float(r[st.session_state.country].values[0]) / curr_er
                    is_disabled = True
                else:
                    # Input normal
                    val_num = st.session_state.inputs.get(lbl, 0.0)

                st.number_input(lbl, value=float(val_num), disabled=is_disabled, key=widget_key)
                st.session_state.inputs[lbl] = val_num

# ==========================================
# 4. TOTALES (AL FINAL)
# ==========================================
st.markdown("---")
st.subheader("4. Resumen Total")

c_tot_1, c_tot_2, c_tot_3 = st.columns(3)

# Botón Calcular
if st.button("CALCULAR COTIZACIÓN", type="primary", use_container_width=True):
    inp = st.session_state.inputs
    
    # Servicios
    cost = inp.get('USD Unit Cost', 0.0)
    qty = inp.get('SQty', 0.0)
    dur1 = inp.get('Duration1', 0.0)
    slc = inp.get('SLC')
    
    uplf = 1.0
    if slc:
        r = DB['SLC'][DB['SLC']['SLC'] == slc]
        if not r.empty: uplf = float(r['UPLF'].values[0])
            
    tot_svc = cost * qty * uplf * dur1
    
    # Labor
    l_cost_usd = inp.get('RR/BR Cost', 0.0)
    l_hours = inp.get('Monthly Hours', 0.0)
    dur2 = inp.get('Duration2', 0.0)
    
    tot_lab = l_cost_usd * l_hours * dur2
    grand = tot_svc + tot_lab
    
    # Guardar Totales
    st.session_state.inputs['Total Service Cost'] = tot_svc
    st.session_state.inputs['Total Labor Cost'] = tot_lab
    st.session_state.inputs['Total Cost'] = grand
    
    st.success("Calculado exitosamente.")
    st.rerun()

# Mostrar Totales (Solo Lectura)
with c_tot_1:
    st.metric("Total Servicios", f"${st.session_state.inputs.get('Total Service Cost',0.0):,.2f}")
with c_tot_2:
    st.metric("Total Labor", f"${st.session_state.inputs.get('Total Labor Cost',0.0):,.2f}")
with c_tot_3:
    st.metric("TOTAL GENERAL", f"${st.session_state.inputs.get('Total Cost',0.0):,.2f}")
