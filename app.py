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

    # Tabla OFFERINGS (Datos del archivo Source 6 - Nombres largos para probar vista)
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

    # Tabla SLC (Datos parciales del Source 3 para lógica Scope)
    slc_data = [
        {'Scope': 'no brazil', 'Desc': '24X74On-site Response time (M47)', 'UPLF': 1.5},
        {'Scope': 'no brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'no brazil', 'Desc': '24X76Fix time (M2B)', 'UPLF': 1.6},
        {'Scope': 'Brazil', 'Desc': '24X7SDOn-site arrival time (M19)', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStd5x9', 'UPLF': 1.0},
        {'Scope': 'Brazil', 'Desc': 'NStdSBD7x24 (1.278)', 'UPLF': 1.278},
    ]
    df_slc = pd.DataFrame(slc_data)

    # Tabla LABOR (Datos del Source 7/8)
    labor_data = [
        {'Type': 'Machine Category', 'Item': 'System Z (Cat A)', 'Argentina': 304504.2, 'Colombia': 2054058.99, 'Ecuador': 991.20, 'Brazil': 2803.85},
        {'Type': 'Machine Category', '
