import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LACOST V20 Pro", layout="wide")

# --- 1. CARGA DE DATOS ---
def load_data():
    # PAISES
    countries_data = {
        'Country': ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico', 'Uruguay', 'Venezuela'],
        'Currency': ['ARS', 'BRL', 'CLP', 'COP', 'USD', 'PEN', 'MXN', 'UYU', 'VES'],
        'ER': [1428.95, 5.34, 934.70, 3775.22, 1.0, 3.37, 18.42, 39.73, 235.28],
    }
    df_countries = pd.DataFrame(countries_data)

    # OFFERINGS
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

# --- FUNCIONES DE CÁLCULO ---
def get_slc_factor(desc):
    try:
        return df_slc[df_slc['Desc'] == desc]['UPLF'].values[0]
    except:
        return 1.0

# --- SIDEBAR ---
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
st.title("📊 LACOST V20")

# Pre-filtros
scope_filter = "Brazil" if selected_country == "Brazil" else "no brazil"
filtered_slc = df_slc[df_slc['Scope'] == scope_filter]['Desc'].tolist()
filtered_items = df_labor['Item'].unique().tolist()

tab_serv, tab_labor, tab_res = st.tabs(["📝 2. Servicios", "👷 3. Labor", "💰 4. Resumen Final"])

# ==========================================
# TAB 1: SERVICIOS
# ==========================================
with tab_serv:
    st.markdown("### Tabla de Servicios")
    
    if 'df_services_input' not in st.session_state:
        st.session_state.df_services_input = pd.DataFrame(
            [{"Offering": "IBM Customized Support - HW", "QA Risk": "Low (0.02)", "SLC Profile": filtered_slc[0], "USD Unit Cost": 10.0, "Qty": 1}]
        )

    # Configuración de columnas (formateada verticalmente para evitar errores)
    column_cfg_serv = {
        "Offering": st.column_config.SelectboxColumn(
            "Offering",
            options=offerings_list,
            width="medium"
        ),
        "QA Risk": st.column_config.SelectboxColumn(
            "QA Risk",
            options=["Low (0.02)", "Medium (0.05)", "High (0.08)"],
            width="small"
        ),
        "SLC Profile": st.column_config.SelectboxColumn(
            "SLC",
            options=filtered_slc,
            width="medium"
        ),
        "USD Unit Cost": st.column_config.NumberColumn(
            "Costo Unit (USD)",
            format="$%.2f"
        ),
        "Qty": st.column_config.NumberColumn(
            "Cant",
            min_value=1
        )
    }

    edited_services = st.data_editor(
        st.session_state.df_services_input,
        num_rows="dynamic",
        column_config=column_cfg_serv,
        use_container_width=True,
        hide_index=True,
        key="editor_servicios"
    )
    
    # --- CÁLCULO SERVICIOS ---
    calc_serv = edited_services.copy()
    calc_serv['SLC Factor'] = calc_serv['SLC Profile'].apply(get_slc_factor)
    calc_serv['Total Linea'] = calc_serv['USD Unit Cost'] * calc_serv['Qty'] * calc_serv['SLC Factor'] * duration_months
    total_servicios = calc_serv['Total Linea'].sum()
    
    st.divider()
    cols_s1, cols_s2 = st.columns([3, 1])
    with cols_s2:
        st.metric("TOTAL SERVICIOS (USD)", f"${total_servicios:,.2f}")

# ==========================================
# TAB 2: LABOR
# ==========================================
with tab_labor:
    st.markdown("### Tabla de Recursos")
    
    if 'df_labor_input' not in st.session_state:
        st.session_state.df_labor_input = pd.DataFrame(
            [{"Item": filtered_items[0], "Qty": 1}]
        )

    column_cfg_labor = {
        "Item": st.column_config.SelectboxColumn(
            "Recurso / Rol",
            options=filtered_items,
            width="large"
        ),
        "Qty": st.column_config.NumberColumn(
            "Horas/Meses",
            min_value=1
        )
    }

    edited_labor = st.data_editor(
        st.session_state.df_labor_input,
        num_rows="dynamic",
        column_config=column_cfg_labor,
        use_container_width=True,
        hide_index=True,
        key="editor_labor"
    )

    # --- CÁLCULO LABOR ---
    calc_labor = edited_labor.copy()
    
    def get_labor_cost(item):
        try:
            if selected_country in df_labor.columns:
                val = df_labor[df_labor['Item'] == item][selected_country].values[0]
                if pd.isna(val): return 0.0
                return val / er_calc 
            return 0.0
        except:
            return 0.0

    calc_labor['USD Unit Cost'] = calc_labor['Item'].apply(get_labor_cost)
    calc_labor['Total Linea'] = calc_labor['USD Unit Cost'] * calc_labor['Qty']
    total_labor = calc_labor['Total Linea'].sum()

    st.divider()
    coll_l1, coll_l2 = st.columns([3, 1])
    with coll_l2:
        st.metric("TOTAL LABOR (USD)", f"${total_labor:,.2f}")

# ==========================================
# TAB 3: RESUMEN FINAL
# ==========================================
with tab_res:
    gran_total = total_servicios + total_labor
    
    st.subheader("Resumen Ejecutivo")
    
    c1, c2, c3 = st.columns(3)
    c1.info(f"Servicios: ${total_servicios:,.2f}")
    c2.warning(f"Labor: ${total_labor:,.2f}")
    c3.success(f"GRAN TOTAL: ${gran_total:,.2f}")
    
    st.divider()
    if st.button("💾 Guardar Proyecto"):
        st.balloons()

