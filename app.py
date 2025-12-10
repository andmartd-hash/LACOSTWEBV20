import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS (V10)
# ==========================================
st.set_page_config(page_title="LACOST V10 System", layout="wide")

# CSS PARA TAMAÑO DE LETRA 8-10px Y VISTA COMPACTA
st.markdown("""
<style>
    /* Reducir fuentes globales */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 12px !important; /* Equivalente visual a 8pt en web */
    }
    
    /* Títulos más pequeños */
    h1 { font-size: 1.4rem !important; padding: 0.5rem 0 !important; }
    h2 { font-size: 1.1rem !important; padding: 0.2rem 0 !important; border-bottom: 1px solid #eee; }
    h3 { font-size: 1.0rem !important; }
    
    /* Inputs compactos */
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stDateInput input {
        font-size: 12px !important;
        height: 28px !important;
        min-height: 28px !important;
    }
    
    /* Labels pegados al input */
    label {
        font-size: 11px !important;
        margin-bottom: 0px !important;
    }
    
    /* Reducir espacios entre bloques */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    div[data-testid="column"] {
        padding: 0px 5px !important;
    }
    div.stButton > button {
        font-size: 12px !important;
        padding: 4px 10px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS V10 INTEGRADOS (Simulando tus archivos)
# ==========================================

def load_v10_data():
    data = {}
    
    # 1. UI_CONGIF.csv
    ui_csv = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. General Info-slide,-,Country,Dropdown,Yes,Countries
1. General Info-slide,-,Currency,Radio,Yes,"USD, Local"
1. General Info-slide,-,Contract Start Date,Date,Yes,User imput
1. General Info-slide,-,Contract End Date,Date,Yes,User imput
1. General Info-slide,-,Contract Period,Number,Yes,Calculated
2. Input Costs,-,QA Risk,Dropdown,Yes,Risk
2. Input Costs,Servicios,Offering,Dropdown,Yes,Offering
2. Input Costs,Servicios,L40,text,Yes,Calculated
2. Input Costs,Servicios,Go To Conga,text,Yes,Calculated
2. Input Costs,Servicios,Start Service Date,Date,Yes,User imput
2. Input Costs,Servicios,End Service Date,Date,Yes,User imput
2. Input Costs,Servicios,Duration,Number,Yes,Calculated
2. Input Costs,Servicios,SLC,Dropdown,Yes,SLC
2. Input Costs,Servicios,USD Unit Cost,Number,Yes,User imput
2. Input Costs,Servicios,SQty,Number,Yes,User imput
3. Input Costs,Labor RR/BR,RR/BR,Dropdown,Yes,Labor
3. Input Costs,Labor RR/BR,RR/BR Cost,Number,Yes,Calculated
3. Input Costs,Labor RR/BR,LQty,Number,Yes,User imput
4. Totales,-,Total Service Cost,Number,Yes,Logic_rules
4. Totales,-,Total Labor Cost,Number,Yes,Logic_rules
4. Totales,-,Total Cost,Number,Yes,Logic_rules
"""
    data['UI'] = pd.read_csv(io.StringIO(ui_csv))
    
    # 2. Countries.csv
    data['Countries'] = pd.DataFrame({
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN'],
        'E/R': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42],
        'Scope': ['No Brazil', 'Brazil', 'No Brazil', 'No Brazil', 'No Brazil', 'No Brazil', 'No Brazil']
    })
    
    # 3. Offering.csv
    data['Offering'] = pd.DataFrame({
        'Offering': ['IBM Hardware Resell', 'IBM Support for Red Hat', 'IBM Customized Support HW', 'Relocation Services'],
        'L40': ['6942-1BT', '6948-B73', '6942-76V', '6942-54E'],
        'Load in Conga': ['Location Based', 'Conga by CSV', 'Location Based', 'Location Based']
    })
    
    # 4. SLC.csv
    data['SLC'] = pd.DataFrame([
        {'Scope': 'No Brazil', 'Desc': '24X7SDOn-site arrival', 'UPLF': 1.0},
        {'Scope': 'No Brazil', 'Desc': '24X74On-site Response', 'UPLF': 1.5},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24', 'UPLF': 1.278}
    ])
    
    # 5. Labor.csv (Matriz)
    data['Labor'] = pd.DataFrame([
        {'Item': 'System Z', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Brazil': 2803.85, 'Ecuador': 991.20},
        {'Item': 'Power HE', 'Argentina': 194856.48, 'Colombia': 540008.96, 'Brazil': 1516.61, 'Ecuador': 340.52},
        {'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Brazil': 186.82, 'Ecuador': 79.19}
    ])
    
    # 6. Risk.csv
    data['Risk'] = pd.DataFrame({'Level': ['Low', 'Medium', 'High'], 'Percentage': [0.02, 0.05, 0.08]})
    
    return data

DB = load_v10_data()
UI_DF = DB['UI']
# Limpieza de columnas
UI_DF.columns = UI_DF.columns.str.strip()

# ==========================================
# 2. FUNCIONES DE LÓGICA
# ==========================================

def get_er(country):
    """Obtiene la tasa de cambio"""
    df = DB['Countries']
    row = df[df['Country'] == country]
    if not row.empty:
        # Si es Ecuador, ER siempre es 1
        return 1.0 if country == "Ecuador" else float(row['E/R'].values[0])
    return 1.0

def get_scope(country):
    """Define si es Brazil o No Brazil"""
    if country == "Brazil": return "Brazil"
    return "No Brazil"

def get_dropdown_options(source_name, country_context):
    """Obtiene opciones filtradas"""
    options = []
    
    if source_name == "Countries":
        return DB['Countries']['Country'].unique().tolist()
    
    elif source_name == "Risk":
        return DB['Risk']['Level'].unique().tolist()
    
    elif source_name == "Offering":
        return DB['Offering']['Offering'].unique().tolist()
    
    elif source_name == "SLC":
        df = DB['SLC']
        scope = get_scope(country_context)
        # Filtrar por Scope
        df_filtered = df[df['Scope'] == scope]
        return df_filtered['Desc'].unique().tolist()
    
    elif source_name == "Labor":
        return DB['Labor']['Item'].unique().tolist()
        
    return []

def calculate_months(start_date, end_date):
    """Calcula duración en meses"""
    if start_date and end_date:
        d = relativedelta(end_date, start_date)
        return d.years * 12 + d.months + (1 if d.days > 0 else 0)
    return 0

def lookup_offering_data(offering_name):
    """Busca L40 y Conga"""
    df = DB['Offering']
    row = df[df['Offering'] == offering_name]
    if not row.empty:
        return row['L40'].values[0], row['Load in Conga'].values[0]
    return "", ""

# ==========================================
# 3. RENDERIZADO DE LA UI
# ==========================================
st.title("💸 LACOST V10 System")

# Inicializar sesión
if 'inputs' not in st.session_state: st.session_state.inputs = {}
if 'global_country' not in st.session_state: st.session_state.global_country = "Colombia"

# Variables globales derivadas
curr_er = get_er(st.session_state.global_country)
curr_currency = "USD" if st.session_state.global_country == "Ecuador" else "Local"

# Agrupar por Sección
for section_name, section_group in UI_DF.groupby('Section', sort=False):
    
    # Detectar -slide
    sec_str = str(section_name).strip()
    is_sidebar = "-slide" in sec_str.lower()
    
    # Contenedor destino
    if is_sidebar:
        container = st.sidebar
        title = sec_str.lower().replace("-slide", "").title()
    else:
        container = st.container()
        title = sec_str
        
    with container:
        st.header(title)
        
        # Iterar campos
        for idx, row in section_group.iterrows():
            label = row['Field Label']
            dtype = row['Data Type']
            source = row['Source / Options']
            key = label # Usamos label como ID único
            
            # --- MANEJO DE TIPOS DE DATOS ---
            
            # 1. DROPDOWN
            if dtype == 'Dropdown':
                opts = get_dropdown_options(source, st.session_state.global_country)
                # Seleccionar valor previo o default
                idx_sel = 0
                if key in st.session_state.inputs and st.session_state.inputs[key] in opts:
                    idx_sel = opts.index(st.session_state.inputs[key])
                
                val = st.selectbox(label, opts, index=idx_sel, key=key+"_widget")
                st.session_state.inputs[key] = val
                
                # Trigger cambio de país
                if label == 'Country':
                    st.session_state.global_country = val
                    st.caption(f"E/R: {get_er(val)}")

            # 2. FECHAS
            elif dtype == 'Date':
                val = st.date_input(label, date.today(), key=key+"_widget")
                st.session_state.inputs[key] = val

            # 3. TEXTO / CALCULADOS (L40, Conga)
            elif dtype == 'text' or dtype == 'Text':
                val_display = ""
                # Auto-rellenar si es L40 o Conga
                if label in ['L40', 'Go To Conga']:
                    off = st.session_state.inputs.get('Offering')
                    if off:
                        l40, conga = lookup_offering_data(off)
                        val_display = l40 if label == 'L40' else conga
                
                st.text_input(label, value=val_display, disabled=True, key=key+"_widget")
                st.session_state.inputs[key] = val_display

            # 4. NUMEROS / CALCULADOS
            elif dtype == 'Number':
                val_num = 0.0
                disabled = False
                
                # Lógica de campos calculados
                if "Period" in label:
                    val_num = calculate_months(st.session_state.inputs.get('Contract Start Date'), st.session_state.inputs.get('Contract End Date'))
                    disabled = True
                elif label == "Duration":
                    val_num = calculate_months(st.session_state.inputs.get('Start Service Date'), st.session_state.inputs.get('End Service Date'))
                    disabled = True
                elif label == "RR/BR Cost": # Preview de costo labor
                    l_item = st.session_state.inputs.get('RR/BR')
                    if l_item:
                        df_l = DB['Labor']
                        r = df_l[df_l['Item'] == l_item]
                        if not r.empty and st.session_state.global_country in r.columns:
                            val_num = float(r[st.session_state.global_country].values[0])
                    disabled = True
                elif "Total" in label: # Totales finales
                     val_num = st.session_state.inputs.get(label, 0.0)
                     disabled = True
                
                if disabled:
                    st.number_input(label, value=float(val_num), disabled=True, key=key+"_widget")
                    st.session_state.inputs[key] = val_num
                else:
                    # Input editable
                    val = st.number_input(label, min_value=0.0, step=1.0, key=key+"_widget")
                    st.session_state.inputs[key] = val

            # 5. RADIO
            elif dtype == 'Radio':
                opts = str(source).replace('"', '').split(',')
                val = st.radio(label, opts, horizontal=True, key=key+"_widget")
                st.session_state.inputs[key] = val

        if not is_sidebar: st.markdown("---")

# ==========================================
# 4. BOTÓN DE CÁLCULO
# ==========================================
col_btn, col_info = st.columns([1, 4])

with col_btn:
    if st.button("CALCULAR COTIZACIÓN", type="primary"):
        # Recuperar datos
        inp = st.session_state.inputs
        country = st.session_state.global_country
        er = get_er(country)
        
        # 1. Servicios
        usd_cost = inp.get('USD Unit Cost', 0.0)
        sqty = inp.get('SQty', 0.0)
        dur = inp.get('Duration', 0)
        slc_desc = inp.get('SLC')
        
        # Buscar factor SLC
        uplf = 1.0
        if slc_desc:
            df_s = DB['SLC']
            r = df_s[df_s['Desc'] == slc_desc]
            if not r.empty: uplf = float(r['UPLF'].values[0])
            
        total_svc = usd_cost * sqty * uplf * dur
        
        # 2. Labor
        lqty = inp.get('LQty', 0.0)
        labor_local_price = inp.get('RR/BR Cost', 0.0)
        
        labor_unit_usd = labor_local_price / er
        total_lab = labor_unit_usd * lqty
        
        # 3. Totales
        grand_total = total_svc + total_lab
        
        # Guardar en estado para mostrar en los campos readonly
        st.session_state.inputs['Total Service Cost'] = total_svc
        st.session_state.inputs['Total Labor Cost'] = total_lab
        st.session_state.inputs['Total Cost'] = grand_total
        
        st.success("Calculado.")
        st.rerun()

# Mostrar Resultados Rápidos
with col_info:
    t_svc = st.session_state.inputs.get('Total Service Cost', 0.0)
    t_lab = st.session_state.inputs.get('Total Labor Cost', 0.0)
    t_tot = st.session_state.inputs.get('Total Cost', 0.0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Servicios", f"${t_svc:,.2f}")
    c2.metric("Labor", f"${t_lab:,.2f}")
    c3.metric("TOTAL USD", f"${t_tot:,.2f}")
