import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import aplicar_estilo
from utils.loaders import cargar_datos

aplicar_estilo()
st.title("Anexo 4 – Intervenciones Complementarias")

data = cargar_datos()
df = data.get("a4")

if not isinstance(df, pd.DataFrame):
    st.warning("No se encontró el archivo del Anexo 4.")
    st.stop()

if "Puntaje (%)" in df.columns:
    st.metric("Promedio Puntaje (%)", round(df["Puntaje (%)"].mean(), 1))

fig = px.box(
    df, x="Región", y="Puntaje (%)",
    color="Región", color_discrete_sequence=px.colors.qualitative.Safe,
    title="Distribución de Puntajes por Región"
)
fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(fig, use_container_width=True)

with st.expander("Ver datos detallados"):
    st.dataframe(df)
