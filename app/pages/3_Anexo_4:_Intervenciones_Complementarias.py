# ==============================================================
# MONITOREO – ANEXO 4: ACOMPAÑAMIENTO A JÓVENES (versión optimizada)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_anexo4_summary
import logging

# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================

st.set_page_config(page_title="Anexo 4 – Acompañamiento a Jóvenes", page_icon="🧭", layout="wide")
aplicar_estilos()

st.title("Intervenciones Complementarias")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# CARGA DE DATOS
# ==============================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@st.cache_data(show_spinner=False)
def cargar_y_preparar_datos():
    try:
        data = cargar_datos()
        df = data.get("a4")
        if df is None or df.empty:
            st.warning("No se encontró el archivo `anexo4_consolidado.xlsx` en `/data/processed/`.")
            return None
        return df
    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        return None

df = cargar_y_preparar_datos()
if df is None:
    st.stop()

# ==============================================================
# FILTROS
# ==============================================================

if "filters" not in st.session_state:
    st.session_state.filters = {"ut": [], "mes": [], "sup": []}

col1, col2, col3 = st.columns(3)
with col1:
    ut_sel = st.multiselect("Unidad Territorial:", sorted(df["UNIDAD_TERRITORIAL"].dropna().unique()),
                            default=st.session_state.filters["ut"])
with col2:
    mes_sel = st.multiselect("Mes:", sorted(df["MES"].dropna().unique()),
                             default=st.session_state.filters["mes"])
with col3:
    sup_sel = st.multiselect("Supervisor:", sorted(df["SUPERVISOR"].dropna().unique()),
                             default=st.session_state.filters["sup"])

st.session_state.filters.update({"ut": ut_sel, "mes": mes_sel, "sup": sup_sel})

df_filtrado = df.copy()
if ut_sel: df_filtrado = df_filtrado[df_filtrado["UNIDAD_TERRITORIAL"].isin(ut_sel)]
if mes_sel: df_filtrado = df_filtrado[df_filtrado["MES"].isin(mes_sel)]
if sup_sel: df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(sup_sel)]

if df_filtrado.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================================================
# 💬 RESUMEN AUTOMÁTICO (IA)
# ==============================================================

contexto_llm = {
    "unidad_territorial": ut_sel or "todas",
    "mes": mes_sel or "todos",
    "supervisor": sup_sel or "todos",
    "porcentajes_globales": {
        "adolescentes": df_filtrado["PORCENTAJE_ADOLES"].mean() if "PORCENTAJE_ADOLES" in df_filtrado else None,
        "independencia": df_filtrado["PORCENTAJE_INDEP"].mean() if "PORCENTAJE_INDEP" in df_filtrado else None,
        "total": df_filtrado["PORCENTAJE_TOTAL"].mean() if "PORCENTAJE_TOTAL" in df_filtrado else None
    }
}

try:
    with st.spinner("Generando resumen operativo..."):
        texto = generate_anexo4_summary(contexto_llm)
        import re
        texto_limpio = re.sub(r"<[^>]+>", "", texto)
        st.markdown(
            f"""
            <div style="margin-top:10px; font-size:15.5px; line-height:1.7; color:#333333;
            font-family:'Source Sans Pro',sans-serif;">{texto_limpio}</div>
            """,
            unsafe_allow_html=True
        )
except Exception as e:
    st.warning("No fue posible generar el resumen automático.")
    st.text(str(e))

st.markdown("<br><hr style='border:0.5px solid #ddd;margin:25px 0;'>", unsafe_allow_html=True)

# ==============================================================
# 📊 RANKING GLOBAL POR COMPONENTE
# ==============================================================

componentes = {
    "Adolescentes": ("PORCENTAJE_ADOLES", "EVALUACION_ADOLES"),
    "Independencia Económica": ("PORCENTAJE_INDEP", "EVALUACION_INDEP"),
    "Total": ("PORCENTAJE_TOTAL", "EVALUACION_TOTAL")
}

