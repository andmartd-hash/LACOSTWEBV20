import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cotizador IBM", layout="centered")

# --- FUNCIONES ---

def calcular_meses_excel(start_date, end_date):
    """
    Replica la fórmula de Excel:
    IF(K14<J14,"Not Valid",ROUND((DATEDIF(J14,K14,"m")+(DATEDIF(J14,K14,"md")+(IF(MONTH(K14)=2,3,1)))/30),1))
    """
    # Validación IF(K14<J14...)
    if end_date < start_date:
        return "Not Valid"
    
    # DATEDIF(..., "m") y "md"
    diff = relativedelta(end_date, start_date)
    meses_completos = (diff.years * 12) + diff.months
    dias_restantes = diff.days
    
    # Ajuste IF(MONTH(K14)=2, 3, 1) -> Si el mes final es Febrero suma 3, sino 1
    ajuste = 3 if end_date.month == 2 else 1
    
    # Cálculo Final: Meses + (Días + Ajuste)/30
    duracion = meses_completos + ((dias_restantes + ajuste) / 30)
    
    return round(duracion, 1)

# --- INTERFAZ DE USUARIO (FRONTEND) ---

st.title("📊 Cotizador de Servicios")
st.markdown("---")

# 1. Sección de Datos
col1, col2 = st.columns(2)

with col1:
    fecha_inicio = st.date_input("Fecha Inicio", value=date.today())
    pais = st.selectbox("País", ["Colombia", "Ecuador", "Peru", "Mexico", "Chile", "Otro"])

with col2:
    fecha_fin = st.date_input("Fecha Fin", value=date.today())
    moneda = st.radio("Moneda de la Cotización", ["Local", "USD"], horizontal=True)

col3, col4 = st.columns(2)
with col3:
    costo_input = st.number_input("Costo (Valor)", min_value=0.0, format="%.2f")
with col4:
    er_input = st.number_input("Tasa de Cambio (ER/TRM)", min_value=1.0, value=1.0, format="%.2f")

# --- LÓGICA DE NEGOCIO (BACKEND) ---

if st.button("Calcular Cotización", type="primary"):
    
    # 1. Calcular Duración con la nueva fórmula
    resultado_duracion = calcular_meses_excel(fecha_inicio, fecha_fin)
    
    if resultado_duracion == "Not Valid":
        st.error("⚠️ Error: La fecha final no puede ser menor a la fecha de inicio.")
    else:
        # 2. Lógica de Costos (Según tus reglas anteriores)
        costo_procesado = costo_input
        
        # Regla: Si está en USD, dividir por ER, EXCEPTO si es Ecuador
        if moneda == "USD":
            if pais.lower() == "ecuador":
                costo_procesado = costo_input # Ecuador usa USD, se deja igual
            else:
                costo_procesado = costo_input / er_input # Tu regla de división
        
        # Costo Total (Asumiendo que el costo ingresado es mensual, multiplicamos por la duración)
        # Si el costo input fuera total, habría que ajustar esta línea.
        total_estimado = costo_procesado * resultado_duracion

        # --- MOSTRAR RESULTADOS ---
        st.success("Cálculo realizado exitosamente")
        
        st.subheader("Resultados")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric("Duración (Meses)", value=f"{resultado_duracion}")
            st.caption("Cálculo basado en lógica Excel")
            
        with c2:
            st.metric("Costo Base Ajustado", value=f"{costo_procesado:,.2f}")
            st.caption(f"Moneda base tras reglas ({pais})")
            
        with c3:
            st.metric("Total Estimado", value=f"{total_estimado:,.2f}")
