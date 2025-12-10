import streamlit as st
import pandas as pd
import io
from datetime import date
from dateutil.relativedelta import relativedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================
st.set_page_config(page_title="LACOST V9 Final", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    h1 { font-size: 1.5rem !important; }
    /* Estilo para resaltar totales */
    div[data-testid="metric-container"] {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. DATOS V9 INTEGRADOS (Hardcoded)
# ==========================================
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
    tables['QA_RISK'] = pd.DataFrame({'Level': ['Low', 'Medium', 'High']})
    tables['Offering'] = pd.DataFrame({'Offering': ['IBM Hardware Resell', 'IBM Support for Red Hat', 'IBM Customized Support HW']})
    
    return tables

# Carga directa de datos (Sin botones de carga)
ui_df = get_default_ui()
db_tables = get_default_db()
# Limpieza de headers
ui_df.columns = ui_df.columns.str.strip()

# ==========================================
# 2. LÓGICA DE NEGOCIO (Lookups V9)
# ==========================================
def get_options(source, country):
    if pd.isna(source): return []
    s = str(source).strip()
    
    if "### TABLE:" not in s:
        return [x.strip() for x in s.split(',')] if ',' in s else []
    
    parts = s.replace("### TABLE:", "").split('(')
    tname = parts[0].strip()
    cname = parts[1].replace(')', '').strip() if len(parts)>1 else None
    
    if tname not in db_tables: return []
    df = db_tables[tname]
    
    # Filtro Scope
    if 'Scope' in df.columns and country:
        tgt = "Brazil" if country == "Brazil" else "no brazil"
        df = df[df['Scope'].str.lower().str.contains(tgt.lower(), na=False) | (df['Scope']=='All')]
        
    if cname and cname in df.columns: return df[cname].unique().tolist()
    
    # Fallback Labor
    if tname == "LABOR":
        if 'Item' in df.columns: return df['Item'].unique().tolist()
        
    return []

def calculate_duration():
    try:
        s = st.session_state.get('Contract Start Date')
        e = st.session_state.get('Contract End Date')
        if s and e:
            d = relativedelta(e, s)
            return d.years*12 + d.months + (1 if d.days > 0 else 0)
    except: pass
    return 12

# ==========================================
# 3. RENDER UI
# ==========================================
st.title("💸 Cotizador V9")

if 'inputs' not in st.session_state: st.session_state.inputs = {}

# Variables Globales por defecto
if 'global_country' not in st.session_state: st.session_state.global_country = "Colombia"
if 'global_er' not in st.session_state: st.session_state.global_er = 3775.0
if 'global_dur' not in st.session_state: st.session_state.global_dur = 12

src_col = 'Source / Options' if 'Source / Options' in ui_df.columns else 'Source'

for section, group in ui_df.groupby('Section', sort=False):
    
    # Detección de Slide (Barra lateral)
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
        
        for idx, row in group.iterrows():
            lbl = row['Field Label']
            dtype = str(row['Data Type']).strip()
            src = row[src_col]
            k = f"{lbl}_{idx}"
            
            # --- DROPDOWN ---
            if dtype == 'Dropdown':
                if lbl == 'Country':
                    opts = get_options(src, None)
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.global_country = val
                    st.session_state.inputs[lbl] = val
                    
                    if 'COUNTRIES' in db_tables:
                        cdf = db_tables['COUNTRIES']
                        row = cdf[cdf['Country'] == val]
                        if not row.empty:
                            raw_er = float(row['E/R'].values[0])
                            st.session_state.global_er = 1.0 if val == "Ecuador" else raw_er
                            # Mostrar KPI pequeño en sidebar
                            if is_slide:
                                st.caption(f"💰 Tasa Cambio: {st.session_state.global_er:,.2f}")
                else:
                    opts = get_options(src, st.session_state.global_country)
                    val = st.selectbox(lbl, opts, key=k)
                    st.session_state.inputs[lbl] = val

            # --- DATE ---
            elif dtype == 'Date':
                val = st.date_input(lbl, date.today(), key=lbl) # Key=Label para encontrarlo facil
                st.session_state.inputs[lbl] = val
                
            # --- NUMBER ---
            elif dtype == 'Number':
                if "Period" in lbl or "Duration" in lbl:
                    calc_dur = calculate_duration()
                    st.session_state.global_dur = calc_dur
                    st.number_input(lbl, value=calc_dur, disabled=True, key=k)
                    st.session_state.inputs[lbl] = calc_dur
                else:
                    val = st.number_input(lbl, min_value=0.0, step=1.0, key=k)
                    st.session_state.inputs[lbl] = val
            
            # --- RADIO ---
            elif dtype == 'Radio':
                opts = [x.strip() for x in str(src).split(',') if "###" not in x]
                val = st.radio(lbl, opts, horizontal=True, key=k)
                st.session_state.inputs[lbl] = val

        if not is_slide: st.divider()

# ==========================================
# 4. CÁLCULO FINAL
# ==========================================
st.header("Resultados")

if st.button("Calcular Totales", type="primary"):
    inputs = st.session_state.inputs
    country = st.session_state.global_country
    er = st.session_state.global_er
    dur = st.session_state.global_dur
    
    # Recuperación flexible de variables
    def get_val(key_part, default=0.0):
        for k, v in inputs.items():
            if key_part.lower() in k.lower(): return v
        return default
    
    usd_cost = get_val("USD Unit", 0.0)
    sqty = get_val("SQty", 0.0)
    slc_sel = get_val("SLC", "")
    lqty = get_val("LQty", 0.0)
    lab_sel = get_val("RR/BR", "")
    
    # 1. Factor SLC
    uplf = 1.0
    if 'SLC' in db_tables:
        sdf = db_tables['SLC']
        col_desc = next((c for c in ['Desc','SLC','ID_Desc'] if c in sdf.columns), None)
        if col_desc:
            tgt = "Brazil" if country=="Brazil" else "no brazil"
            row = sdf[sdf['Scope'].str.lower().str.contains(tgt.lower(), na=False) & (sdf[col_desc]==slc_sel)]
            if not row.empty: uplf = float(row['UPLF'].values[0])

    # 2. Tarifa Labor
    lab_rate_usd = 0.0
    if 'LABOR' in db_tables:
        ldf = db_tables['LABOR']
        lrow = ldf[ldf.apply(lambda x: str(lab_sel) in str(x.values), axis=1)]
        if not lrow.empty and country in ldf.columns:
            local_rate = float(lrow[country].values[0])
            lab_rate_usd = local_rate / er
            
    # Totales
    tot_serv = usd_cost * sqty * uplf * dur
    tot_lab = lab_rate_usd * lqty
    grand_tot = tot_serv + tot_lab
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Servicios", f"${tot_serv:,.2f}", help=f"${usd_cost} * {sqty} * {uplf} * {dur}m")
    c2.metric("Total Labor", f"${tot_lab:,.2f}", help=f"(Local / {er}) * {lqty}")
    c3.metric("GRAN TOTAL", f"${grand_tot:,.2f}")
