import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import aplicar_estilo
from utils.loaders import cargar_datos

aplicar_estilo()
st.title("Anexo 5 – Hallazgos y Acuerdos de Mejora")

data = cargar_datos()
df = data.get("a5")

if not isinstance(df, pd.DataFrame):
    st.warning("No se encontró el archivo del Anexo 5.")
    st.stop()

if "UNIDAD_TERRITORIAL" in df.columns:
    df.rename(columns={"UNIDAD_TERRITORIAL": "Unidad Territorial"}, inplace=True)

regiones = st.multiselect(
    "Filtrar por Unidad Territorial:",
    sorted(df["Unidad Territorial"].dropna().unique())
)
if regiones:
    df = df[df["Unidad Territorial"].isin(regiones)]

if "PLAZO_DÍAS" not in df.columns and "PLAZO" in df.columns:
    df["PLAZO_DÍAS"] = pd.to_numeric(df["PLAZO"].astype(str).str.extract(r"(\\d+)")[0], errors="coerce")
elif "PLAZO_DÍAS" in df.columns:
    df["PLAZO_DÍAS"] = pd.to_numeric(df["PLAZO_DÍAS"].astype(str).str.extract(r"(\\d+)")[0], errors="coerce")

df["Estado"] = df["PLAZO_DÍAS"].apply(
    lambda x: "Cumplido" if pd.notna(x) and x <= 3 else
              "En curso" if pd.notna(x) and 3 < x <= 7 else
              "Vencido" if pd.notna(x) and x > 7 else "Sin definir"
)

estado_df = df["Estado"].value_counts().reset_index()
estado_df.columns = ["Estado", "Cantidad"]

fig = px.bar(
    estado_df, x="Cantidad", y="Estado", orientation="h",
    color="Estado",
    color_discrete_map={
        "Cumplido": "#2E7D32",
        "En curso": "#FBC02D",
        "Vencido": "#D9534F",
        "Sin definir": "#9E9E9E"
    },
    title="Estado de Cumplimiento de Acuerdos"
)
fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
st.plotly_chart(fig, use_container_width=True)

with st.expander("Ver detalles de acuerdos"):
    st.dataframe(df)
