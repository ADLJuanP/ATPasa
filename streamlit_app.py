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
@st.cache_data
def load_data(download_url):
    response = requests.get(download_url)
    if response.status_code == 200:
        try:
            return pd.read_excel(BytesIO(response.content), engine='openpyxl')
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            return None
    else:
        st.error("No se pudo descargar el archivo. Verifica el enlace.")
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
    centro_options = ['Todos'] + df['Centro'].unique().tolist()
    lote_options = ['Todos'] + df['Lote'].unique().tolist()
    unidad_options = ['Todos'] + df['Unidad'].unique().tolist()

    st.sidebar.header("Filtros")
    selected_centro = st.sidebar.selectbox("Seleccionar Centro", centro_options)
    selected_lote = st.sidebar.multiselect("Seleccionar Lote", lote_options)
    selected_unidad = st.sidebar.multiselect("Seleccionar Unidad", unidad_options)

    # Filtrar los datos según la selección
    filtered_df = df.copy()
    if selected_centro != 'Todos':
        filtered_df = filtered_df[filtered_df['Centro'] == selected_centro]
    if selected_lote:
        filtered_df = filtered_df[filtered_df['Lote'].isin(selected_lote)]
    if selected_unidad:
        filtered_df = filtered_df[filtered_df['Unidad'].isin(selected_unidad)]

    # Verificar si hay datos después del filtrado
    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        # Ordenar por fecha
        filtered_df = filtered_df.sort_values(by='Fecha')

        # Convertir la columna 'Fecha' en formato datetime a un formato adecuado para el gráfico
        filtered_df['Fecha'] = pd.to_datetime(filtered_df['Fecha']).dt.strftime('%Y-%m-%d')

        # Configuración de la figura
        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Crear una paleta de colores consistente para "C. Externa"
        unique_conditions = sorted(filtered_df['C. Externa'].unique())  # Asegurar el mismo orden
        palette = sns.color_palette("Set2", n_colors=len(unique_conditions)).as_hex()
        condition_color_map = dict(zip(unique_conditions, palette))

        # Crear el boxplot
        sns.boxplot(x=filtered_df['Fecha'], y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

        # Crear el stripplot con colores consistentes
        sns.stripplot(x=filtered_df['Fecha'], y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                      jitter=True, alpha=0.7, palette=condition_color_map, dodge=True, ax=ax1, legend=False)

        # Configurar las etiquetas de fecha en el eje x
        ax1.set_xticklabels(filtered_df['Fecha'], rotation=90)

        # Agregar título y etiquetas
        ax1.set_ylabel("ATPasa", fontsize=12)
        ax1.set_title(
            f"Evolución ATPasa y Condición Externa\nCentro: {selected_centro}, Lote(s): {', '.join(selected_lote) if selected_lote else 'Todos'}, Unidad(es): {', '.join(selected_unidad) if selected_unidad else 'Todos'}",
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

