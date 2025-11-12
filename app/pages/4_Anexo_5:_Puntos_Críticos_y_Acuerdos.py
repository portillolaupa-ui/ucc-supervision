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
from utils.llm import generate_section_insight

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

# --------------------------------------------------------------
# IA – ANÁLISIS E INTERPRETACIÓN (sin hallazgos)
# --------------------------------------------------------------
# Construimos contexto con agregados de gestión (no PII, no texto crudo)
def contexto_acuerdos(df_in: pd.DataFrame) -> dict:
    conteo_estado = df_in["ESTADO"].value_counts().to_dict()
    # Top supervisores por % vencidos
    base = df_in.copy()
    tot = base.groupby("SUPERVISOR").size().rename("total")
    ven = base[(base["ESTADO"] == "Vencido")].groupby("SUPERVISOR").size().rename("vencidos")
    kpi = pd.concat([tot, ven], axis=1).fillna(0)
    kpi["pct_vencidos"] = np.where(kpi["total"] > 0, (kpi["vencidos"] / kpi["total"] * 100).round(1), 0.0)
    top_sup = kpi.sort_values("pct_vencidos", ascending=False).head(5).reset_index()
    top_sup_list = [{"supervisor": r["SUPERVISOR"], "pct_vencidos": float(r["pct_vencidos"]), "total": int(r["total"])} for _, r in top_sup.iterrows()]

    # Top UT por vencidos
    ut_v = base[base["ESTADO"] == "Vencido"].groupby("UNIDAD_TERRITORIAL").size().sort_values(ascending=False).head(5)
    top_ut_list = [{"ut": k, "vencidos": int(v)} for k, v in ut_v.items()]

    # Próximos 15 días
    prox = base[(~base["FECHA_LÍMITE"].isna()) & (base["DIAS_RESTANTES"] >= 0) & (base["DIAS_RESTANTES"] <= 15)]
    proximos_15 = int(len(prox))

    return {
        "anexo": "Anexo 5 – Seguimiento de Acuerdos",
        "seccion": "Análisis e interpretación",
        "modo": "analisis",
        "sla": conteo_estado,
        "top_supervisores_riesgo": top_sup_list,
        "top_ut_vencidos": top_ut_list,
        "proximos_15_dias": proximos_15
    }

