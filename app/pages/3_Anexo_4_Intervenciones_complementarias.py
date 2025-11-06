# ==============================================================
# INTERVENCIONES COMPLEMENTARIAS – ANEXO 4
# MIDIS | UCC 2025 – Versión armonizada (A2/A3)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import yaml

from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_section_insight  # IA centrada en interpretación + recomendaciones

# --------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------
st.set_page_config(
    page_title="Anexo 4 – Intervenciones Complementarias",
    page_icon="🏷️",
    layout="wide"
)
aplicar_estilos()

st.title("Intervenciones Complementarias")
st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------------------
data = cargar_datos()
df = data.get("a4")
if df is None:
    st.warning("⚠️ No se encontró el archivo `anexo4_consolidado.xlsx` en `/data/processed/`.")
    st.stop()

# --------------------------------------------------------------
# YAML – nombres de ítems
# --------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = BASE_DIR / "config" / "settings_anexo4.yaml"

try:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        config_a4 = yaml.safe_load(f)
        mapa_items = config_a4.get("items_nombres", {})
except Exception as e:
    st.error(f"❌ Error al leer {YAML_PATH.name}: {e}")
    mapa_items = {}

# --------------------------------------------------------------
# FILTROS
# --------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    ut_sel = st.multiselect("Unidad Territorial:", sorted(df["UNIDAD_TERRITORIAL"].dropna().unique()))
with col2:
    mes_sel = st.multiselect("Mes:", sorted(df["MES"].dropna().unique()))
with col3:
    sup_sel = st.multiselect("Supervisor:", sorted(df["SUPERVISOR"].dropna().unique()))

df_filtrado = df.copy()
if ut_sel:
    df_filtrado = df_filtrado[df_filtrado["UNIDAD_TERRITORIAL"].isin(ut_sel)]
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["MES"].isin(mes_sel)]
if sup_sel:
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(sup_sel)]

if df_filtrado.empty:
    st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# --------------------------------------------------------------
# BLOQUES Y RANGOS
# --------------------------------------------------------------
bloques = {
    "Proyecto Vida Adolescente": [f"ITEM_{i}" for i in range(1, 13)],   # 1–12
    "Independencia Económica":   [f"ITEM_{i}" for i in range(13, 19)],  # 13–18
}

# --------------------------------------------------------------
# KPI GLOBAL (brechas por bloque) – igual a A3
# --------------------------------------------------------------
def porcentaje_valor(df_in, items, valor):
    subset = df_in[items]
    tot = subset.notna().sum().sum()
    if tot == 0:
        return 0.0
    return round(((subset == valor).sum().sum() / tot) * 100, 1)

colA, colB = st.columns(2)
with colA:
    st.metric("❌ % No Cumple – Proyecto Vida Adolescente",
              f"{porcentaje_valor(df_filtrado, bloques['Proyecto Vida Adolescente'], 0)}%")
with colB:
    st.metric("❌ % No Cumple – Independencia Económica",
              f"{porcentaje_valor(df_filtrado, bloques['Independencia Económica'], 0)}%")

st.markdown("---")

# --------------------------------------------------------------
# Helpers de ranking y gráfico
# --------------------------------------------------------------
def ranking_items_subset(df_in, items, valor, etiqueta_map):
    s = df_in[items].apply(lambda col: (col == valor).sum())
    s = s[s > 0].sort_values(ascending=False)
    return [{"item": k, "nombre": etiqueta_map.get(k, k), "freq": int(v)} for k, v in s.items()]

