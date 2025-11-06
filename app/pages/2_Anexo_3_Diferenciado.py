# ==============================================================
# ACOMPAÑAMIENTO DIFERENCIADO – ANEXO 3
# MIDIS | UCC 2025 – Versión profesional y armonizada
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import yaml
from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_section_summary  # se reutiliza la función IA

# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================

st.set_page_config(
    page_title="Anexo 3 – Acompañamiento Diferenciado",
    page_icon="👥",
    layout="wide"
)
aplicar_estilos()

# ==============================================================
# CABECERA
# ==============================================================

st.title("Acompañamiento Diferenciado")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# CARGA DE DATOS
# ==============================================================

data = cargar_datos()
df = data.get("a3")  # base consolidada del anexo 3

if df is None:
    st.warning("⚠️ No se encontró el archivo `anexo3_consolidado.xlsx` en `/data/processed/`.")
    st.stop()

# ==============================================================
# CARGAR YAML DE NOMBRES DE ÍTEMS
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = BASE_DIR / "config" / "settings_anexo3.yaml"

try:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        config_a3 = yaml.safe_load(f)
        mapa_items = config_a3.get("items_nombres", {})
except Exception as e:
    st.error(f"❌ Error al leer {YAML_PATH.name}: {e}")
    mapa_items = {}

# ==============================================================
# FILTROS
# ==============================================================

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

# ==============================================================
# KPI GLOBALES (BRECHAS)
# ==============================================================

grupos = {
    "Rol del Gestor Local": [f"ITEM_{i}" for i in range(1, 7)],
    "Facilitador(a)": [f"ITEM_{i}" for i in range(7, 13)],
    "Coordinador Técnico Zonal (CTZ)": [f"ITEM_{i}" for i in range(13, 18)]
}

def porcentaje_valor(df, items, valor):
    subset = df[items]
    total_validos = subset.notna().sum().sum()
    if total_validos == 0:
        return 0
    total_valor = (subset == valor).sum().sum()
    return round((total_valor / total_validos) * 100, 1)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("❌ % No Cumple – Rol del Gestor", f"{porcentaje_valor(df_filtrado, grupos['Rol del Gestor Local'], 0)}%")
with col2:
    st.metric("❌ % No Cumple – Facilitador(a)", f"{porcentaje_valor(df_filtrado, grupos['Facilitador(a)'], 0)}%")
with col3:
    st.metric("❌ % No Cumple – CTZ", f"{porcentaje_valor(df_filtrado, grupos['Coordinador Técnico Zonal (CTZ)'], 0)}%")

st.markdown("---")

# ==============================================================
# FUNCIÓN DE PROCESAMIENTO Y GRÁFICO
# ==============================================================

