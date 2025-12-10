import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LACOST VERSION 20", layout="wide")
st.title("💸 LACOST VERSION 20 - Cotizador Cloud")

# --- 1. CARGA DE DATOS ---
def load_data():
    # Tabla PAISES (Datos del archivo Source 3)
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'ER': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
    }
    df_countries = pd.DataFrame(countries_data)

    # Tabla OFFERINGS (Datos del archivo Source 6)
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

    # Tabla SLC (Datos parciales del Source 3)
    slc_data = [
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response time (M47)', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'no brazil', 'Desc': '24X76Fix time (M2B)', 'UPLF': 1.6},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24 (1.278)', 'UPLF': 1.278},
    ]
    df_slc = pd.DataFrame(slc_data)

    # Tabla LABOR (Datos del Source 7/8) - CORREGIDA
    labor_data = [
        {'Type': 'Machine Category', 'Item': 'System Z (Cat A)', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Ecuador': 991.20, 'Brazil': 2803.85},
        {'Type': 'Machine Category', 'Item': 'Power HE (Cat C)', 'Argentina': 194856.48, 'Colombia': 540008.96, 'Ecuador': 340.52, 'Brazil': 1516.61},
        {'Type': 'Brand Rate Full', 'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Ecuador': 79.19, 'Brazil': 186.82}
    ]
    df_labor = pd.DataFrame(labor_data)
    
    return df_countries, df_offerings, df_slc, df_labor

df_countries, df_offerings, df_slc, df_labor = load_data()

# --- ESTILOS CSS PARA MEJORAR VISTA ---
st.markdown("""
<style>
    .stSelectbox div[data-baseweb="select"] > div {
        white-space: normal !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SECCIÓN 1: GENERAL INFO ---
st.header("1. General Info")
c1, c2, c3 = st.columns([1, 1, 2])

with c1:
    selected_country = st.selectbox("Country", df_countries['Country'])
    country_row = df_countries[df_countries['Country'] == selected_country].iloc[0]
    
    if selected_country == "Ecuador":
        er_calc = 1.0
        currency_display = "USD"
    else:
        er_calc = country_row['ER']
        currency_display = country_row['Currency']

with c2:
    st.metric("Currency", currency_display)
    st.metric("Exchange Rate (E/R)", f"{er_calc:,.2f}")

with c3:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Contract Start", date.today())
    with col_d2:
        end_date = st.date_input("Contract End", date.today() + relativedelta(months=12))
    
    diff = relativedelta(end_date, start_date)
    duration_months = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
    st.info(f"📅 **Period:** {duration_months} Months")

st.divider()

# --- SECCIÓN 2: INPUT COSTS - SERVICIOS ---
st.header("2. Input Costs - Services")

st.subheader("2.1. Configuración del Servicio")
col_s1, col_s2 = st.columns([2, 1])

with col_s1:
    offering = st.selectbox("Offering / Servicio (Nombres Completos)", df_offerings['Offering'])
    
with col_s2:
    qa_risk = st.selectbox("QA Risk Level", ["Low (0.02)", "Medium (0.05)", "High (0.08)"])

st.markdown("---")
st.subheader("2.2. Costos y Niveles de Servicio (SLC)")

col_s3, col_s4, col_s5 = st.columns([2, 1, 1])

with col_s3:
    scope_filter = "Brazil" if selected_country == "Brazil" else "no brazil"
    filtered_slc = df_slc[df_slc['Scope'] == scope_filter]
    
    slc_selection = st.selectbox("SLC Profile (Descripción Completa)", filtered_slc['Desc'])
    if not filtered_slc.empty:
        slc_factor = filtered_slc[filtered_slc['Desc'] == slc_selection]['UPLF'].values[0]
    else:
        slc_factor = 1.0
    st.caption(f"Factor Seleccionado: **{slc_factor}**")

with col_s4:
    usd_unit_cost = st.number_input("USD Unit Cost", value=10.0, format="%.2f")

with col_s5:
    sqty = st.number_input("Service Qty", min_value=1, value=1)

st.divider()

# --- SECCIÓN 3: INPUT COSTS - LABOR ---
st.header("3. Input Costs - Labor RR/BR")

st.subheader("3.1. Selección de Recurso")
col_l1, col_l2 = st.columns([1, 2])

with col_l1:
    labor_type = st.radio("Tipo de Tarifa", df_labor['Type'].unique(), horizontal=True)

with col_l2:
    items_avail = df_labor[df_labor['Type'] == labor_type]['Item'].unique()
    labor_item = st.selectbox("Categoría / Item (Detalle Completo)", items_avail)

st.markdown("---")
st.subheader("3.2. Cantidad y Costo Calculado")

col_l3, col_l4, col_l5 = st.columns(3)

with col_l3:
    lqty = st.number_input("Labor Quantity (Horas/Meses)", min_value=1, value=1)

with col_l4:
    try:
        if selected_country in df_labor.columns:
            raw_cost = df_labor[(df_labor['Type'] == labor_type) & (df_labor['Item'] == labor_item)][selected_country].values[0]
            if pd.isna(raw_cost): raw_cost = 0
            final_labor_unit_cost = raw_cost / er_calc
        else:
            raw_cost = 0
            final_labor_unit_cost = 0
            st.warning(f"No hay tarifa para {selected_country}")
    except:
        raw_cost = 0
        final_labor_unit_cost = 0

    st.metric("Costo Local (Ref)", f"{raw_cost:,.0f} {currency_display}")

with col_l5:
    st.metric("Costo Unitario (USD)", f"${final_labor_unit_cost:,.2f}")

st.divider()

# --- SECCIÓN 4: RESULTADOS ---
st.header("4. Resumen de Cotización")

total_service_cost = usd_unit_cost * sqty * slc_factor * duration_months
total_labor_cost = final_labor_unit_cost * lqty
total_grand = total_service_cost + total_labor_cost

res_col1, res_col2, res_col3 = st.columns(3)

with res_col1:
    st.success(f"Total Servicios\n# ${total_service_cost:,.2f}")
    st.caption("Fórmula: Unit Cost * Qty * SLC * Meses")

with res_col2:
    st.warning(f"Total Labor\n# ${total_labor_cost:,.2f}")
    st.caption("Fórmula: (Costo Local / ER) * Qty")

with res_col3:
    st.error(f"GRAN TOTAL (USD)\n# ${total_grand:,.2f}")

if st.button("Generar Archivo JSON para Conga"):
    st.balloons()
    st.write("Datos procesados listos para exportar...")
