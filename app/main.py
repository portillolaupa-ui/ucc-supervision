# ==============================================================
# DASHBOARD BASE – Versión Institucional UCC 2025
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from utils.style import aplicar_estilos

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
    "Anexo 2 – Acompañamiento": "#1565C0",
    "Anexo 3 – Sesiones Diferenciadas": "#2E7D32",
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
# 📊 COMPARATIVO GLOBAL ENTRE ANEXOS (porcentaje + evaluación visible)
# ==============================================================

try:
    df2 = cargar_excel("anexo2_consolidado.xlsx")
    df3 = cargar_excel("anexo3_consolidado.xlsx")
    df4 = cargar_excel("anexo4_consolidado.xlsx")

    # Selección y renombrado uniforme
    g2 = df2.groupby("UNIDAD_TERRITORIAL")[["PORCENTAJE"]].mean().reset_index()
    g2["Anexo"] = "Anexo 2 – Acompañamiento"
    g2["Evaluacion"] = df2.groupby("UNIDAD_TERRITORIAL")["EVALUACION"].agg(lambda x: x.mode()[0] if not x.mode().empty else "Sin dato").values

    g3 = df3.groupby("UNIDAD_TERRITORIAL")[["PORCENTAJE_TOTAL"]].mean().reset_index()
    g3.rename(columns={"PORCENTAJE_TOTAL": "PORCENTAJE"}, inplace=True)
    g3["Anexo"] = "Anexo 3 – Sesiones Diferenciadas"
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
# 🔍 DETALLES ANEXO 3 Y 4 (pestañas directas, sin expansión)
# ==============================================================

# --- Detalle Anexo 3 ---
try:
    pestañas3 = st.tabs(["GEL", "Facilitador Local", "CTZ"])
    columnas_anexo3 = [
        ("SUMA_TOTAL_GEL", "Anexo 3 – Evaluación GEL"),
        ("SUMA_TOTAL_FAC", "Anexo 3 – Evaluación Facilitador Local"),
        ("SUMA_TOTAL_CTZ", "Anexo 3 – Evaluación CTZ")
    ]
    for (col, titulo), tab in zip(columnas_anexo3, pestañas3):
        with tab:
            if col in df3.columns:
                graficar(df3, 3, col, titulo)
except Exception as e:
    st.warning(f"No se pudo generar el detalle del Anexo 3: {e}")

# --- Detalle Anexo 4 ---
try:
    pestañas4 = st.tabs(["Adolescentes", "Independencia Económica"])
    columnas_anexo4 = [
        ("SUMA_TOTAL_ADOLES", "Anexo 4 – Evaluación Adolescentes"),
        ("SUMA_TOTAL_INDEP", "Anexo 4 – Evaluación Independencia Económica")
    ]
    for (col, titulo), tab in zip(columnas_anexo4, pestañas4):
        with tab:
            if col in df4.columns:
                # Normalizado a 100%
                graficar(df4, 4, col, titulo, normalizar=True, max_valor=100)
except Exception as e:
    st.warning(f"No se pudo generar el detalle del Anexo 4: {e}")
