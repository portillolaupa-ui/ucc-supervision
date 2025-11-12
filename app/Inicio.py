# ==============================================================
# DASHBOARD BASE – Versión Institucional UCC 2025
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from utils.style import aplicar_estilos
import datetime
st.caption(f"Última actualización: {datetime.date.today():%d/%m/%Y}")


# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Dashboard UCC – Supervisión y Monitoreo",
    page_icon="📊",
    layout="wide"
)

aplicar_estilos()

# ==============================================================
# 🧩 CLASIFICADOR POR ANEXO
# ==============================================================

def clasificar_anexo(anexo, col_sum):
    if anexo == 2:
        if col_sum <= 10: return "DEFICIENTE"
        elif col_sum <= 20: return "REGULAR"
        elif col_sum <= 30: return "BUENO"
        else: return "EXCELENTE"

    elif anexo == 3:
        if col_sum <= 7: return "DEFICIENTE"
        elif col_sum <= 16: return "REGULAR"
        elif col_sum <= 25: return "BUENO"
        else: return "EXCELENTE"

    elif anexo == 4:
        if col_sum <= 8: return "DEFICIENTE"
        elif col_sum <= 18: return "REGULAR"
        elif col_sum <= 26: return "BUENO"
        else: return "EXCELENTE"
    else:
        return "Sin dato"

# ==============================================================
# 🎨 COLORES INSTITUCIONALES
# ==============================================================

COLORES = {
    "DEFICIENTE": "#C62828",
    "REGULAR": "#F9A825",
    "BUENO": "#2E7D32",
    "EXCELENTE": "#1565C0",
    "Sin dato": "#9E9E9E"
}

COLOR_ANEXOS = {
    "Anexo 2 – Acompañamiento con Gestión Territorial": "#1565C0",
    "Anexo 3 – Acompañamiento Diferenciado": "#2E7D32",
    "Anexo 4 – Intervenciones Complementarias": "#EF6C00"
}

# ==============================================================
# 🧠 FUNCIÓN DE CARGA CACHEADA
# ==============================================================

@st.cache_data(show_spinner=False)
def cargar_excel(nombre):
    return pd.read_excel(DATA_DIR / nombre)

# ==============================================================
# 📊 FUNCIÓN GENERAL DE GRÁFICO
# ==============================================================

def graficar(df, anexo, col_puntaje, titulo, normalizar=False, max_valor=None):
    """Genera gráfico horizontal por UT, coloreado por categoría"""
    resumen = (
        df.groupby("UNIDAD_TERRITORIAL")[col_puntaje]
        .mean()
        .reset_index()
        .sort_values(by=col_puntaje, ascending=False)
    )

    if normalizar and max_valor:
        resumen["Porcentaje"] = (resumen[col_puntaje] / max_valor) * 100
        x_var = "Porcentaje"
        x_label = "Cumplimiento promedio (%)"
    else:
        x_var = col_puntaje
        x_label = "Puntaje promedio"

    resumen["Categoria"] = resumen[col_puntaje].apply(lambda x: clasificar_anexo(anexo, x))

    fig = px.bar(
        resumen,
        x=x_var,
        y="UNIDAD_TERRITORIAL",
        color="Categoria",
        color_discrete_map=COLORES,
        orientation="h",
        text_auto=".1f",
        hover_data={"UNIDAD_TERRITORIAL": True, x_var: True, "Categoria": True}
    )

    fig.update_layout(
        title_text=titulo,
        xaxis_title=x_label,
        yaxis_title="Unidad Territorial",
        plot_bgcolor="white",
        bargap=0.3,
        height=450,
        margin=dict(l=80, r=40, t=60, b=40),
        title_font=dict(size=18, color="#333333"),
        legend_title_text="Evaluación"
    )
    st.plotly_chart(fig, use_container_width=True)

# ==============================================================
# 🏷️ TÍTULO PRINCIPAL DE LA PÁGINA
# ==============================================================

st.markdown(
    """
    <h2 style='text-align:center; color:#1A237E; font-weight:800; margin-bottom:10px;'>
        Sistematización de Supervisiones Territoriales – UCC 2025
    </h1>
    <hr style='border: 1px solid #1A237E; margin-top:10px; margin-bottom:30px;'>
    """,
    unsafe_allow_html=True
)


