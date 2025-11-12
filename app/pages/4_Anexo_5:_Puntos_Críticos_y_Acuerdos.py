# ==============================================================
# SEGUIMIENTO DE ACUERDOS Y COMPROMISOS – ANEXO 5
# MIDIS | UCC 2025 – Panel de gestión operativo
# ==============================================================

import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import yaml
from datetime import datetime, timedelta

from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_anexo5_summary

# --------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------------------
st.set_page_config(
    page_title="Anexo 5 – Seguimiento de Acuerdos",
    page_icon="🗂️",
    layout="wide"
)
aplicar_estilos()

st.title("Seguimiento de Acuerdos y Compromisos")
st.markdown("<br>", unsafe_allow_html=True)

# --------------------------------------------------------------
# CARGA DE DATOS
# --------------------------------------------------------------
data = cargar_datos()
df_raw = data.get("a5")
if df_raw is None:
    st.warning("⚠️ No se encontró el archivo `anexo5_consolidado.xlsx` en `/data/processed/`.")
    st.stop()

# Trabajamos sobre una copia
df = df_raw.copy()

# --------------------------------------------------------------
# NORMALIZACIÓN DE COLUMNAS Y TIPOS
# --------------------------------------------------------------
# Asegura existencia de columnas clave con nombres exactos
esperadas = [
    "AÑO","MES","REGION","UNIDAD_TERRITORIAL","DISTRITO","SUPERVISOR","FECHA_SUPERVISIÓN",
    "PUNTOS_CRITICOS","ACUERDOS_MEJORA","RESPONSABLE","PLAZO_DÍAS","FECHA_LÍMITE"
]
faltantes = [c for c in esperadas if c not in df.columns]
if faltantes:
    st.error(f"Faltan columnas en Anexo 5: {faltantes}")
    st.stop()

# Tipos
df["PLAZO_DÍAS"] = pd.to_numeric(df["PLAZO_DÍAS"], errors="coerce")
df["FECHA_SUPERVISIÓN"] = pd.to_datetime(df["FECHA_SUPERVISIÓN"], errors="coerce", dayfirst=True)
df["FECHA_LÍMITE"] = pd.to_datetime(df["FECHA_LÍMITE"], errors="coerce", dayfirst=True)

# Columnas operativas (si no existen en archivo, las creamos)
if "MEDIO_VERIFICACION" not in df.columns:
    df["MEDIO_VERIFICACION"] = ""   # texto o URL
if "CUMPLIMIENTO" not in df.columns:
    df["CUMPLIMIENTO"] = ""         # '✅ Cumplido' si hay medio

# Día de referencia: hoy (para servidores con tz diferente, se puede fijar tz local)
hoy = pd.Timestamp(datetime.now().date())

# Cálculo de días restantes
df["DIAS_RESTANTES"] = (df["FECHA_LÍMITE"] - hoy).dt.days
df.loc[df["FECHA_LÍMITE"].isna(), "DIAS_RESTANTES"] = np.nan

# Marcado de cumplido por medio de verificación
df["CUMPLIMIENTO"] = np.where(df["MEDIO_VERIFICACION"].astype(str).str.strip() != "", "✅ Cumplido", "")

# Estado SLA
def clasificar_estado(row) -> str:
    # Si está cumplido, prioriza ese estado
    if str(row.get("CUMPLIMIENTO", "")).strip() == "✅ Cumplido":
        return "Cumplido"
    # Sin fecha
    if pd.isna(row.get("DIAS_RESTANTES")):
        return "Sin fecha"
    dias = row["DIAS_RESTANTES"]
    if dias < 0:
        return "Vencido"
    elif 0 <= dias <= 3:
        return "Por vencer"
    elif 4 <= dias <= 10:
        return "En curso"
    elif dias > 10:
        return "Con holgura"
    return "Sin fecha"

df["ESTADO"] = df.apply(clasificar_estado, axis=1)

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

df_f = df.copy()
if ut_sel:
    df_f = df_f[df_f["UNIDAD_TERRITORIAL"].isin(ut_sel)]
if mes_sel:
    df_f = df_f[df_f["MES"].isin(mes_sel)]
if sup_sel:
    df_f = df_f[df_f["SUPERVISOR"].isin(sup_sel)]

if df_f.empty:
    st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# --------------------------------------------------------------