def generar_grafico(df, items, titulo, mapa_items):
    registros = []
    for item in items:
        if item in df.columns:
            total = df[item].notna().sum()
            if total == 0:
                continue
            counts = df[item].value_counts().reindex([0, 1, 2], fill_value=0)
            for valor, freq in counts.items():
                registros.append({
                    "Ítem": item,
                    "Descripción": mapa_items.get(item, item),
                    "Valor": valor,
                    "Frecuencia": freq,
                    "Porcentaje": round((freq / total) * 100, 1)
                })
    if not registros:
        return None

    df_p = pd.DataFrame(registros).pivot_table(
        index=["Ítem", "Descripción"],
        columns="Valor",
        values="Porcentaje",
        fill_value=0
    ).reset_index()

    df_p.columns.name = None
    df_p = df_p.rename(columns={0: "❌ No cumple", 1: "⚠️ En desarrollo", 2: "✅ Cumple"})
    df_p["Ítem_nro"] = df_p["Ítem"].str.extract(r"(\d+)").astype(int)
    df_p = df_p.sort_values("Ítem_nro")

    color_map = {
        "❌ No cumple": "#D32F2F",
        "⚠️ En desarrollo": "#FBC02D",
        "✅ Cumple": "#388E3C"
    }

    fig = go.Figure()
    for col in ["❌ No cumple", "⚠️ En desarrollo", "✅ Cumple"]:
        fig.add_trace(go.Bar(
            y=df_p["Descripción"],
            x=df_p[col],
            name=col,
            orientation="h",
            marker=dict(color=color_map[col]),
            hovertemplate=f"<b>{col}:</b> %{{x:.1f}}%<extra></extra>"
        ))

    fig.update_layout(
        title=titulo,
        barmode="stack",
        xaxis=dict(title="Porcentaje (%)", range=[0, 100], showgrid=True, gridcolor="#ECEFF1"),
        yaxis=dict(title="", showgrid=False, autorange="reversed"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(size=12, color="#003A70"),
        title_font=dict(size=16, color="#003A70"),
        legend_title_text="Estado del ítem",
        bargap=0.15,
        margin=dict(t=60, b=30, l=250, r=80),
        height=500
    )
    return fig

# ==============================================================
# BLOQUES POR SECCIÓN
# ==============================================================

def ranking_items_subset(df, items, valor, etiqueta_map):
    s = df[items].apply(lambda col: (col == valor).sum())
    s = s[s > 0].sort_values(ascending=False)
    # Devolvemos TODOS (tú decides si recortar a N en el futuro)
    return [{"item": k, "nombre": etiqueta_map.get(k, k), "freq": int(v)} for k, v in s.items()]

def generar_resumen(df, items, etiqueta, mapa_items):
    """Genera resumen IA con análisis y recomendaciones por bloque (subconjunto correcto)."""
    def pct(df, items, v):
        subset = df[items]
        tot = subset.notna().sum().sum()
        if tot == 0:
            return 0.0
        return round(((subset == v).sum().sum() / tot) * 100, 1)

    contexto = {
        "anexo": "Anexo 3 – Acompañamiento Diferenciado",
        "seccion": etiqueta,
        "porcentajes": {
            "no_cumple": pct(df, items, 0),
            "en_desarrollo": pct(df, items, 1),
            "cumple": pct(df, items, 2),
        },
        "top_no_cumple": ranking_items_subset(df, items, 0, mapa_items),
        "top_en_desarrollo": ranking_items_subset(df, items, 1, mapa_items),
    }

    try:
        with st.spinner("Generando resumen ejecutivo..."):
            texto = generate_section_summary(contexto)
            import re
            texto_limpio = re.sub(r"<[^>]+>", "", texto)
            texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
            texto_limpio = texto_limpio.strip()

        st.markdown(
            f"""
            <div style="font-size:16px; line-height:1.6; color:#222; background-color:#f9fafb;
                        padding:15px; border-radius:8px; border-left:5px solid #004C97;">
                {texto_limpio}
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.warning(f"No fue posible generar el resumen para {etiqueta}.")
        st.text(str(e))

# ==============================================================
# SECCIÓN 1 – ROL DEL GESTOR LOCAL
# ==============================================================

st.subheader("Rol del Gestor Local")
generar_resumen(df_filtrado, grupos["Rol del Gestor Local"], "Rol del Gestor Local", mapa_items)
fig1 = generar_grafico(df_filtrado, grupos["Rol del Gestor Local"],
                       "Evaluación del Rol del Gestor Local", mapa_items)
if fig1:
    st.plotly_chart(fig1, use_container_width=True)
st.markdown("---")

# ==============================================================
# SECCIÓN 2 – FACILITADOR(A)
# ==============================================================

st.subheader("Facilitador(a)")
generar_resumen(df_filtrado, grupos["Facilitador(a)"], "Facilitador(a)", mapa_items)
fig2 = generar_grafico(df_filtrado, grupos["Facilitador(a)"], "Evaluación del Facilitador(a)", mapa_items)
if fig2:
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("---")

# ==============================================================
# SECCIÓN 3 – COORDINADOR TÉCNICO ZONAL (CTZ)
# ==============================================================

st.subheader("Coordinador Técnico Zonal (CTZ)")
generar_resumen(df_filtrado, grupos["Coordinador Técnico Zonal (CTZ)"], "Coordinador Técnico Zonal (CTZ)", mapa_items)
fig3 = generar_grafico(df_filtrado, grupos["Coordinador Técnico Zonal (CTZ)"],
                       "Evaluación del Coordinador Técnico Zonal (CTZ)", mapa_items)
if fig3:
    st.plotly_chart(fig3, use_container_width=True)