# ==============================================================
# 📊 COMPARATIVO GLOBAL ENTRE ANEXOS (porcentaje + evaluación visible)
# ==============================================================

try:
    df2 = cargar_excel("anexo2_consolidado.xlsx")
    df3 = cargar_excel("anexo3_consolidado.xlsx")
    df4 = cargar_excel("anexo4_consolidado.xlsx")

    # Selección y renombrado uniforme
    g2 = df2.groupby("UNIDAD_TERRITORIAL")[["PORCENTAJE"]].mean().reset_index()
    g2["Anexo"] = "Anexo 2 – Acompañamiento con Gestión Territorial"
    g2["Evaluacion"] = df2.groupby("UNIDAD_TERRITORIAL")["EVALUACION"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Sin dato").values

    g3 = df3.groupby("UNIDAD_TERRITORIAL")[["PORCENTAJE_TOTAL"]].mean().reset_index()
    g3.rename(columns={"PORCENTAJE_TOTAL": "PORCENTAJE"}, inplace=True)
    g3["Anexo"] = "Anexo 3 – Acompañamiento Diferenciado"
    g3["Evaluacion"] = df3.groupby("UNIDAD_TERRITORIAL")["EVALUACION_TOTAL"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Sin dato").values

    g4 = df4.groupby("UNIDAD_TERRITORIAL")[["PORCENTAJE_TOTAL"]].mean().reset_index()
    g4.rename(columns={"PORCENTAJE_TOTAL": "PORCENTAJE"}, inplace=True)
    g4["Anexo"] = "Anexo 4 – Intervenciones Complementarias"
    g4["Evaluacion"] = df4.groupby("UNIDAD_TERRITORIAL")["EVALUACION_TOTAL"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Sin dato").values

    # Unir, escalar y ordenar
    df_global = pd.concat([g2, g3, g4], ignore_index=True)
    df_global["PORCENTAJE"] = (df_global["PORCENTAJE"] * 100).round(1)
    df_global["TextoEtiqueta"] = df_global.apply(lambda r: f"{r['PORCENTAJE']:.1f}% – {r['Evaluacion']}", axis=1)
    df_global = df_global.sort_values(by="PORCENTAJE", ascending=False)

    # Gráfico comparativo
    fig = px.bar(
        df_global,
        x="PORCENTAJE",
        y="UNIDAD_TERRITORIAL",
        color="Anexo",
        text="TextoEtiqueta",  # 🔹 muestra porcentaje + evaluación
        barmode="group",
        orientation="h",
        hover_data={
            "UNIDAD_TERRITORIAL": True,
            "PORCENTAJE": ":.1f",
            "Evaluacion": True,
            "Anexo": True
        },
        color_discrete_map=COLOR_ANEXOS
    )

    fig.update_layout(
        title_text="Comparativo Global entre Anexos",
        xaxis_title="Cumplimiento promedio (%)",
        yaxis_title="Unidad Territorial",
        plot_bgcolor="white",
        bargap=0.3,
        height=550,
        margin=dict(l=80, r=40, t=60, b=40),
        title_font=dict(size=18, color="#333333"),
        legend_title_text="Ficha de supervisión",
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.warning(f"No se pudo generar el comparativo global: {e}")


# ==============================================================
# INTERPRETACION IA
# ==============================================================

from utils.llm import generar_interpretacion_grafico

placeholder_ia = st.empty()

with st.spinner("Generando interpretación automática..."):
    try:
        interpretacion = generar_interpretacion_grafico(df_global, "Comparativo Global entre Anexos")
        placeholder_ia.markdown(f"<p style='color:#424242;font-style:italic;'>💬 {interpretacion}</p>", unsafe_allow_html=True)
    except Exception as e:
        placeholder_ia.warning(f"No se pudo generar la interpretación automática: {e}")


# ==============================================================
# 🔍 DETALLES ANEXO 3 Y 4 (porcentajes y evaluación reales)
# ==============================================================

# --- Detalle Anexo 3 ---
try:
    pestañas3 = st.tabs(["GEL", "Facilitador Local", "CTZ"])

    detalles_anexo3 = [
        ("PORCENTAJE_GEL", "EVALUACION_GEL", "Anexo 3 – Evaluación GEL"),
        ("PORCENTAJE_FAC", "EVALUACION_FAC", "Anexo 3 – Evaluación Facilitador Local"),
        ("PORCENTAJE_CTZ", "EVALUACION_CTZ", "Anexo 3 – Evaluación CTZ")
    ]

    for (col_pct, col_eval, titulo), tab in zip(detalles_anexo3, pestañas3):
        with tab:
            if col_pct in df3.columns and col_eval in df3.columns:
                resumen = (
                    df3.groupby("UNIDAD_TERRITORIAL")[[col_pct]]
                    .mean()
                    .reset_index()
                    .sort_values(by=col_pct, ascending=False)
                )
                resumen[col_pct] = (resumen[col_pct] * 100).round(1)
                resumen["Evaluacion"] = (
                    df3.groupby("UNIDAD_TERRITORIAL")[col_eval]
                    .agg(lambda x: x.mode()[0] if not x.mode().empty else "Sin dato")
                    .values
                )
                resumen["Etiqueta"] = resumen.apply(
                    lambda r: f"{r[col_pct]:.1f}% – {r['Evaluacion']}", axis=1
                )

                fig = px.bar(
                    resumen,
                    x=col_pct,
                    y="UNIDAD_TERRITORIAL",
                    color="Evaluacion",
                    text="Etiqueta",
                    orientation="h",
                    color_discrete_map=COLORES,
                    hover_data={
                        "UNIDAD_TERRITORIAL": True,
                        col_pct: ":.1f",
                        "Evaluacion": True
                    }
                )

                fig.update_layout(
                    title_text=titulo,
                    xaxis_title="Cumplimiento promedio (%)",
                    yaxis_title="Unidad Territorial",
                    plot_bgcolor="white",
                    bargap=0.3,
                    height=450,
                    margin=dict(l=80, r=40, t=60, b=40),
                    title_font=dict(size=18, color="#333333"),
                    legend_title_text="Evaluación",
                    uniformtext_minsize=8,
                    uniformtext_mode='hide'
                )
                st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"No se pudo generar el detalle del Anexo 3: {e}")


# --- Detalle Anexo 4 ---
try:
    pestañas4 = st.tabs(["Adolescentes", "Independencia Económica"])

    detalles_anexo4 = [
        ("PORCENTAJE_ADOLES", "EVALUACION_ADOLES", "Anexo 4 – Evaluación Adolescentes"),
        ("PORCENTAJE_INDEP", "EVALUACION_INDEP", "Anexo 4 – Evaluación Independencia Económica")
    ]

    for (col_pct, col_eval, titulo), tab in zip(detalles_anexo4, pestañas4):
        with tab:
            if col_pct in df4.columns and col_eval in df4.columns:
                resumen = (
                    df4[["UNIDAD_TERRITORIAL", col_pct, col_eval]]
                    .dropna(subset=[col_pct])  # evita filas vacías
                    .groupby("UNIDAD_TERRITORIAL", as_index=False)
                    .agg({col_pct: "mean", col_eval: "first"})  # toma el valor de evaluación existente
                    .sort_values(by=col_pct, ascending=False)
                )
                resumen[col_pct] = (resumen[col_pct] * 100).round(1)
                resumen["Etiqueta"] = resumen.apply(
                    lambda r: f"{r[col_pct]:.1f}% – {r[col_eval]}", axis=1
                )

                fig = px.bar(
                    resumen,
                    x=col_pct,
                    y="UNIDAD_TERRITORIAL",
                    color=col_eval,
                    text="Etiqueta",
                    orientation="h",
                    color_discrete_map=COLORES,
                    hover_data={
                        "UNIDAD_TERRITORIAL": True,
                        col_pct: ":.1f",
                        col_eval: True
                    }
                )

                fig.update_layout(
                    title_text=titulo,
                    xaxis_title="Cumplimiento promedio (%)",
                    yaxis_title="Unidad Territorial",
                    plot_bgcolor="white",
                    bargap=0.3,
                    height=450,
                    margin=dict(l=80, r=40, t=60, b=40),
                    title_font=dict(size=18, color="#333333"),
                    legend_title_text="Evaluación",
                    uniformtext_minsize=8,
                    uniformtext_mode='hide'
                )
                st.plotly_chart(fig, use_container_width=True)
except Exception as e:
    st.warning(f"No se pudo generar el detalle del Anexo 4: {e}")
