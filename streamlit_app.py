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
url = "https://drive.google.com/uc?id=1pddBpb0xyn2WxRVXuL4oXI_R7kdFZuHX"

# Descargar el archivo y guardarlo en caché
@st.cache_data
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

# Botón para actualizar los datos
if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()  # Limpia la caché para forzar la recarga

# Cargar los datos
df = load_data(url)

# Validar si `df` es válido
if df is None or df.empty:
    st.warning("No se encontraron datos. Revisa el enlace o el formato del archivo.")
else:
    # Asegurarse de que la columna 'Fecha' esté en formato datetime (sin horas ni minutos)
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce').dt.date  # Convertir a solo fecha (sin tiempo)
    df = df.dropna(subset=['Fecha'])  # Eliminar fechas no válidas

    # Crear opciones para los filtros
    centro_options = ['Todos'] + df['Centro'].unique().tolist()
    lote_options = ['Todos'] + df['Lote'].unique().tolist()
    unidad_options = ['Todos'] + df['Unidad'].unique().tolist()

    st.sidebar.header("Filtros")
    selected_centro = st.sidebar.selectbox("Seleccionar Centro", centro_options)
    selected_lote = st.sidebar.selectbox("Seleccionar Lote", lote_options)
    selected_unidad = st.sidebar.selectbox("Seleccionar Unidad", unidad_options)

    # Filtrar los datos según la selección
    filtered_df = df.copy()
    if selected_centro != 'Todos':
        filtered_df = filtered_df[filtered_df['Centro'] == selected_centro]
    if selected_lote != 'Todos':
        filtered_df = filtered_df[filtered_df['Lote'] == selected_lote]
    if selected_unidad != 'Todos':
        filtered_df = filtered_df[filtered_df['Unidad'] == selected_unidad]

    # Verificar si hay datos después del filtrado
    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        # Ordenar por fecha
        filtered_df = filtered_df.sort_values(by='Fecha')

        # Configuración de la figura
        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Crear la paleta de colores
        palette = sns.color_palette("pastel", n_colors=filtered_df['C. Externa'].nunique()).as_hex()

        # Crear el boxplot
        sns.boxplot(x=filtered_df['Fecha'], y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

        # Crear el stripplot
        sns.stripplot(x=filtered_df['Fecha'], y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                      jitter=True, alpha=0.7, palette=palette, dodge=True, ax=ax1, legend=False)

        # Configurar las etiquetas de fecha en el eje x
        ax1.set_xticklabels(filtered_df['Fecha'].astype(str), rotation=90)

        # Agregar título y etiquetas
        ax1.set_ylabel("ATPasa", fontsize=12)
        ax1.set_title(
            f"Evolución ATPasa y Condición Externa\nCentro: {selected_centro}, Lote: {selected_lote}, Unidad: {selected_unidad}",
            fontsize=16
        )

        # Crear segundo eje (para gráfico de barras apiladas)
        ax2 = ax1.twinx()
        percentages = filtered_df.groupby(['Fecha', 'C. Externa']).size().unstack(fill_value=0)
        percentages = percentages.div(percentages.sum(axis=1), axis=0) * 100

        percentages.plot(kind='bar', stacked=True, ax=ax2, alpha=0.3, width=0.5, color=palette)

        ax2.set_ylabel("% de Categoría", fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.grid(visible=False)
        ax2.legend(title="Condición Externa", bbox_to_anchor=(1.15, 0.5), loc='center')

        # Mostrar el gráfico en Streamlit
        st.pyplot(fig)
