import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import requests

# Configuración de la página de Streamlit
st.set_page_config(layout="wide", page_title="Dashboard ATPasa")

# Enlace de descarga directa del archivo de Google Sheets en formato Excel
url = "https://docs.google.com/spreadsheets/d/1pddBpb0xyn2WxRVXuL4oXI_R7kdFZuHX/export?format=xlsx"

# Descargar y cargar los datos en caché
@st.cache_data
def load_data(download_url):
    try:
        response = requests.get(download_url)
        if response.status_code == 200:
            return pd.read_excel(BytesIO(response.content), engine='openpyxl')
        else:
            st.error("No se pudo descargar el archivo. Verifica el enlace.")
            return None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
        return None

# Botón para actualizar los datos
if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()  # Limpia la caché para forzar la recarga

# Cargar los datos
df = load_data(url)

# Validar si `df` es válido
if df is None or df.empty:
    st.warning("No se encontraron datos. Revisa el enlace o el formato del archivo.")
else:
    # Asegurarse de que la columna 'Fecha' esté en formato datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')  # Convertir a formato datetime
    df = df.dropna(subset=['Fecha'])  # Eliminar filas con fechas inválidas

    # Crear opciones para seleccionar Centro, Lote y Unidad
    centro_options = ["Todos"] + list(df['Centro'].unique())
    lote_options = ["Todos"] + list(df['Lote'].unique())
    unidad_options = ["Todos"] + list(df['Unidad'].unique())

    st.sidebar.header("Filtros")
    selected_centro = st.sidebar.selectbox("Seleccionar Centro", centro_options)
    selected_lote = st.sidebar.selectbox("Seleccionar Lote", lote_options)
    selected_unidad = st.sidebar.selectbox("Seleccionar Unidad", unidad_options)

    # Filtrar los datos
    filtered_df = df[(df['Centro'] == selected_centro if selected_centro != "Todos" else df['Centro']) & 
                     (df['Lote'] == selected_lote if selected_lote != "Todos" else df['Lote']) & 
                     (df['Unidad'] == selected_unidad if selected_unidad != "Todos" else df['Unidad'])]

    # Verificar si hay datos después del filtrado
    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        # Configuración de la figura
        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Ordenar por fecha
        filtered_df = filtered_df.sort_values(by='Fecha')

        # Crear la paleta de colores
        palette = sns.color_palette("pastel", n_colors=filtered_df['C. Externa'].nunique()).as_hex()

        # Crear el boxplot
        sns.boxplot(x=filtered_df['Fecha'].dt.strftime('%d/%m'), y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

        # Crear el stripplot
        sns.stripplot(x=filtered_df['Fecha'].dt.strftime('%d/%m'), y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                      jitter=True, alpha=0.7, palette=palette, dodge=True, ax=ax1, legend=False)

        # Configurar las etiquetas de fecha
        ax1.set_xticklabels(filtered_df['Fecha'].dt.strftime('%d/%m'), rotation=90)

        # Agregar título y etiquetas
        ax1.set_ylabel("ATPasa", fontsize=12)
        ax1.set_title(f"Evolución ATPasa y Condición Externa\nLote: {selected_lote}, Unidad: {selected_unidad}", fontsize=16)

        # Mostrar el gráfico en Streamlit
        st.pyplot(fig)
