import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import requests
import openpyxl

# Configuración de la página de Streamlit
st.set_page_config(layout="wide", page_title="Dashboard ATPasa")

# Enlace de descarga directa del archivo de Google Drive
url = "https://drive.google.com/uc?id=1I4gN0K0S2RQmqpSPb2dQOM9effOhfNCO"

# Descargar el archivo
def load_data(download_url):
    try:
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content), engine='openpyxl')
        else:
            st.error("No se pudo descargar el archivo. Verifica el enlace.")
            return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

df = load_data(url)

# Validar si `df` es válido
if df is None or df.empty:
    st.warning("No se encontraron datos. Revisa el enlace o el formato del archivo.")
else:
    # Asegurarse de que la columna 'Fecha' esté en formato datetime (sin horas ni minutos)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date  # Convertir a solo fecha (sin tiempo)
    df = df.dropna(subset=['Fecha'])  # Eliminar fechas no válidas

    # Crear opciones para los filtros

