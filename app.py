import streamlit as st
import pandas as pd

# --- Configuración de la Página ---
st.set_page_config(page_title="Cotizador V11 - IBM (Standalone)", layout="wide")
st.title("🛡️ Cotizador de Servicios - Lógica V11")

# ==========================================
# 1. BASE DE DATOS INTEGRADA (Hardcoded)
# ==========================================

# Datos de Países y TRM (Fuente: Countries.csv)
DATA_COUNTRIES = {
    "Colombia":  {"Currency": "COP", "ER": 3775.22},
    "Ecuador":   {"Currency": "USD", "ER": 1.0},
    "Peru":      {"Currency": "PEN", "ER": 3.37},
    "Mexico":    {"Currency": "MXN", "ER": 18.42},
    "Brazil":    {"Currency": "BRL", "ER": 5.34},
    "Chile":     {"Currency": "CLP", "ER": 934.70},
    "Argentina": {"Currency": "ARS", "ER": 1428.95},
    "Uruguay":   {"Currency": "UYU", "ER": 39.73},
    "Venezuela": {"Currency": "VES", "ER": 235.28}
}

# Datos de Riesgo (Fuente: Risk.csv)
DATA_RISK = {
    "Low": 0.02,
    "Medium": 0.05,
    "High": 0.08
}

# Datos de SLC (Fuente: SLC.csv - Muestra representativa)
DATA_SLC = {
    "M1A": 1.0, "M16": 1.0, "M19": 1.0, 
    "M5B": 1.05, "MJ7": 1.1, "M3F": 1.15, 
    "M3B": 1.2, "M33": 1.3, "M2F": 1.4, 
    "M2B": 1.6, "M23": 1.7, "M47": 1.5
}

# Datos de Mano de Obra (Fuente: Labor.csv - Muestra extraída del snippet)
# Estructura: Tipo -> Plataforma -> Costo Local por País
DATA_LABOR = {
    "Machine Category": {
        "System Z":   {"Colombia": 2054058, "Ecuador": 991.21, "Mexico": 12857, "Brazil": 2803.85, "Peru": 1284.60, "Chile": 2165270, "Argentina": 304504},
        "Power HE":   {"Colombia": 540009,  "Ecuador": 340.52, "Mexico": 5857,  "Brazil": 1516.61, "Peru": 505.85,  "Chile": 486361,  "Argentina": 194856},
        "Power LE":   {"Colombia": 379582,  "Ecuador": 283.77, "Mexico": 4500,  "Brazil": 742.22,  "Peru": 312.87,  "Chile": 486361,  "Argentina": 162675},
        "Storage HE": {"Colombia": 450000,  "Ecuador": 300.00, "Mexico": 5000,  "Brazil": 1403.43}, # Valores estimados donde no había data en snippet
        "Storage LE": {"Colombia": 300000,  "Ecuador": 200.00, "Mexico": 3000,  "Brazil": 536.45}
    },
    "Brand Rate Full": {
        "FULL":       {"Colombia": 15000000, "Ecuador": 4000, "Mexico": 80000, "Brazil": 15247} # Ejemplo genérico
    }
}

# ==========================================
# 2. INTERFAZ Y LÓGICA
# ==========================================

# --- Sidebar: Configuración General ---
with st.sidebar:
    st.header("1. Configuración del Contrato")
    
    # País
    paises_list = list(DATA_COUNTRIES.keys())
    pais_sel = st.selectbox("País", paises_list, index=paises_list.index("Colombia"))
    
    # Datos automáticos del país
    info_pais = DATA_COUNTRIES[pais_sel]
    er_pais = info_pais["ER"]
    moneda_pais = info_pais["Currency"]
    
    st.info(f"🏳️ **{pais_sel}** | Moneda: {moneda_pais} | TRM: {er_pais:,.2f}")

    # Fechas
    fecha_inicio = st.date_input("Inicio Contrato")
    fecha_fin = st.date_input("Fin Contrato")
    
    # Cálculo duración contrato (meses)
    meses_contrato = (fecha_fin.year - fecha_inicio.year) * 12 + (fecha_fin.month - fecha_inicio.month)
    meses_contrato = max(1, meses_contrato) # Mínimo 1 mes
    st.write(f"⏱️ Duración: **{meses_contrato} meses**")

    # Riesgo y Cliente
    riesgo_sel = st.selectbox("QA Risk", list(DATA_RISK.keys()))
    pct_riesgo = DATA_RISK[riesgo_sel]
    
    cliente = st.text_input("Cliente", "Cliente Prueba")

# --- Cuerpo Principal ---
tab_servicios, tab_labor, tab_resumen = st.tabs(["🧩 Servicios (Offering)", "👷 Mano de Obra (Labor)", "📊 Resumen"])