for nombre, (col_pct, col_eval) in componentes.items():
    if col_pct in df_filtrado.columns and col_eval in df_filtrado.columns:
        st.markdown(f"### 🔹 {nombre}")

        ranking = (
            df_filtrado.groupby("UNIDAD_TERRITORIAL", as_index=False)
            .agg(
                PORCENTAJE=(col_pct, "mean"),
                EVALUACION=(col_eval, lambda x: x.mode()[0] if not x.mode().empty else "Sin dato")
            )
            .sort_values("PORCENTAJE", ascending=False)
        )
        ranking["PORCENTAJE"] = (ranking["PORCENTAJE"] * 100).round(1)

        col1, col2 = st.columns(2)
        n_show = min(5, len(ranking))

        with col1:
            fig_top = px.bar(
                ranking.head(n_show),
                x="PORCENTAJE",
                y="UNIDAD_TERRITORIAL",
                orientation="h",
                color="EVALUACION",
                color_discrete_map={
                    "DEFICIENTE": "#C62828",
                    "REGULAR": "#F9A825",
                    "BUENO": "#2E7D32",
                    "EXCELENTE": "#1565C0",
                    "Sin dato": "#90A4AE"
                },
                text_auto=".1f",
                title=f"🔹 Mejores UT – {nombre}"
            )
            fig_top.update_layout(xaxis_title="Porcentaje (%)", yaxis_title=None, height=380)
            st.plotly_chart(fig_top, use_container_width=True)

        with col2:
            fig_bottom = px.bar(
                ranking.tail(n_show).sort_values("PORCENTAJE", ascending=True),
                x="PORCENTAJE",
                y="UNIDAD_TERRITORIAL",
                orientation="h",
                color="EVALUACION",
                color_discrete_map={
                    "DEFICIENTE": "#C62828",
                    "REGULAR": "#F9A825",
                    "BUENO": "#2E7D32",
                    "EXCELENTE": "#1565C0",
                    "Sin dato": "#90A4AE"
                },
                text_auto=".1f",
                title=f"🔸 Menor desempeño – {nombre}"
            )
            fig_bottom.update_layout(xaxis_title="Porcentaje (%)", yaxis_title=None, height=380)
            st.plotly_chart(fig_bottom, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# 🔥 MAPA DE CALOR – PROMEDIO DE ÍTEMS
# ==============================================================

cols_items = [c for c in df_filtrado.columns if c.startswith("ITEM_")]
if cols_items:
    heat = df_filtrado.groupby("UNIDAD_TERRITORIAL")[cols_items].mean().reset_index()
    heat_melt = heat.melt(id_vars="UNIDAD_TERRITORIAL", var_name="Ítem", value_name="Promedio")

    heat_melt["Etiqueta"] = heat_melt["Ítem"].apply(lambda x: x.replace("ITEM_", "Item "))
    heat_melt["num_item"] = heat_melt["Etiqueta"].str.extract(r"(\d+)").astype(int)
    heat_melt = heat_melt.sort_values("num_item")

    matriz = heat_melt.pivot(index="UNIDAD_TERRITORIAL", columns="Etiqueta", values="Promedio")
    matriz = matriz.reindex(sorted(matriz.columns, key=lambda x: int(x.split(" ")[1])), axis=1)

    fig_heat = px.imshow(
        matriz,
        color_continuous_scale="YlOrRd",
        title="Mapa de calor – Promedio de cumplimiento por ítem y Unidad Territorial"
    )
    fig_heat.update_layout(
        height=650,
        margin=dict(l=60, r=60, t=60, b=60),
        coloraxis_colorbar=dict(title="Promedio"),
        xaxis_title="Ítems evaluados",
        yaxis_title="Unidad Territorial"
    )
    st.plotly_chart(fig_heat, use_container_width=True)
