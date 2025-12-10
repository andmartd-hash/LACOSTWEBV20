import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

st.set_page_config(page_title="LACOST V20 Dynamic", layout="wide")

# ==========================================
# 1. SIMULACIÓN DE TU ARCHIVO "UI_CONFIG"
# ==========================================
# Aquí es donde defines la estructura. Nota el "-slide" en la primera sección.
ui_config_data = [
    # Sección 1: Marcada con "-slide" para ir al Sidebar
    {"Section": "1. Configuración-slide", "Sub-Section": "-", "Field Label": "País", "Data Type": "Dropdown", "Source": "Countries"},
    {"Section": "1. Configuración-slide", "Sub-Section": "-", "Field Label": "Moneda", "Data Type": "Read-Only", "Source": "Currency_Ref"},
    {"Section": "1. Configuración-slide", "Sub-Section": "Vigencia", "Field Label": "Inicio Contrato", "Data Type": "Date", "Source": "User"},
    {"Section": "1. Configuración-slide", "Sub-Section": "Vigencia", "Field Label": "Fin Contrato", "Data Type": "Date", "Source": "User"},
    
    # Sección 2: Sin "-slide", va al cuerpo principal
    {"Section": "2. Servicios", "Sub-Section": "Selección", "Field Label": "Offering / Servicio", "Data Type": "Dropdown", "Source": "Offerings"},
    {"Section": "2. Servicios", "Sub-Section": "Selección", "Field Label": "QA Risk", "Data Type": "Dropdown", "Source": "Risk"},
    {"Section": "2. Servicios", "Sub-Section": "Costos", "Field Label": "SLC Profile", "Data Type": "Dropdown", "Source": "SLC"},
    {"Section": "2. Servicios", "Sub-Section": "Costos", "Field Label": "Costo Unit (USD)", "Data Type": "Number", "Source": "User"},
    {"Section": "2. Servicios", "Sub-Section": "Costos", "Field Label": "Cantidad", "Data Type": "Number", "Source": "User"},

    # Sección 3: Labor
    {"Section": "3. Labor (Recursos)", "Sub-Section": "-", "Field Label": "Rol / Perfil", "Data Type": "Dropdown", "Source": "LaborItems"},
    {"Section": "3. Labor (Recursos)", "Sub-Section": "-", "Field Label": "Horas/Meses", "Data Type": "Number", "Source": "User"},
]
df_config = pd.DataFrame(ui_config_data)

# ==========================================
# 2. CARGA DE BASES DE DATOS (Simulada)
# ==========================================
def get_database_options(source_name, selected_country=None):
    # En un caso real, aquí leerías tus otras hojas de Excel
    if source_name == "Countries":
        return ['Argentina', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Peru', 'Mexico']
    elif source_name == "Offerings":
        return ["IBM Hardware Resell", "Support Red Hat", "Customized Support HW", "Technical Support Svc"]
    elif source_name == "Risk":
        return ["Low (2%)", "Medium (5%)", "High (8%)"]
    elif source_name == "SLC":
        # Ejemplo: Filtrar SLC si es Brazil (Lógica simple para demo)
        if selected_country == "Brazil":
            return ["NStd5x9", "NStdSBD7x24"]
        return ["24X7SD (M19)", "24X74 (M47)", "24X76 (M2B)"]
    elif source_name == "LaborItems":
        return ["System Z (Cat A)", "Power HE (Cat C)", "B7 (Senior)", "B8 (Specialist)"]
    return []

# ==========================================
# 3. MOTOR DE RENDERIZADO (LA MAGIA)
# ==========================================
st.title("⚙️ LACOST V20: Generador Dinámico")

# Diccionario para guardar lo que el usuario va eligiendo
user_inputs = {}

# Agrupar por SECCIÓN (Respetando el orden del Excel)
# sort=False es vital para que no ordene alfabéticamente (1, 2, 3...)
for section_name, section_df in df_config.groupby("Section", sort=False):
    
    # --- LÓGICA "-slide" ---
    # Detectamos si la palabra clave está en el nombre de la sección
    if "-slide" in section_name.lower():
        target_container = st.sidebar  # Manda a la izquierda
        display_title = section_name.replace("-slide", "").replace("-Slide", "") # Limpia el título
    else:
        target_container = st          # Manda al centro
        display_title = section_name
    
    # Dibujar el Título de la Sección en el contenedor correcto
    with target_container:
        st.header(display_title)
        
        # Agrupar por SUB-SECCIÓN (Opcional, para orden visual)
        for sub_name, sub_df in section_df.groupby("Sub-Section", sort=False):
            if sub_name != "-":
                st.subheader(sub_name)
            
            # Dibujar cada CAMPO (Fila del Excel)
            for idx, row in sub_df.iterrows():
                label = row['Field Label']
                dtype = row['Data Type']
                source = row['Source']
                
                # Generar clave única para Streamlit
                key_id = f"{label}_{idx}"
                
                # --- RENDERIZAR SEGÚN TIPO DE DATO ---
                if dtype == "Dropdown":
                    # Obtener opciones (Pasamos el país seleccionado si ya existe)
                    curr_country = user_inputs.get("País", "Colombia") 
                    opts = get_database_options(source, curr_country)
                    val = st.selectbox(label, opts, key=key_id)
                    user_inputs[label] = val
                    
                elif dtype == "Date":
                    val = st.date_input(label, date.today(), key=key_id)
                    user_inputs[label] = val
                    
                elif dtype == "Number":
                    val = st.number_input(label, min_value=0.0, step=1.0, key=key_id)
                    user_inputs[label] = val
                
                elif dtype == "Read-Only":
                    # Ejemplo de lógica visual
                    st.info(f"{label}: (Calculado Auto)")

        # Separador visual entre secciones del main
        if target_container == st:
            st.divider()

# ==========================================
# 4. BOTÓN DE CÁLCULO (Usa lo recolectado)
# ==========================================
st.subheader("4. Resultados")
if st.button("Calcular Proyecto"):
    st.write("Datos capturados dinámicamente:")
    st.json(user_inputs) # Muestra todo lo que el sistema "leyó" de los inputs
    
    # Ejemplo de uso de los datos capturados
    try:
        cost = user_inputs.get("Costo Unit (USD)", 0)
        qty = user_inputs.get("Cantidad", 0)
        total = cost * qty
        st.success(f"Cálculo Rápido (Costo * Cantidad): ${total:,.2f}")
    except:
        st.error("Faltan datos numéricos para calcular.")
