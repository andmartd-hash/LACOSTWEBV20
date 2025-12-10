import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="LACOST V9 - Full Fields", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    .stNumberInput input { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS COMPLETOS (TODOS LOS CAMPOS V9)
# ==========================================
def get_default_ui():
    # He agregado TODAS las filas de tu archivo original
    csv_data = """Section,Sub-Section,Field Label,Data Type,Mandatory,Source / Options
1. General Info-slide,-,Country,Dropdown,Yes,### TABLE: COUNTRIES(Country)
1. General Info-slide,-,Currency,Radio,Yes,"USD, Local"
1. General Info-slide,-,Contract Start Date,Date,Yes,User imput
1. General Info-slide,-,Contract End Date,Date,Yes,User imput
1. General Info-slide,-,Contract Period,Number,Yes,Calculated
2. Input Costs,-,QA Risk,Dropdown,Yes,### TABLE: QA_RISK (Level)
2. Input Costs,Servicios,Offering,Dropdown,Yes,### TABLE: Offering(Offering)
2. Input Costs,Servicios,L40,text,Yes,### TABLE: Offering(L40)
2. Input Costs,Servicios,Go To Conga,text,Yes,### TABLE: Offering(Load in Conga)
2. Input Costs,Servicios,Start Service Date,Date,Yes,User imput
2. Input Costs,Servicios,End Service Date,Date,Yes,User imput
2. Input Costs,Servicios,Duration,Number,Yes,Calculated
2. Input Costs,Servicios,SLC,Dropdown,Yes,### TABLE: SLC(Desc)
2. Input Costs,Servicios,USD Unit Cost,Number,Yes,User imput
2. Input Costs,Servicios,SQty,Number,Yes,User imput
3. Input Costs,Labor RR/BR,RR/BR,Dropdown,Yes,### TABLE: LABOR(Item)
3. Input Costs,Labor RR/BR,RR/BR Cost,Number,Yes,Calculated
3. Input Costs,Labor RR/BR,LQty,Number,Yes,User imput
4. Input Costs,Total Cost,Total Service Cost,Number,Yes,Logic_rules
4. Input Costs,Total Cost,Total Labor Cost,Number,Yes,Logic_rules
4. Input Costs,Total Cost,Total Cost,Number,Yes,Logic_rules
"""
    return pd.read_csv(io.StringIO(csv_data))

def get_default_db():
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
        {'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Brazil': 186.82},
        {'Item': 'Power HE', 'Argentina': 194856.48, 'Colombia': 540008.96, 'Brazil': 1516.61}
    ])
    # Tabla Offering enriquecida para L40 y Conga
    tables['Offering'] = pd.DataFrame({
        'Offering': ['IBM Hardware Resell', 'IBM Support for Red Hat', 'IBM Customized Support HW'],
        'L40': ['6942-1BT', '6948-B73', '6942-76V'],
        'Load in Conga': ['Location Based', 'Conga by CSV', 'Location Based']
    })
    tables['QA_RISK'] = pd.DataFrame({'Level': ['Low', 'Medium', 'High']})
    
    return tables

ui_df = get_default_ui()
db_tables = get_default_db()
ui_df.columns = ui_df.columns.str.strip()

# ==========================================
# 2. FUNCIONES DE LÓGICA
# ==========================================
def get_options(source, country):
    if pd.isna(source): return []
    s = str(source).strip()
    if "### TABLE:" not in s: return [x.strip() for x in s.split(',')] if ',' in s else []
    
    parts = s.replace("### TABLE:", "").split('(')
    tname = parts[0].strip()
    cname = parts[1].replace(')', '').strip() if len(parts)>1 else None
    
    if tname not in db_tables: return []
    df = db_tables[tname]
    
    if 'Scope' in df.columns and country:
        tgt = "Brazil" if country == "Brazil" else "no brazil"
        df = df[df['Scope'].str.lower().str.contains(tgt.lower(), na=False) | (df['Scope']=='All')]
        
    if cname and cname in df.columns: return df[cname].unique().tolist()
    if tname == "LABOR" and 'Item' in df.columns: return df['Item'].unique().tolist()
    return []

def lookup_value(table_name, search_col, search_val, target_col):
    """Simula un VLOOKUP / BUSCARV"""
    if table_name in db_tables:
        df = db_tables[table_name]
        row = df[df[search_col] == search_val]
        if not row.empty and target_col in row.columns:
            return row[target_col].values[0]
    return ""

def calculate_months(start_k, end_k):
    try:
        s = st.session_state.inputs.get(start_k)
        e = st.session_state.inputs.get(end_k)
        if s and e:
            d = relativedelta(e, s)
            return d.years*12 + d.months + (1 if d.days > 0 else 0)
    except: pass
    return 12

# ==========================================
# 3. RENDER UI
# ==========================================
st.title("💸 Cotizador V9 Full")

if 'inputs' not in st.session_state: st.session_state.inputs = {}
if 'global_country' not in st.session_state: st.session_state.global_country = "Colombia"

src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

