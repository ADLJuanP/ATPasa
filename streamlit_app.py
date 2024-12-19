# Verificar si la columna 'Mes-Dia' existe en los datos
if 'Mes-Dia' not in filtered_df.columns:
    st.error("La columna 'Mes-Dia' no está presente en los datos.")
else:
    # Ordenar 'Mes-Dia' según la columna 'Fecha'
    filtered_df['Mes-Dia'] = pd.Categorical(
        filtered_df['Mes-Dia'],
        categories=filtered_df.sort_values(by='Fecha')['Mes-Dia'].unique(),
        ordered=True
    )

    # Configuración de la figura
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # Crear la paleta de colores
    palette = sns.color_palette("pastel", n_colors=filtered_df['C. Externa'].nunique()).as_hex()

    # Crear el boxplot usando 'Mes-Dia'
    sns.boxplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], showfliers=False, color="lightblue", ax=ax1)

    # Crear el stripplot
    sns.stripplot(x=filtered_df['Mes-Dia'], y=filtered_df['ATPasa'], hue=filtered_df['C. Externa'],
                  jitter=True, alpha=0.7, palette=palette, dodge=True, ax=ax1, legend=False)

    # Configurar las etiquetas de fecha en el eje x
    ax1.set_xticklabels(filtered_df['Mes-Dia'], rotation=90)  # Mostrar 'Mes-Dia' en el eje X

    # **Quitar el título del eje x**
    ax1.set_xlabel('')  

    # Agregar título y etiquetas
    ax1.set_ylabel("ATPasa", fontsize=12)
    ax1.set_title(
        f"Evolución ATPasa y Condición Externa\nCentro(s): {centro_title}, Lote(s): {lote_title}, Unidad(es): {unidad_title}",
        fontsize=16
    )

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


