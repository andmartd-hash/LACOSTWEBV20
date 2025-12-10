import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA (Layout Wide para aprovechar el ancho) ---
st.set_page_config(page_title="LACOST V20 Compact", layout="wide")

# --- ESTILOS CSS PERSONALIZADOS (MODO COMPACTO) ---
st.markdown("""
<style>
    /* Reducir tamaño de fuente global */
    html, body, [class*="css"] {
        font-size: 14px;
    }
    
    /* Reducir tamaño de Títulos */
    h1 { font-size: 1.8rem !important; padding-bottom: 0.5rem !important; }
    h2 { font-size: 1.4rem !important; padding-top: 0.5rem !important; padding-bottom: 0.2rem !important; }
    h3 { font-size: 1.1rem !important; padding-top: 0.5rem !important; }
    
    /* Reducir altura y relleno de los Inputs (Selectbox, NumberInput, etc.) */
    .stSelectbox div[data-baseweb="select"] > div,
    .stTextInput div[data-baseweb="input"] > div,
    .stNumberInput div[data-baseweb="input"] > div {
        min-height: 35px !important;
        padding-top: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* Reducir espacio entre elementos */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* Ajustar tamaño de etiquetas de los inputs */
    label p {
        font-size: 0.9rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
def load_data():
    # Tabla PAISES
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'ER': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
    }
    df_countries = pd.DataFrame(countries_data)

    # Tabla OFFERINGS
    offerings_list = [
        "IBM Hardware Resell for Server and Storage-Lenovo",
        "1-HWMA MVS SPT other Prod",
        "IBM Support for Red Hat - Enterprise Linux Subscription",
        "IBM Customized Support for Multivendor Hardware Services",
        "IBM Customized Support for Software Services-Logo",
        "System Technical Support Service-MVS-STSS",
        "Relocation Services - External Vendor's Charge"
    ]
    df_offerings = pd.DataFrame(offerings_list, columns=['Offering'])

    # Tabla SLC
    slc_data = [
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response time (M47)', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'no brazil', 'Desc': '24X76Fix time (M2B)', 'UPLF': 1.6},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24 (1.278)', 'UPLF': 1.278},
    ]
    df_slc = pd.DataFrame(slc_data)

    # Tabla LABOR
    labor_data = [
        {'Type': 'Machine Category', 'Item': 'System Z (Cat A)', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Ecuador': 991.20, 'Brazil': 2803.85},
        {'Type': 'Machine Category', 'Item': 'Power HE (Cat C)', 'Argentina': 194856.48, 'Colombia': 540008.96, 'Ecuador': 340.52, 'Brazil': 1516.61},
        {'Type': 'Brand Rate Full', 'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Ecuador': 79.19, 'Brazil': 186.82}
    ]
    df_labor = pd.DataFrame(labor_data)
    
    return df_countries, df_offerings, df_slc, df_labor

df_countries, df_offerings, df_slc, df_labor = load_data()

# ==========================================
# BARRA LATERAL (SIDEBAR)
# ==========================================
with st.sidebar:
    st.header("⚙️ Config Global")
    
    selected_country = st.selectbox("País", df_countries['Country'])
    country_row = df_countries[df_countries['Country'] == selected_country].iloc[0]
    
    if selected_country == "Ecuador":
        er_calc = 1.0
        currency_display = "USD"
    else:
        er_calc = country_row['ER']
        currency_display = country_row['Currency']

    col_kpi1, col_kpi2 = st.columns(2)
    col_kpi1.metric("Moneda", currency_display)
    col_kpi2.metric("Tasa (E/R)", f"{er_calc:,.2f}")
    
    st.markdown("---")
    
    st.subheader("Contrato")
    start_date = st.date_input("Inicio", date.today())
    end_date = st.date_input("Fin", date.today() + relativedelta(months=12))
    
    diff = relativedelta(end_date, start_date)
    duration_months = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
    st.caption(f"Duración: **{duration_months} Meses**")

# ==========================================
# CUERPO PRINCIPAL
# ==========================================
st.subheader("💸 LACOST V20 - Calculadora Cloud")

# --- SECCIÓN 2: SERVICIOS ---
with st.expander("2. Input Costs - Services", expanded=True):
    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        offering = st.selectbox("Offering / Servicio", df_offerings['Offering'])
    with col_s2:
        qa_risk = st.selectbox("QA Risk", ["Low (0.02)", "Medium (0.05)", "High (0.08)"])

    col_s3, col_s4, col_s5 = st.columns([3, 1, 1])
    with col_s3:
        scope_filter = "Brazil" if selected_country == "Brazil" else "no brazil"
        filtered_slc = df_slc[df_slc['Scope'] == scope_filter]
        slc_selection = st.selectbox("SLC Profile", filtered_slc['Desc'])
        slc_factor = filtered_slc[filtered_slc['Desc'] == slc_selection]['UPLF'].values[0] if not filtered_slc.empty else 1.0
        st.caption(f"Factor: **{slc_factor}**")
    with col_s4:
        usd_unit_cost = st.number_input("USD Unit Cost", value=10.0, format="%.2f")
    with col_s5:
        sqty = st.number_input("Qty", min_value=1, value=1)

# --- SECCIÓN 3: LABOR ---
with st.expander("3. Input Costs - Labor", expanded=True):
    col_l1, col_l2 = st.columns([1, 3])
    with col_l1:
        labor_type = st.radio("Tarifa", df_labor['Type'].unique(), horizontal=False)
    with col_l2:
        items_avail = df_labor[df_labor['Type'] == labor_type]['Item'].unique()
        labor_item = st.selectbox("Categoría / Item", items_avail)

    col_l3, col_l4, col_l5 = st.columns(3)
    with col_l3:
        lqty = st.number_input("Horas/Meses", min_value=1, value=1)
    with col_l4:
        try:
            if selected_country in df_labor.columns:
                raw_cost = df_labor[(df_labor['Type'] == labor_type) & (df_labor['Item'] == labor_item)][selected_country].values[0]
                if pd.isna(raw_cost): raw_cost = 0
                final_labor_unit_cost = raw_cost / er_calc
            else:
                raw_cost = 0; final_labor_unit_cost = 0
        except:
            raw_cost = 0; final_labor_unit_cost = 0
        st.metric("Local", f"{raw_cost:,.0f}")
    with col_l5:
        st.metric("Unit USD", f"${final_labor_unit_cost:,.2f}")

# --- RESULTADOS ---
total_service_cost = usd_unit_cost * sqty * slc_factor * duration_months
total_labor_cost = final_labor_unit_cost * lqty
total_grand = total_service_cost + total_labor_cost

st.markdown("---")
res_col1, res_col2, res_col3, res_col4 = st.columns([2, 2, 2, 2])
with res_col1:
    st.info(f"Servicios: **${total_service_cost:,.2f}**")
with res_col2:
    st.warning(f"Labor: **${total_labor_cost:,.2f}**")
with res_col3:
    st.error(f"TOTAL: **${total_grand:,.2f}**")
with res_col4:
    if st.button("Exportar"):
        st.toast("Archivo generado!")