# KPI EJECUTIVOS – TARJETAS POR SUPERVISOR (% VENCIDOS)
# --------------------------------------------------------------
def cards_por_supervisor(df_in: pd.DataFrame):
    # Tomamos sólo acuerdos no cumplidos (para % vencidos), los cumplidos no cuentan como vencidos.
    base = df_in.copy()
    # Totales por supervisor
    tot = base.groupby("SUPERVISOR").size().rename("total")
    # Vencidos (no cumplidos)
    ven = base[(base["ESTADO"] == "Vencido")].groupby("SUPERVISOR").size().rename("vencidos")
    kpi = pd.concat([tot, ven], axis=1).fillna(0)
    kpi["% vencidos"] = np.where(kpi["total"] > 0, (kpi["vencidos"] / kpi["total"] * 100).round(1), 0.0)
    kpi = kpi.sort_values("% vencidos", ascending=False).reset_index()

    if kpi.empty:
        st.info("No hay supervisores para mostrar KPI.")
        return

    # Tarjetas responsivas (de 3 en 3)
    n = len(kpi)
    cols_per_row = 3
    for i in range(0, n, cols_per_row):
        cols = st.columns(cols_per_row)
        fila = kpi.iloc[i:i+cols_per_row]
        for j, (_, row) in enumerate(fila.iterrows()):
            sup = row["SUPERVISOR"]
            pct = row["% vencidos"]
            total = int(row["total"])
            # color por riesgo
            if pct < 20:
                borde = "#2E7D32"  # verde
            elif pct <= 50:
                borde = "#FBC02D"  # ámbar
            else:
                borde = "#C62828"  # rojo

            with cols[j]:
                st.markdown(
                    f"""
                    <div style="
                        background-color:#f9fafb; padding:16px; border-radius:12px;
                        border-left:6px solid {borde};
                        box-shadow:0 1px 3px rgba(0,0,0,0.08);">
                        <div style="font-size:13px; color:#003A70; font-weight:600;">{sup}</div>
                        <div style="font-size:26px; font-weight:700; color:#003A70; margin-top:4px;">
                            {pct}%
                        </div>
                        <div style="font-size:12px; color:#37474F;">% de acuerdos vencidos</div>
                        <div style="font-size:12px; color:#607D8B; margin-top:6px;">
                            Total de acuerdos: <b>{total}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

cards_por_supervisor(df_f)
st.markdown("---")

# ==============================================================
# 💬 ANÁLISIS AUTOMÁTICO ASISTIDO POR IA
# ==============================================================

contexto_llm = {
    "unidad_territorial": ut_sel or "todas",
    "mes": mes_sel or "todos",
    "supervisor": sup_sel or "todos",
    "acuerdos": df_f["ACUERDOS_MEJORA"].dropna().tolist(),
    "puntos_criticos": df_f["PUNTOS_CRITICOS"].dropna().tolist(),
    "responsables": df_f["RESPONSABLE"].dropna().tolist(),

}

try:
    with st.spinner("Analizando acuerdos y puntos críticos..."):
        texto = generate_anexo5_summary(contexto_llm)
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
    st.warning("No fue posible generar el análisis automático.")
    st.text(str(e))

st.markdown("<br><hr style='border:0.5px solid #ddd;margin:25px 0;'>", unsafe_allow_html=True)

# --------------------------------------------------------------
# TABLA OPERATIVA – CUMPLIMIENTO CON CHECK Y COLOR DE VENCIDOS
# --------------------------------------------------------------
st.subheader("Tabla operativa de acuerdos")

vista_cols = [
    "UNIDAD_TERRITORIAL", "DISTRITO", "SUPERVISOR",
    "ACUERDOS_MEJORA", "RESPONSABLE", "FECHA_LÍMITE", "ESTADO"
]

df_tabla = df_f[vista_cols].copy()
df_tabla["FECHA_LÍMITE"] = pd.to_datetime(df_tabla["FECHA_LÍMITE"], errors="coerce").dt.date

# Agregar columna editable tipo check para cumplimiento
if "cumplidos" not in st.session_state:
    st.session_state.cumplidos = {
        i: (df_f.loc[i, "ESTADO"] == "Cumplido")
        for i in df_tabla.index
    }

tabla_editable = df_tabla.copy()
tabla_editable["Cumplido"] = [
    st.session_state.cumplidos.get(i, False) for i in df_tabla.index
]

# Editor interactivo con checkbox
tabla_editable = st.data_editor(
    tabla_editable,
    column_config={
        "UNIDAD_TERRITORIAL": st.column_config.TextColumn("UT", disabled=True),
        "DISTRITO": st.column_config.TextColumn("Distrito", disabled=True),
        "SUPERVISOR": st.column_config.TextColumn("Supervisor", disabled=True),
        "ACUERDOS_MEJORA": st.column_config.TextColumn("Acuerdo", disabled=True),
        "RESPONSABLE": st.column_config.TextColumn("Responsable", disabled=True),
        "FECHA_LÍMITE": st.column_config.DateColumn("Fecha límite", disabled=True),
        "ESTADO": st.column_config.TextColumn("Estado", disabled=True),
        "Cumplido": st.column_config.CheckboxColumn("Cumplido"),
    },
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="tabla_acuerdos"
)

# Sincronizar estado de cumplimiento
for i, row in tabla_editable.iterrows():
    if row["Cumplido"]:
        df_tabla.loc[i, "ESTADO"] = "Cumplido"
        st.session_state.cumplidos[i] = True
    else:
        st.session_state.cumplidos[i] = False

# Guardar versión actual para descarga
df_tabla["Cumplido"] = [
    "✅ Cumplido" if st.session_state.cumplidos.get(i, False) else "" for i in df_tabla.index
]

st.download_button(
    label="⬇️ Descargar vista actual (CSV)",
    data=df_tabla.to_csv(index=False).encode("utf-8"),
    file_name="anexo5_seguimiento.csv",
    mime="text/csv"
)