try:
    ctx_analisis = contexto_acuerdos(df_f)
    with st.spinner("Generando análisis e interpretación..."):
        texto_analisis = generate_section_insight(ctx_analisis)
    # Limpieza mínima
    import re
    texto_analisis = re.sub(r"<[^>]+>", "", texto_analisis)
    texto_analisis = re.sub(r"\[[^\]]+\]", "", texto_analisis).strip()

    st.subheader("Análisis e interpretación")
    st.markdown(
        f"""
        <div style="font-size:16px; line-height:1.6; color:#222; background-color:#f9fafb;
                    padding:15px; border-radius:8px; border-left:5px solid #004C97;">
            {texto_analisis}
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.warning("No fue posible generar el análisis automático.")
    st.text(str(e))

# --------------------------------------------------------------
# IA – RECOMENDACIONES (corto y mediano plazo)
# --------------------------------------------------------------
def contexto_recomendaciones(df_in: pd.DataFrame) -> dict:
    # Reutilizamos algunos agregados para orientar recomendaciones
    conteo_estado = df_in["ESTADO"].value_counts().to_dict()
    return {
        "anexo": "Anexo 5 – Seguimiento de Acuerdos",
        "seccion": "Recomendaciones",
        "modo": "recomendaciones",
        "sla": conteo_estado
    }

try:
    ctx_reco = contexto_recomendaciones(df_f)
    with st.spinner("Generando recomendaciones..."):
        texto_reco = generate_section_insight(ctx_reco)
    import re
    texto_reco = re.sub(r"<[^>]+>", "", texto_reco)
    texto_reco = re.sub(r"\[[^\]]+\]", "", texto_reco).strip()

    st.subheader("Recomendaciones a corto y mediano plazo")
    st.markdown(
        f"""
        <div style="font-size:16px; line-height:1.6; color:#222; background-color:#f9fafb;
                    padding:15px; border-radius:8px; border-left:5px solid #007ACC;">
            {texto_reco}
        </div>
        """,
        unsafe_allow_html=True
    )
except Exception as e:
    st.warning("No fue posible generar las recomendaciones automáticas.")
    st.text(str(e))

st.markdown("---")

# --------------------------------------------------------------
# VISUALIZACIÓN 1: HEATMAP UT × ESTADO
# --------------------------------------------------------------
st.subheader("Mapa de calor: Unidad Territorial × Estado")
heat_df = df_f.pivot_table(index="UNIDAD_TERRITORIAL", columns="ESTADO", values="AÑO", aggfunc="count", fill_value=0)

# Asegurar el orden de columnas de estado
estado_cols = ["Vencido", "Por vencer", "En curso", "Con holgura", "Cumplido", "Sin fecha"]
for c in estado_cols:
    if c not in heat_df.columns:
        heat_df[c] = 0
heat_df = heat_df[estado_cols]

fig_heat = go.Figure(data=go.Heatmap(
    z=heat_df.values,
    x=heat_df.columns.tolist(),
    y=heat_df.index.tolist(),
    colorscale="YlOrRd",
    colorbar=dict(title="N° acuerdos")
))
fig_heat.update_layout(
    xaxis_title="Estado",
    yaxis_title="Unidad Territorial",
    plot_bgcolor="#FFFFFF",
    paper_bgcolor="#FFFFFF",
    margin=dict(t=40, b=40, l=80, r=40),
    height=480
)
st.plotly_chart(fig_heat, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------
# VISUALIZACIÓN 2: TIMELINE (GANTT) – PRÓXIMOS 15 DÍAS
# --------------------------------------------------------------
st.subheader("Timeline: acuerdos con plazo en los próximos 15 días")
df_gantt = df_f[(~df_f["FECHA_LÍMITE"].isna()) & (df_f["DIAS_RESTANTES"] >= 0) & (df_f["DIAS_RESTANTES"] <= 15)].copy()

if df_gantt.empty:
    st.info("No hay acuerdos con vencimiento en los próximos 15 días.")
else:
    gantt = df_gantt.copy()
    gantt["Inicio"] = hoy
    gantt["Fin"] = gantt["FECHA_LÍMITE"]
    # Etiqueta lateral (puedes alternar por RESPONSABLE)
    gantt["Recurso"] = gantt["SUPERVISOR"]

    color_map = {
        "Vencido": "#C62828",
        "Por vencer": "#F57C00",
        "En curso": "#FBC02D",
        "Con holgura": "#388E3C",
        "Cumplido": "#2E7D32",
        "Sin fecha": "#9E9E9E"
    }

    fig_gantt = px.timeline(
        gantt,
        x_start="Inicio", x_end="Fin",
        y="Recurso",
        color="ESTADO",
        hover_data=["UNIDAD_TERRITORIAL", "DISTRITO", "ACUERDOS_MEJORA", "RESPONSABLE", "FECHA_LÍMITE"],
        color_discrete_map=color_map
    )
    fig_gantt.update_yaxes(autorange="reversed")
    fig_gantt.update_layout(
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(t=40, b=40, l=80, r=40),
        height=520
    )
    st.plotly_chart(fig_gantt, use_container_width=True)

st.markdown("---")

# --------------------------------------------------------------
# TABLA OPERATIVA – EDITABLE
# --------------------------------------------------------------
st.subheader("Tabla operativa de acuerdos")

# Vista reducida con columnas solicitadas
vista_cols = [
    "UNIDAD_TERRITORIAL", "DISTRITO", "SUPERVISOR", "ACUERDOS_MEJORA",
    "RESPONSABLE", "FECHA_LÍMITE", "MEDIO_VERIFICACION", "ESTADO", "CUMPLIMIENTO"
]
tabla = df_f[vista_cols].copy()

# Editor (permite editar Medio de verificación); Estado y Cumplimiento solo lectura
# Nota: st.data_editor requiere Streamlit >= 1.22 para column_config
editable_cols = {"MEDIO_VERIFICACION": True}
column_config = {
    "UNIDAD_TERRITORIAL": st.column_config.TextColumn("UT", disabled=True),
    "DISTRITO": st.column_config.TextColumn("Distrito", disabled=True),
    "SUPERVISOR": st.column_config.TextColumn("Supervisor", disabled=True),
    "ACUERDOS_MEJORA": st.column_config.TextColumn("Acuerdo", disabled=True),
    "RESPONSABLE": st.column_config.TextColumn("Responsable", disabled=True),
    "FECHA_LÍMITE": st.column_config.DatetimeColumn("Fecha límite", disabled=True),
    "MEDIO_VERIFICACION": st.column_config.TextColumn("Medio de verificación (URL o nota)"),
    "ESTADO": st.column_config.TextColumn("Estado", disabled=True),
    "CUMPLIMIENTO": st.column_config.TextColumn("Cumplimiento", disabled=True),
}

# Persistencia temporal en sesión
session_key = "a5_tabla_edit"
if session_key not in st.session_state:
    st.session_state[session_key] = tabla.copy()

edited = st.data_editor(
    st.session_state[session_key],
    column_config=column_config,
    num_rows="fixed",
    use_container_width=True
)

# Si cambió algo, recalculamos Cumplimiento y Estado para toda la vista filtrada
if not edited.equals(st.session_state[session_key]):
    tmp = edited.copy()
    # Reglas: si hay medio -> Cumplido
    tmp["CUMPLIMIENTO"] = np.where(tmp["MEDIO_VERIFICACION"].astype(str).str.strip() != "", "✅ Cumplido", tmp["CUMPLIMIENTO"])

    # Volcar cambios a df_f y df original (sobre los índices coincidentes)
    # Emparejamos por varias columnas clave para identificar registros únicos
    merge_keys = ["UNIDAD_TERRITORIAL","DISTRITO","SUPERVISOR","ACUERDOS_MEJORA","RESPONSABLE","FECHA_LÍMITE"]
    df_f = df_f.drop(columns=["MEDIO_VERIFICACION","CUMPLIMIENTO","ESTADO"], errors="ignore")
    df_f = df_f.merge(
        tmp[merge_keys + ["MEDIO_VERIFICACION","CUMPLIMIENTO"]],
        on=merge_keys, how="left"
    )

    # Recalcular estado en df_f (sólo vista filtrada)
    def _estado_row(r):
        if str(r.get("CUMPLIMIENTO","")).strip() == "✅ Cumplido":
            return "Cumplido"
        if pd.isna(r.get("DIAS_RESTANTES")):
            return "Sin fecha"
        d = r["DIAS_RESTANTES"]
        if d < 0: return "Vencido"
        if 0 <= d <= 3: return "Por vencer"
        if 4 <= d <= 10: return "En curso"
        if d > 10: return "Con holgura"
        return "Sin fecha"

    df_f["ESTADO"] = df_f.apply(_estado_row, axis=1)

    # Propagar a la sesión del editor
    # Reconstruir tabla visible a partir de df_f
    tabla = df_f[vista_cols].copy()
    st.session_state[session_key] = tabla.copy()
    # Forzar refresco visual de KPIs/Gráficos (sencillo: re-ejecuta la app en el siguiente run)
    st.toast("Actualizado: KPIs y gráficos se recalcularán con los cambios.", icon="✅")

# Botón de descarga de la vista actual
st.download_button(
    label="Descargar vista (CSV)",
    data=st.session_state[session_key].to_csv(index=False).encode("utf-8"),
    file_name="acuerdos_vista_filtrada.csv",
    mime="text/csv"
)