# ------------------------------------------
# TAB 1: SERVICIOS
# ------------------------------------------
with tab_servicios:
    st.subheader("Cálculo de Servicios")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        offering_name = st.selectbox("Offering", ["IBM Hardware Resell", "IBM Support for Red Hat", "Customized Support", "HWMA MVS SPT"])
        slc_sel = st.selectbox("Nivel de Servicio (SLC)", list(DATA_SLC.keys()), index=2) # Default M19
        uplf = DATA_SLC[slc_sel]
        st.metric("Factor SLC (UPLF)", uplf)
        
    with c2:
        usd_unit_cost = st.number_input("Costo Unitario (USD)", value=10.0, min_value=0.0)
        sqty = st.number_input("Cantidad (SQty)", value=1, min_value=1)
        
    with c3:
        duracion_srv = st.number_input("Duración Servicio (Meses)", value=meses_contrato, min_value=1)

    # FÓRMULA SERVICIOS: Unit * Qty * UPLF * Duration
    costo_total_servicios = usd_unit_cost * sqty * uplf * duracion_srv
    st.success(f"💰 Total Servicios: **USD {costo_total_servicios:,.2f}**")

# ------------------------------------------
# TAB 2: MANO DE OBRA (LABOR)
# ------------------------------------------
with tab_labor:
    st.subheader("Cálculo de Mano de Obra")
    l1, l2, l3 = st.columns(3)
    
    with l1:
        tipo_labor = st.selectbox("Tipo (MC/RR)", list(DATA_LABOR.keys()))
        plataformas = list(DATA_LABOR[tipo_labor].keys())
        plat_sel = st.selectbox("Plataforma / Categoría", plataformas)
        
    with l2:
        # LÓGICA V11 BASE: Buscar costo local y dividir por ER
        costos_plataforma = DATA_LABOR[tipo_labor][plat_sel]
        
        # Verificar si existe costo para el país seleccionado
        costo_base_local = costos_plataforma.get(pais_sel, 0.0)
        
        if costo_base_local > 0:
            costo_labor_usd = costo_base_local / er_pais
            st.metric(f"Costo Base ({moneda_pais})", f"{costo_base_local:,.2f}")
            st.metric("Costo Calculado (USD)", f"{costo_labor_usd:,.2f}", help=f"Costo Local / TRM {er_pais}")
        else:
            st.error(f"No hay tarifa definida para {plat_sel} en {pais_sel}.")
            costo_labor_usd = 0.0

    with l3:
        lqty = st.number_input("Cantidad Recursos (LQty)", value=1, min_value=1)
        duracion_lab = st.number_input("Duración Labor (Meses)", value=meses_contrato, min_value=1)

    # FÓRMULA LABOR: Costo_USD * Qty * Duration
    costo_total_labor = costo_labor_usd * lqty * duracion_lab
    st.success(f"👷 Total Labor: **USD {costo_total_labor:,.2f}**")

# ------------------------------------------
# TAB 3: RESUMEN FINAL
# ------------------------------------------
with tab_resumen:
    st.header(f"Resumen de Cotización: {cliente}")
    
    total_costo = costo_total_servicios + costo_total_labor
    # El riesgo en V11 (según test case) parece ser informativo o una provisión aparte, 
    # aquí lo calculamos pero mostramos el Total Costo estricto primero.
    reserva_riesgo = total_costo * pct_riesgo
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.write("### Desglose")
        st.write(f"**(+) Servicios:** USD {costo_total_servicios:,.2f}")
        st.write(f"**(+) Mano de Obra:** USD {costo_total_labor:,.2f}")
        st.markdown("---")
        st.write(f"**(=) COSTO TOTAL:** USD {total_costo:,.2f}")
    
    with col_r2:
        st.write("### Indicadores")
        st.metric("Riesgo QA Aplicado", f"{pct_riesgo:.1%}")
        st.metric("Reserva de Riesgo (Provisión)", f"USD {reserva_riesgo:,.2f}")
        
    # Botón de exportación simple (CSV del resultado)
    st.markdown("---")
    resumen_dict = {
        "Cliente": [cliente],
        "País": [pais_sel],
        "TRM Usada": [er_pais],
        "Total Servicios": [costo_total_servicios],
        "Total Labor": [costo_total_labor],
        "Costo Total": [total_costo],
        "Riesgo": [reserva_riesgo]
    }
    df_resumen = pd.DataFrame(resumen_dict)
    csv = df_resumen.to_csv(index=False).encode('utf-8')
    
    st.download_button(
        "📥 Descargar Resumen CSV",
        csv,
        "resumen_cotizacion.csv",
        "text/csv",
        key='download-csv'
    )
