# app/pages/1_Anexo_2_Acompañamiento.py
import streamlit as st
import plotly.express as px
from pathlib import Path
import yaml
import pandas as pd

from utils.style import aplicar_estilo
from utils.loaders import cargar_datos
from utils.normalizers import normalizar_anexo2

aplicar_estilo()
st.title("Anexo 2 – Acompañamiento al Hogar con Gestión Territorial")

# --- Cargar data
data = cargar_datos()
df = data.get("a2")

if df is None or not isinstance(df, pd.DataFrame):
    st.warning("No se encontró el archivo del Anexo 2 en data/processed/anexo2_consolidado.xlsx")
    st.stop()

df = normalizar_anexo2(df)

# --- Cargar YAML (items_nombres)
BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH_A2 = BASE_DIR / "config" / "settings_anexo2.yaml"
mapa_items = {}
try:
    if CONFIG_PATH_A2.exists():
        with open(CONFIG_PATH_A2, "r", encoding="utf-8") as f:
            config_a2 = yaml.safe_load(f) or {}
            if "items_nombres" in config_a2:
                mapa_items = config_a2["items_nombres"]
            elif "items" in config_a2:
                mapa_items = config_a2["items"]
            elif "columnas" in config_a2:
                mapa_items = config_a2["columnas"]
    else:
        st.warning("⚠️ No se encontró settings_anexo2.yaml. Se usarán nombres genéricos de ítems.")
except Exception as e:
    st.warning(f"No se pudo leer settings_anexo2.yaml: {e}")

# --- Filtros
if "Región" not in df.columns:
    st.error("La columna 'Región' no está disponible tras normalizar el Anexo 2.")
    st.stop()

regiones = st.multiselect("Filtrar por Región:", sorted(df["Región"].dropna().unique()))
if regiones:
    df = df[df["Región"].isin(regiones)]

# --- Promedio por región
if "Puntaje (%)" in df.columns:
    prom = df.groupby("Región", dropna=True)["Puntaje (%)"].mean().reset_index()
    fig = px.bar(
        prom, x="Puntaje (%)", y="Región", orientation="h",
        color="Puntaje (%)", color_continuous_scale="Blues",
        title="Promedio de Puntaje por Región"
    )
    fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay columna 'Puntaje (%)' para graficar.")

st.markdown("---")
st.subheader("Ítems en Desarrollo (Valor = 1)")

cols_items = [c for c in df.columns if c.upper().startswith("ITEM_")]
if not cols_items:
    st.warning("No se encontraron columnas de ítems (ITEM_1, ITEM_2, etc.) en la base.")
else:
    # (A) Conteo total por región
    df_items_1 = df.groupby("Región")[cols_items].apply(lambda x: (x == 1).sum().sum()).reset_index()
    df_items_1.columns = ["Región", "Total Ítems en Desarrollo"]
    fig1 = px.bar(
        df_items_1, x="Total Ítems en Desarrollo", y="Región", orientation="h",
        color="Total Ítems en Desarrollo", color_continuous_scale="Oranges",
        title="Cantidad de Ítems en Desarrollo por Región"
    )
    fig1.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    st.plotly_chart(fig1, use_container_width=True)

    # (B) Top 10 de ítems con valor 1
    items_counts = (df[cols_items] == 1).sum().sort_values(ascending=False).reset_index()
    items_counts.columns = ["Ítem", "Veces en Desarrollo"]

    if mapa_items:
        items_counts["Ítem"] = items_counts["Ítem"].apply(
            lambda s: mapa_items.get(s, mapa_items.get(s.upper(), s))
        )

    fig2 = px.bar(
        items_counts.head(10), x="Veces en Desarrollo", y="Ítem", orientation="h",
        color="Veces en Desarrollo", color_continuous_scale="Reds",
        title="Ítems con mayor frecuencia de valor 1 (En desarrollo)"
    )
    fig2.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
with st.expander("Ver datos detallados"):
    st.dataframe(df)