for section, group in ui_df.groupby('Section', sort=False):
    
    # Slide detection
    sec_str = str(section).strip()
    is_slide = "-slide" in sec_str.lower()
    
    if is_slide:
        cont = st.sidebar
        title = sec_str.lower().replace("-slide", "").title()
    else:
        cont = st.container()
        title = sec_str
        
    with cont:
        st.header(title)
        
        # Agrupar por Sub-Sección para ordenar mejor visualmente
        for sub, subgroup in group.groupby('Sub-Section', sort=False):
            if sub != "-":
                st.subheader(sub)
            
            for idx, row in subgroup.iterrows():
                lbl = row['Field Label']
                dtype = str(row['Data Type']).strip()
                src = row[src_col]
                # Key único usando label
                k = lbl 
                
                # --- DROPDOWN ---
                if dtype == 'Dropdown':
                    opts = get_options(src, st.session_state.global_country)
                    # Si es Country, no filtramos por country
                    if lbl == 'Country': opts = get_options(src, None)
                        
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.inputs[lbl] = val
                    
                    if lbl == 'Country': st.session_state.global_country = val

                # --- TEXT (Con Autocompletado) ---
                elif dtype == 'text':
                    # Lógica especial para autocompletar L40 y Conga
                    val_default = ""
                    if lbl in ['L40', 'Go To Conga']:
                        offering_sel = st.session_state.inputs.get('Offering')
                        if offering_sel:
                            target_col = 'L40' if lbl == 'L40' else 'Load in Conga'
                            val_default = lookup_value('Offering', 'Offering', offering_sel, target_col)
                    
                    st.text_input(lbl, value=val_default, key=k, disabled=True if val_default else False)
                    st.session_state.inputs[lbl] = val_default

                # --- DATE ---
                elif dtype == 'Date':
                    val = st.date_input(lbl, date.today(), key=k)
                    st.session_state.inputs[lbl] = val

                # --- NUMBER ---
                elif dtype == 'Number':
                    # Logica Duración Automática
                    val_display = 0.0
                    is_disabled = False
                    
                    if "Period" in lbl: # Contract Period
                        val_display = calculate_months('Contract Start Date', 'Contract End Date')
                        is_disabled = True
                    elif lbl == "Duration": # Service Duration
                        val_display = calculate_months('Start Service Date', 'End Service Date')
                        is_disabled = True
                    elif "Total" in lbl: # Totales (resultados)
                         val_display = st.session_state.inputs.get(lbl, 0.0)
                         is_disabled = True
                    elif "RR/BR Cost" in lbl: # Costo Laboral Unitario (Preview)
                         # Intentar mostrar costo referencial
                         lab_item = st.session_state.inputs.get('RR/BR')
                         if lab_item:
                             # Lógica simplificada de lookup precio local
                             df_l = db_tables.get('LABOR', pd.DataFrame())
                             if not df_l.empty and st.session_state.global_country in df_l.columns:
                                 r = df_l[df_l['Item'] == lab_item]
                                 if not r.empty: val_display = float(r[st.session_state.global_country].values[0])
                         is_disabled = True
                    
                    # Render
                    if is_disabled:
                         st.number_input(lbl, value=val_display, disabled=True, key=k)
                         st.session_state.inputs[lbl] = val_display
                    else:
                         val = st.number_input(lbl, min_value=0.0, step=1.0, key=k)
                         st.session_state.inputs[lbl] = val
                
                # --- RADIO ---
                elif dtype == 'Radio':
                    opts = [x.strip() for x in str(src).split(',') if "###" not in x]
                    st.radio(lbl, opts, horizontal=True, key=k)

        if not is_slide: st.divider()

# ==========================================
# 4. CÁLCULO FINAL
# ==========================================
if st.button("Calcular Cotización Full", type="primary"):
    inp = st.session_state.inputs
    country = st.session_state.global_country
    
    # 1. Obtener Tasa E/R
    er = 1.0
    if 'COUNTRIES' in db_tables:
        c_df = db_tables['COUNTRIES']
        row = c_df[c_df['Country'] == country]
        if not row.empty: er = 1.0 if country == "Ecuador" else float(row['E/R'].values[0])
            
    # 2. Servicios
    usd_unit = inp.get('USD Unit Cost', 0.0)
    sqty = inp.get('SQty', 0.0)
    dur_svc = inp.get('Duration', 12)
    slc = inp.get('SLC', '')
    
    # Factor SLC
    uplf = 1.0
    if 'SLC' in db_tables:
        sdf = db_tables['SLC']
        row = sdf[sdf['Desc'] == slc]
        if not row.empty: uplf = float(row['UPLF'].values[0])
            
    total_svc = usd_unit * sqty * uplf * dur_svc
    
    # 3. Labor
    lqty = inp.get('LQty', 0.0)
    rr_cost_local = inp.get('RR/BR Cost', 0.0) # Tomado del preview
    
    # Convertir a USD
    lab_unit_usd = rr_cost_local / er
    total_lab = lab_unit_usd * lqty
    
    grand_total = total_svc + total_lab
    
    # Actualizar campos de solo lectura en UI
    st.session_state.inputs['Total Service Cost'] = total_svc
    st.session_state.inputs['Total Labor Cost'] = total_lab
    st.session_state.inputs['Total Cost'] = grand_total
    
    st.success("¡Cálculo Exitoso! Revisa los campos de totales abajo.")
    st.metric("GRAN TOTAL (USD)", f"${grand_total:,.2f}")
    st.rerun() # Recarga para mostrar los valores en los campos de solo lectura
