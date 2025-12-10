import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LACOST V20 Sheets", layout="wide")

# --- 1. CARGA DE DATOS ---
def load_data():
    # PAISES
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'ER': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
    }
    df_countries = pd.DataFrame(countries_data)

    # OFFERINGS (Solo lista simple para el dropdown)
    offerings_list = [
        "IBM Hardware Resell - Server/Storage",
        "1-HWMA MVS SPT other Prod",
        "IBM Support for Red Hat",
        "IBM Customized Support - HW",
        "IBM Customized Support - SW",
        "System Technical Support Service",
        "Relocation Services"
    ]

    # SLC
    slc_data = [
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response (M47)', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival (M19)', 'UPLF': 1.0},
        {'Scope': 'no brazil', 'Desc': '24X76Fix time (M2B)', 'UPLF': 1.6},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival (M19)', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24 (1.278)', 'UPLF': 1.278},
    ]
    df_slc = pd.DataFrame(slc_data)

    # LABOR
    labor_data = [
        {'Type': 'Machine Category', 'Item': 'System Z (Cat A)', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Ecuador': 991.20, 'Brazil': 2803.85},
        {'Type': 'Machine Category', 'Item': 'Power HE (Cat C)', 'Argentina': 194856.48, 'Colombia': 540008.96, 'Ecuador': 340.52, 'Brazil': 1516.61},
        {'Type': 'Brand Rate Full', 'Item': 'B7 (Senior)', 'Argentina': 40166.28, 'Colombia': 126000.0, 'Ecuador': 79.19, 'Brazil': 186.82}
    ]
    df_labor = pd.DataFrame(labor_data)
    
    return df_countries, offerings_list, df_slc, df_labor

df_countries, offerings_list, df_slc, df_labor = load_data()

# --- SIDEBAR: CONTEXTO GLOBAL ---
with st.sidebar:
    st.header("1. Configuración")
    
    selected_country = st.selectbox("País", df_countries['Country'])
    country_row = df_countries[df_countries['Country'] == selected_country].iloc[0]
    
    if selected_country == "Ecuador":
        er_calc = 1.0
        curr = "USD"
    else:
        er_calc = country_row['ER']
        curr = country_row['Currency']

    col1, col2 = st.columns(2)
    col1.metric("Moneda", curr)
    col2.metric("Tasa", f"{er_calc:,.2f}")
    
    st.divider()
    
    start_date = st.date_input("Inicio", date.today())
    end_date = st.date_input("Fin", date.today() + relativedelta(months=12))
    
    diff = relativedelta(end_date, start_date)
    duration_months = diff.years * 12 + diff.months + (1 if diff.days > 0 else 0)
    st.info(f"Duración: {duration_months} Meses")

# --- MAIN ---
st.title("📊 LACOST V20: Vista de Hoja de Cálculo")

# Filtros previos para configurar las tablas
scope_filter = "Brazil" if selected_country == "Brazil" else "no brazil"
filtered_slc = df_slc[df_slc['Scope'] == scope_filter]['Desc'].tolist()
filtered_items = df_labor['Item'].unique().tolist()

# TABS PARA ORGANIZACIÓN
tab_serv, tab_labor, tab_res = st.tabs(["📝 2. Servicios (Grid)", "👷 3. Labor (Grid)", "💰 4. Resultados Finales"])

# === TAB 1: SERVICIOS ===
with tab_serv:
    st.markdown("### Ingreso de Servicios")
    st.caption("Edita la tabla abajo. Agrega filas con el botón '+'.")
    
    # Estructura inicial de la "Hoja"
    if 'df_services_input' not in st.session_state:
        st.session_state.df_services_input = pd.DataFrame(
            [{"Offering": "IBM Customized Support - HW", "QA Risk": "Low (0.02)", "SLC Profile": filtered_slc[0], "USD Unit Cost": 10.0, "Qty": 1}]
        )

    # El Editor (La "Hoja de Cálculo")
    edited_services = st.data_editor(
        st.session_state.df_services_input,
        num_rows="dynamic",
        column_config={
            "Offering": st.column_config.SelectboxColumn("Offering", options=offerings_list, width="medium"),
            "QA Risk": st.column_config.SelectboxColumn("QA Risk", options=["Low (0.02)", "Medium (0.05)", "High (0.08)"], width="small"),
            "SLC Profile": st.column_config.SelectboxColumn("SLC", options=filtered_slc, width="medium"),
            "USD Unit Cost": st.column_config.NumberColumn("Costo Unit (USD)", format="$%.2f"),
            "Qty": st.column_config.NumberColumn("Cantidad", min_value=1, step=1)
        },
        use_container_width=True,
        hide_index=True
    )

# === TAB 2: LABOR ===
with tab_labor:
    st.markdown("### Ingreso de Recursos (Labor)")
    
    if 'df_labor_input' not in st.session_state:
        st.session_state.df_labor_input = pd.DataFrame(
            [{"Item": filtered_items[0], "Qty": 1}]
        )

    edited_labor = st.data_editor(
        st.session_state.df_labor_input,
        num_rows="dynamic",
        column_config={
            "Item": st.column_config.SelectboxColumn("Recurso / Rol", options=filtered_items, width="large"),
            "Qty": st.column_config.NumberColumn("Horas/Meses", min_value=1, step=1)
        },
        use_container_width=True,
        hide_index=True
    )

# === CÁLCULOS (LÓGICA PANDAS) ===

# 1. Calcular Servicios
# Mapear los valores de SLC y Risk al dataframe editado
# (Creamos copias para no romper la visual)
calc_serv = edited_services.copy()

# Funciones auxiliares para buscar valores
def get_slc_factor(desc):
    try:
        return df_slc[df_slc['Desc'] == desc]['UPLF'].values[0]
    except:
        return 1.0

# Aplicar calculos fila por fila
calc_serv['SLC Factor'] = calc_serv['SLC Profile'].apply(get_slc_factor)
calc_serv['Total Linea'] = calc_serv['USD Unit Cost'] * calc_serv['Qty'] * calc_serv['SLC Factor'] * duration_months

# 2. Calcular Labor
calc_labor = edited_labor.copy()

def get_labor_cost(item):
    try:
        # Busca costo en moneda local
        if selected_country in df_labor.columns:
            val = df_labor[df_labor['Item'] == item][selected_country].values[0]
            if pd.isna(val): return 0.0
            return val / er_calc # Convertir a USD
        return 0.0
    except:
        return 0.0

calc_labor['USD Unit Cost'] = calc_labor['Item'].apply(get_labor_cost)
calc_labor['Total Linea'] = calc_labor['USD Unit Cost'] * calc_labor['Qty']

# Totales Generales
total_servicios = calc_serv['Total Linea'].sum()
total_labor = calc_labor['Total Linea'].sum()
gran_total = total_servicios + total_labor

# === TAB 3: RESULTADOS ===
with tab_res:
    st.subheader("Resumen Financiero")
    
    # Métricas grandes
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Servicios", f"${total_servicios:,.2f}")
    c2.metric("Total Labor", f"${total_labor:,.2f}")
    c3.metric("GRAN TOTAL (USD)", f"${gran_total:,.2f}", delta="Proyecto Completo")
    
    st.divider()
    
    # Mostrar detalle calculado
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write("**Detalle Servicios (Calculado):**")
        st.dataframe(calc_serv[['Offering', 'SLC Factor', 'Total Linea']], hide_index=True)
    
    with col_d2:
        st.write("**Detalle Labor (Calculado):**")
        st.dataframe(calc_labor[['Item', 'USD Unit Cost', 'Total Linea']], hide_index=True)

    if st.button("📥 Descargar Cotización Completa"):
        st.toast("Generando Excel/JSON...")
