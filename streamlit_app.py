import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import requests

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
        # Asegurarse de que 'C. Externa' sea numérico
        filtered_df['C. Externa'] = pd.to_numeric(filtered_df['C. Externa'], errors='coerce')

        # Eliminar filas con 'C. Externa' no numérica
        filtered_df = filtered_df.dropna(subset=['C. Externa'])

        # Verificar las categorías de 'C. Externa'
        valid_columns = [2, 3, 4]
        existing_categories = filtered_df['C. Externa'].unique()
        missing_categories = [cat for cat in valid_columns if cat not in existing_categories]

        if missing_categories:
            st.warning(f"Faltan las siguientes categorías en los datos: {missing_categories}")

        # Asegurarse de que solo seleccionamos las categorías que existen
        valid_columns = [cat for cat in valid_columns if cat in existing_categories]

        # Ordenar las etiquetas de 'Mes-Dia' según la columna 'Fecha'
        ordered_labels = filtered_df.drop_duplicates(subset=['Mes-Dia']).sort_values(by='Fecha')['Mes-Dia']

        # Crear la figura del gráfico
        fig, ax1 = plt.subplots(figsize=(14, 8))

        # Crear el boxplot usando 'Mes-Dia'
        sns.boxplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

        # Crear el stripplot
        sns.stripplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                      jitter=True, alpha=0.7, dodge=True, ax=ax1, legend=False)

        # Ordenar las etiquetas en el eje X de acuerdo a la columna 'Fecha'
        ax1.set_xticks(range(len(ordered_labels)))
        ax1.set_xticklabels(ordered_labels, rotation=90)

        # Quitar el título del eje x
        ax1.set_xlabel(None)
        ax1.set_ylabel("ATPasa", fontsize=12)

        # Crear segundo eje (para gráfico de barras apiladas)
        ax2 = ax1.twinx()

        percentages = filtered_df.groupby(['Mes-Dia', 'C. Externa']).size().unstack(fill_value=0)
        percentages = percentages.div(percentages.sum(axis=1), axis=0) * 100

        # Ordenar las categorías 2, 3, 4 en el gráfico de barras apiladas
        ordered_percentages = percentages[valid_columns]

        # Crear las barras apiladas con la paleta de colores ajustada
        ordered_percentages.plot(kind='bar', stacked=True, ax=ax2, alpha=0.3, width=0.5, color=[color_mapping[cat] for cat in valid_columns])

        # Mostrar el gráfico
        st.pyplot(fig)
