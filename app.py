import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LACOST VERSION 20", layout="wide")
st.title("💸 LACOST VERSION 20 - Cotizador Cloud")

# --- 1. CARGA DE DATOS (Simulando tus CSVs para estabilidad) ---
def load_data():
    # Tabla PAISES
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'ER': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
        'Tax': [0.0529, 0.1425, 0.0, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0155]
    }
    df_countries = pd.DataFrame(countries_data)

    # Tabla SLC (Simplificada con lógica Scope)
    # Nota: Mapeo parcial basado en tu archivo para el ejemplo
    slc_data = [
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response time', 'Code': 'M47', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival time', 'Code': 'M19', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival time', 'Code': 'M19', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'Code': 'NStd5x9', 'UPLF': 1.0},
        # ... se pueden añadir más filas aquí
    ]
    df_slc = pd.DataFrame(slc_data)

    # Tabla LABOR (Precios brutos)
    # Columnas son los países. Filas son los productos.
    labor_data = [
        {'Type': 'Machine Category', 'Item': 'System Z', 'Argentina': 304504.2, 'Chile': 2165270.4, 'Colombia': 2054058.99, 'Ecuador': 991.20, 'Peru': 1284.60, 'Uruguay': 30167.39, 'Venezuela': 102721.98, 'Mexico': 12857.25, 'Brazil': 2803.85},
        {'Type': 'Brand Rate Full', 'Item': 'B7', 'Argentina': 40166.28, 'Chile': 54081.72, 'Colombia': 126000.0, 'Ecuador': 79.19, 'Peru': 216.45, 'Uruguay': 3581.26, 'Venezuela': 20998.96, 'Mexico': 673.05, 'Brazil': 186.82},
        # Añadir más items según necesidad
    ]
    df_labor = pd.DataFrame(labor_data)
    
    return df_countries, df_slc, df_labor

df_countries, df_slc, df_labor = load_data()

# --- 2. INTERFAZ DE USUARIO ---

# --- SECCIÓN 1: GENERAL INFO ---
st.header("1. General Info")
col1, col2, col3 = st.columns(3)

with col1:
    selected_country = st.selectbox("Country", df_countries['Country'])
    # Obtener datos del país seleccionado
    country_row = df_countries[df_countries['Country'] == selected_country].iloc[0]
    er_val = country_row['ER']
    currency_val = country_row['Currency']
    
    # Lógica de excepción Ecuador
    if selected_country == "Ecuador":
        er_calc = 1.0
    else:
        er_calc = er_val

with col2:
    st.info(f"Currency: {currency_val}")
    st.metric("Exchange Rate (E/R)", f"{er_val:,.2f}")

with col3:
    start_date = st.date_input("Contract Start Date", date.today())
    end_date = st.date_input("Contract End Date", date.today() + relativedelta(months=12))

# Cálculo automático de duración
diff = relativedelta(end_date, start_date)
duration_months = diff.years * 12 + diff.months
st.success(f"Contract Period: {duration_months} Months")


st.divider()

# --- SECCIÓN 2: INPUT COSTS (SERVICIOS) ---
st.header("2. Input Costs - Services")
col_s1, col_s2, col_s3 = st.columns(3)

with col_s1:
    qa_risk = st.selectbox("QA Risk", ["Low (2%)", "Medium (5%)", "High (8%)"])
    offering = st.text_input("Offering / L40", "IBM Customized Support")
    
with col_s2:
    # Filtro SLC por Scope (Brazil vs No Brazil)
    scope_filter = "Brazil" if selected_country == "Brazil" else "no brazil"
    filtered_slc = df_slc[df_slc['Scope'] == scope_filter]
    
    if not filtered_slc.empty:
        slc_selection = st.selectbox("SLC Profile", filtered_slc['Desc'])
        slc_factor = filtered_slc[filtered_slc['Desc'] == slc_selection]['UPLF'].values[0]
    else:
        st.warning("No SLC found for scope")
        slc_factor = 1.0
    st.caption(f"SLC Factor: {slc_factor}")

with col_s3:
    usd_unit_cost = st.number_input("USD Unit Cost", min_value=0.0, value=10.0)
    sqty = st.number_input("Service Qty", min_value=1, value=1)

# --- SECCIÓN 3: INPUT COSTS (LABOR) ---
st.header("3. Input Costs - Labor RR/BR")
col_l1, col_l2, col_l3 = st.columns(3)

with col_l1:
    labor_type = st.selectbox("RR/BR Type", df_labor['Type'].unique())
    
with col_l2:
    # Filtrar items por tipo
    items_avail = df_labor[df_labor['Type'] == labor_type]['Item'].unique()
    labor_item = st.selectbox("Item / Category", items_avail)

with col_l3:
    lqty = st.number_input("Labor Qty", min_value=1, value=1)

# Lógica de costo laboral: Buscar valor en columna del país y dividir por E/R
try:
    if selected_country in df_labor.columns:
        raw_labor_cost = df_labor[(df_labor['Type'] == labor_type) & (df_labor['Item'] == labor_item)][selected_country].values[0]
        # REGLA DE NEGOCIO: Costo / ER (Excepto si E/R es 1 o es Ecuador, que ya se manejó en er_calc)
        final_labor_unit_cost = raw_labor_cost / er_calc
    else:
        raw_labor_cost = 0
        final_labor_unit_cost = 0
        st.error(f"No labor data for {selected_country}")
except Exception as e:
    final_labor_unit_cost = 0
    st.error(f"Error calculating labor: {e}")

st.info(f"Labor Unit Cost (Calc): ${final_labor_unit_cost:,.2f} USD")

st.divider()

# --- SECCIÓN 4: RESULTADOS ---
st.header("4. Total Costs Estimation")

# Cálculos Finales
# Total Service Cost = USDunit cost * sqty * SLCuplf * duracion
total_service_cost = usd_unit_cost * sqty * slc_factor * duration_months

# Total Labor Cost = (Calculated Unit Cost) * lqty
total_labor_cost = final_labor_unit_cost * lqty

# Total Cost
total_cost_project = total_service_cost + total_labor_cost

# Display
c1, c2, c3 = st.columns(3)
c1.metric("Total Service Cost", f"${total_service_cost:,.2f}")
c2.metric("Total Labor Cost", f"${total_labor_cost:,.2f}")
c3.metric("GRAND TOTAL", f"${total_cost_project:,.2f}", delta="USD")

# Botón para descargar resumen (Opcional)
resumen = {
    "Country": selected_country,
    "Duration": duration_months,
    "Total Service": total_service_cost,
    "Total Labor": total_labor_cost,
    "Grand Total": total_cost_project
}
st.download_button("Download Summary", data=str(resumen), file_name="lacost_v20_summary.txt")