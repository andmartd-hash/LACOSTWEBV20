import streamlit as st

# --- Configuración ---
st.set_page_config(page_title="Cotizador v11Base", layout="wide")
st.title("Cotizador de Servicios (Lógica v11)")

# --- Lógica de Negocio del v11 ---
def calcular_logica_v11(pais, moneda, costo, trm):
    # Regla 1: Si es Ecuador, NO aplica conversión (Excepción).
    if pais == "Ecuador":
        return costo
    # Regla 2: Si es USD, se divide por la TRM.
    elif moneda == "USD":
        if trm > 0:
            return costo / trm
        else:
            return 0
    # Regla 3: Si es Local, el valor pasa igual.
    else:
        return costo

# --- Formulario (Igual a tu imagen) ---
col1, col2 = st.columns(2)

with col1:
    fecha_inicio = st.date_input("Fecha Inicio")
    # Lista de países basada en tu negocio
    pais = st.selectbox("País", ["Colombia", "Ecuador", "Perú", "México", "Chile", "Argentina"])

with col2:
    fecha_fin = st.date_input("Fecha Fin")
    moneda = st.radio("Moneda de la Cotización", ["Local", "USD"], horizontal=True)

col3, col4 = st.columns(2)
with col3:
    costo_input = st.number_input("Costo (Valor)", min_value=0.0, format="%.2f")
with col4:
    trm_input = st.number_input("Tasa de Cambio (ER/TRM)", value=1.0, min_value=0.0001, format="%.2f")

# --- Botón y Resultado ---
if st.button("Calcular Cotización", type="primary"):
    resultado = calcular_logica_v11(pais, moneda, costo_input, trm_input)
    
    st.divider()
    
    # Mostrar explicación visual de qué regla v11 se usó
    if pais == "Ecuador":
        st.warning(f"⚠️ Regla v11 aplicada: País es {pais} (Excepción). No se aplicó tasa de cambio.")
    elif moneda == "USD":
        st.info(f"ℹ️ Regla v11 aplicada: Moneda USD. Se dividió por TRM {trm_input}.")
    else:
        st.success("✅ Regla v11 aplicada: Moneda Local. Valor pasa directo.")

    # Resultado Final
    st.metric(label="Costo Final Calculado", value=f"{resultado:,.2f}")