def grafico_apilado(df_in, items, titulo, etiqueta_map):
    registros = []
    for item in items:
        if item in df_in.columns:
            total = df_in[item].notna().sum()
            if total == 0:
                continue
            counts = df_in[item].value_counts().reindex([0, 1, 2], fill_value=0)
            for v, freq in counts.items():
                registros.append({
                    "Ítem": item,
                    "Descripción": etiqueta_map.get(item, item),
                    "Valor": v,
                    "Porcentaje": round((freq / total) * 100, 1)
                })
    if not registros:
        return None

    df_p = pd.DataFrame(registros).pivot_table(
        index=["Ítem", "Descripción"], columns="Valor", values="Porcentaje", fill_value=0
    ).reset_index()
    df_p.columns.name = None
    df_p = df_p.rename(columns={0: "❌ No cumple", 1: "⚠️ En desarrollo", 2: "✅ Cumple"})
    df_p["Ítem_nro"] = df_p["Ítem"].str.extract(r"(\d+)").astype(int)
    df_p = df_p.sort_values("Ítem_nro")

    color_map = {"❌ No cumple": "#D32F2F", "⚠️ En desarrollo": "#FBC02D", "✅ Cumple": "#388E3C"}

    fig = go.Figure()
    for col in ["❌ No cumple", "⚠️ En desarrollo", "✅ Cumple"]:
        fig.add_trace(go.Bar(
            y=df_p["Descripción"], x=df_p[col],
            name=col, orientation="h", marker=dict(color=color_map[col]),
            hovertemplate=f"<b>{col}:</b> %{{x:.1f}}%<extra></extra>"
        ))
    fig.update_layout(
        title=titulo, barmode="stack",
        xaxis=dict(title="Porcentaje (%)", range=[0, 100], showgrid=True, gridcolor="#ECEFF1"),
        yaxis=dict(title="", showgrid=False, autorange="reversed"),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(size=12, color="#003A70"), title_font=dict(size=16, color="#003A70"),
        legend_title_text="Estado del ítem",
        bargap=0.15, margin=dict(t=60, b=30, l=260, r=80), height=520
    )
    return fig

def resumen_ia(df_in, items, etiqueta, etiqueta_map):
    # Contexto para IA: SIN hallazgos, solo interpretación + recomendaciones
    top0 = ranking_items_subset(df_in, items, 0, etiqueta_map)
    top1 = ranking_items_subset(df_in, items, 1, etiqueta_map)
    contexto = {
        "anexo": "Anexo 4 – Intervenciones Complementarias",
        "seccion": etiqueta,
        "porcentajes": {  # por si en el futuro requieres usarlo en el prompt
            "no_cumple": porcentaje_valor(df_in, items, 0),
            "en_desarrollo": porcentaje_valor(df_in, items, 1),
            "cumple": porcentaje_valor(df_in, items, 2),
        },
        "top_no_cumple": top0,
        "top_en_desarrollo": top1
    }
    try:
        import re
        with st.spinner("Generando resumen ejecutivo..."):
            texto = generate_section_insight(contexto)
        texto = re.sub(r"<[^>]+>", "", texto)
        texto = re.sub(r"\[[^\]]+\]", "", texto).strip()
        st.markdown(
            f"""
            <div style="font-size:16px; line-height:1.6; color:#222; background-color:#f9fafb;
                        padding:15px; border-radius:8px; border-left:5px solid #004C97;">
                {texto}
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"No fue posible generar el resumen para {etiqueta}.")
        st.text(str(e))

# --------------------------------------------------------------
# BLOQUE 1 – PROYECTO VIDA ADOLESCENTE (ITEM_1 a ITEM_12)
# --------------------------------------------------------------
st.subheader("Proyecto Vida Adolescente")
resumen_ia(df_filtrado, bloques["Proyecto Vida Adolescente"], "Proyecto Vida Adolescente", mapa_items)
fig1 = grafico_apilado(df_filtrado, bloques["Proyecto Vida Adolescente"],
                       "Evaluación del Proyecto Vida Adolescente", mapa_items)
if fig1:
    st.plotly_chart(fig1, use_container_width=True)
st.markdown("---")

# --------------------------------------------------------------
# BLOQUE 2 – INDEPENDENCIA ECONÓMICA (ITEM_13 a ITEM_18)
# --------------------------------------------------------------
st.subheader("Independencia Económica")
resumen_ia(df_filtrado, bloques["Independencia Económica"], "Independencia Económica", mapa_items)
fig2 = grafico_apilado(df_filtrado, bloques["Independencia Económica"],
                       "Evaluación de Independencia Económica", mapa_items)
if fig2:
    st.plotly_chart(fig2, use_container_width=True)
