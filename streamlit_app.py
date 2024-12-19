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
@st.cache_data(show_spinner=False, ttl=300)  # TTL opcional: los datos se recargan cada 5 minutos
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

# Cargar datos al inicio o recargar al presionar el botón
if st.button("Recargar datos"):
    df = load_data(url)  # Descargar los datos nuevamente
    st.session_state.df = df  # Actualizar en session_state
    st.success("Datos recargados correctamente.")
elif 'df' not in st.session_state or st.session_state.df is None:
    st.session_state.df = load_data(url)  # Descargar los datos por primera vez si no están en session_state

df = st.session_state.df

# Verificar que el archivo se descargó correctamente
if df is None or df.empty:
    st.warning("No se encontraron datos. Revisa el enlace o el formato del archivo.")
else:
    # Asegurarse de que la columna 'Fecha' esté en formato datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%d-%m-%Y', errors='coerce')  # Especificar el formato 'dd-mm-yyyy'
    
    # Eliminar fechas no válidas (NaT)
    df = df.dropna(subset=['Fecha'])

    # Reemplazar comas por puntos en los valores numéricos
    df['ATPasa'] = df['ATPasa'].astype(str).str.replace(',', '.', regex=False)
    
    # Asegurarse de que 'ATPasa' sea numérico después de reemplazar las comas
    df['ATPasa'] = pd.to_numeric(df['ATPasa'], errors='coerce')  # Convierte a NaN cualquier valor no numérico
    df = df.dropna(subset=['ATPasa'])  # Eliminar filas con 'ATPasa' no numérico

    # Crear opciones para los filtros
    centro_options = ['Todos'] + df['Centro'].unique().tolist()
    lote_options = ['Todos'] + df['Lote'].unique().tolist()
    unidad_options = ['Todos'] + df['Unidad'].unique().tolist()

    st.sidebar.header("Filtros")
    selected_centro = st.sidebar.multiselect("Seleccionar Centro", centro_options)
    selected_lote = st.sidebar.multiselect("Seleccionar Lote", lote_options)
    selected_unidad = st.sidebar.multiselect("Seleccionar Unidad", unidad_options)

    # Validar que selected_unidad siempre sea una lista
    if selected_unidad == []:  # Si no se seleccionan unidades, poner 'Todos'
        selected_unidad = ['Todos']
    
    # Filtrar los datos según la selección
    filtered_df = df.copy()
    
    # Aplicar filtros de Centro, Lote y Unidad
    if selected_centro and 'Todos' not in selected_centro:
        filtered_df = filtered_df[filtered_df['Centro'].isin(selected_centro)]
    if selected_lote and 'Todos' not in selected_lote:
        filtered_df = filtered_df[filtered_df['Lote'].isin(selected_lote)]
    if selected_unidad and 'Todos' not in selected_unidad:
        filtered_df = filtered_df[filtered_df['Unidad'].isin(selected_unidad)]

    # Verificar si hay datos después del filtrado
    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
    else:
        # Ordenar por fecha
        filtered_df = filtered_df.sort_values(by='Fecha')

        # Verificar si la columna 'Mes-Dia' existe en los datos
        if 'Mes-Dia' not in filtered_df.columns:
            st.error("La columna 'Mes-Dia' no está presente en los datos.")
        else:
            # Configuración de la figura
            fig, ax1 = plt.subplots(figsize=(14, 8))

            # Crear la paleta de colores
            palette = sns.color_palette("pastel", n_colors=filtered_df['C. Externa'].nunique()).as_hex()

            # Crear el boxplot usando 'Mes-Dia'
            sns.boxplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

            # Crear el stripplot
            sns.stripplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                          jitter=True, alpha=0.7, palette=palette, dodge=True, ax=ax1, legend=False)

            # Configurar las etiquetas de fecha en el eje x ordenadas por la columna 'Fecha'
            ordered_labels = filtered_df.sort_values(by='Fecha')['Mes-Dia'].unique()
            ax1.set_xticks(range(len(ordered_labels)))
            ax1.set_xticklabels(ordered_labels, rotation=90)

            # Agregar título y etiquetas
            ax1.set_ylabel("ATPasa", fontsize=12)

            # Crear segundo eje (para gráfico de barras apiladas)
            ax2 = ax1.twinx()
            percentages = filtered_df.groupby(['Mes-Dia', 'C. Externa']).size().unstack(fill_value=0)
            percentages = percentages.div(percentages.sum(axis=1), axis=0) * 100

            percentages.plot(kind='bar', stacked=True, ax=ax2, alpha=0.3, width=0.5, color=palette)

            ax2.set_ylabel("% de Categoría", fontsize=12)
            ax2.set_ylim(0, 100)
            ax2.grid(visible=False)
            ax2.legend(title="Condición Externa", bbox_to_anchor=(1.15, 0.5), loc='center')

            # Mostrar el gráfico en Streamlit
            st.pyplot(fig)

