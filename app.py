import streamlit as st
import pandas as pd
from datetime import date
import math

# --- Configuración de la Página ---
st.set_page_config(page_title="Cotizador V11 - IBM", layout="wide")
st.title("🛡️ Cotizador de Servicios - Lógica V11 Base")

# --- Carga de Datos (Data-Driven) ---
# Usamos caché para no recargar los CSV cada vez que cambias un dato
@st.cache_data
def load_data():
    try:
        # Ajusta los nombres de archivo si es necesario
        countries = pd.read_csv("Countries.csv")
        risk = pd.read_csv("Risk.csv")
        offering = pd.read_csv("Offering.csv")
        labor = pd.read_csv("Labor.csv")
        slc = pd.read_csv("SLC.csv")
        return countries, risk, offering, labor, slc
    except FileNotFoundError as e:
        st.error(f"❌ Error: No encuentro el archivo {e.filename}. Asegúrate de que los CSV estén en la carpeta.")
        return None, None, None, None, None

df_countries, df_risk, df_offering, df_labor, df_slc = load_data()

if df_countries is not None:
    # --- 1. BARRA LATERAL: CONFIGURACIÓN (UI_CONFIG Section 1) ---
    with st.sidebar:
        st.header("1. Configuración")
        
        # Selección de País
        lista_paises = df_countries['Country'].dropna().unique().tolist()
        pais_sel = st.selectbox("País (Country)", lista_paises, index=lista_paises.index("Colombia") if "Colombia" in lista_paises else 0)
        
        # Obtener datos del país (TRM, Moneda)
        datos_pais = df_countries[df_countries['Country'] == pais_sel].iloc[0]
        currency = datos_pais['Currency']
        er = datos_pais['ER']
        
        st.info(f"💱 Moneda: **{currency}** | TRM (ER): **{er:,.2f}**")

        # Fechas y Duración
        start_date = st.date_input("Fecha Inicio Contrato", date.today())
        end_date = st.date_input("Fecha Fin Contrato", date.today().replace(year=date.today().year + 1))
        
        # Cálculo de meses (Contract Period)
        months_contract = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
        if end_date.day < start_date.day:
            months_contract -= 1
        months_contract = max(0, months_contract) # Evitar negativos
        
        st.write(f"📅 Periodo del Contrato: **{months_contract} meses**")

        # Riesgo
        lista_riesgos = df_risk['Level'].dropna().unique().tolist()
        risk_sel = st.selectbox("QA Risk", lista_riesgos)
        risk_pct = df_risk[df_risk['Level'] == risk_sel]['Percentage'].values[0]

        # Cliente
        client_name = st.text_input("Nombre Cliente", "Cliente Ejemplo")
        client_num = st.text_input("Número Cliente", "00000")

    # --- PESTAÑAS PRINCIPALES ---
    tab1, tab2, tab3 = st.tabs(["2. Servicios (Offering)", "3. Mano de Obra (Labor)", "📊 Resumen Total"])

    # --- TAB 1: SERVICIOS (Offering) ---
    with tab1:
        st.subheader("Configuración de Servicios")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Offering Dropdown
            offering_list = df_offering['Offering'].dropna().unique().tolist()
            offering_sel = st.selectbox("Offering", offering_list)
            
            # Auto-fill fields based on Offering
            offering_data = df_offering[df_offering['Offering'] == offering_sel].iloc[0]
            l40_code = offering_data['L40']
            go_to_conga = offering_data['Go To Conga'] if 'Go To Conga' in offering_data else "N/A"
            
            st.caption(f"📌 L40: {l40_code}")
            st.caption(f"⚙️ Go To Conga: {go_to_conga}")

        with col2:
            # SLC (Service Level Code)
            # Filtramos por país si aplica "only Brazil" o Scope vacío/Global
            # Lógica simplificada: Mostrar todos los códigos únicos de SLC
            slc_list = df_slc['SLC'].unique().tolist()
            slc_sel = st.selectbox("SLC (Nivel de Servicio)", slc_list)
            
            # Buscar el UPLF (Factor)
            # Prioridad: Buscar fila con Scope="only Brazil" si el país es Brasil, sino Scope vacío/ALL
            # Como simplificación, tomamos el valor del SLC seleccionado.
            try:
                slc_row = df_slc[df_slc['SLC'] == slc_sel].iloc[0]
                uplf = slc_row['UPLF'] if 'UPLF' in slc_row else 1.0
            except:
                uplf = 1.0
            st.metric("Factor SLC (UPLF)", uplf)

        with col3:
            usd_unit_cost = st.number_input("Costo Unitario (USD Unit Cost)", min_value=0.0, value=10.0)
            sqty = st.number_input("Cantidad (SQty)", min_value=1, value=1)
            duration_srv = st.number_input("Duración Servicio (Meses)", min_value=1, value=months_contract)

        # --- CÁLCULO SERVICIO (Logic Rule 1) ---
        # Total Service Cost = USDunit cost * sqty * SLCuplf * duration1
        total_service_cost = usd_unit_cost * sqty * uplf * duration_srv
        st.success(f"💰 Costo Total Servicios: **USD {total_service_cost:,.2f}**")

    # --- TAB 2: LABOR (Mano de Obra) ---
    with tab2:
        st.subheader("Cálculo de Mano de Obra")
        
        lc1, lc2, lc3 = st.columns(3)
        
        with lc1:
            # Selector Tipo (Machine Category vs Brand Rate) - Columna MC/RR
            tipos_labor = df_labor['MC/RR'].unique().tolist()
            tipo_labor_sel = st.selectbox("Tipo (RR/BR)", tipos_labor)
            
            # Selector Sub-Tipo (Plataforma) - Columna Plat
            # Filtramos DF Labor por el tipo seleccionado
            labor_filtered = df_labor[df_labor['MC/RR'] == tipo_labor_sel]
            plataformas = labor_filtered['Plat'].unique().tolist()
            plat_sel = st.selectbox("Categoría / Plataforma", plataformas)

        with lc2:
            # --- LÓGICA CRÍTICA V11 ---
            # Buscar el valor en la columna del PAÍS seleccionado
            try:
                # Fila específica
                row_labor = labor_filtered[labor_filtered['Plat'] == plat_sel].iloc[0]
                
                # Verificar si la columna del país existe en Labor.csv (ej: 'Colombia', 'Ecuador')
                if pais_sel in row_labor:
                    raw_cost = row_labor[pais_sel]
                    
                    # APLICAR FÓRMULA: Costo Base / ER
                    # Si el costo es NaN o 0, manejarlo
                    if pd.isna(raw_cost):
                        raw_cost = 0.0
                    
                    rr_br_cost_usd = raw_cost / er
                    
                    st.metric(f"Costo Base Local ({pais_sel})", f"{raw_cost:,.2f}")
                    st.metric("Costo Calculado (USD)", f"{rr_br_cost_usd:,.2f}", help=f"Fórmula V11: {raw_cost:,.2f} / {er:,.2f}")
                else:
                    st.error(f"No hay tarifa definida para {pais_sel} en esta categoría.")
                    rr_br_cost_usd = 0.0
            except Exception as e:
                st.error(f"Error calculando costo labor: {e}")
                rr_br_cost_usd = 0.0

        with lc3:
            monthly_hours = st.number_input("Horas Mensuales", min_value=0.0, value=1.0)
            lqty = st.number_input("Cantidad Recursos (LQty)", min_value=1, value=1)
            duration_lab = st.number_input("Duración Labor (Meses)", min_value=1, value=months_contract)

        # --- CÁLCULO LABOR (Logic Rule 2) ---
        # Total Labor Cost = (Rate_USD * lqty * duration)
        # Nota: La fórmula en logic_rules dice: (Machine Category/(ER)*lqty*duration)
        # Nosotros ya calculamos (Machine Category/ER) en la variable rr_br_cost_usd
        total_labor_cost = rr_br_cost_usd * lqty * duration_lab # * monthly_hours? 
        # NOTA: En tu test case, 'Monthly Hours' aparece pero el cálculo final parece usar el costo unitario derivado.
        # Si el costo en tabla es "por hora", multiplicamos por horas. Si es "mensual", no. 
        # Asumiré costo mensual base según la magnitud de los números en Labor.csv (ej: 2 millones COP).
        
        st.success(f"👷 Costo Total Labor: **USD {total_labor_cost:,.2f}**")

    # --- TAB 3: RESUMEN ---
    with tab3:
        st.header("Resumen de Cotización")
        
        total_cost = total_service_cost + total_labor_cost
        
        # Aplicar Riesgo (Opcional, según Logic Rules no vi fórmula explícita sumando riesgo al total, 
        # pero UI_CONFIG lo pide. Lo mostraré informativo o sumado si es la práctica standard)
        cost_risk = total_cost * risk_pct
        final_total_with_risk = total_cost + cost_risk

        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.write(f"**Cliente:** {client_name} ({client_num})")
            st.write(f"**País:** {pais_sel}")
            st.write(f"**Riesgo ({risk_sel}):** {risk_pct:.1%}")
        
        with col_res2:
            st.write(f"Servicios: USD {total_service_cost:,.2f}")
            st.write(f"Labor: USD {total_labor_cost:,.2f}")
            st.divider()
            st.write(f"Subtotal: USD {total_cost:,.2f}")
            st.write(f"Provisión Riesgo: USD {cost_risk:,.2f}")
            st.subheader(f"Total: USD {final_total_with_risk:,.2f}")

else:
    st.warning("Esperando archivos CSV...")
