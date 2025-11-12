# ==============================================================
# MONITOREO A LAS ACCIONES DE ACOMPAÑAMIENTO DIFERENCIADO
# CON GESTIÓN TERRITORIAL – ANEXO 3 (versión final optimizada)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import yaml
import logging
from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_anexo3_summary  # ⚠️ Asegúrate de definir esta función en utils/llm.py

# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================

st.set_page_config(
    page_title="Anexo 3 – Acompañamiento Diferenciado",
    page_icon="🧩",
    layout="wide"
)
aplicar_estilos()

st.title("Acompañamiento Diferenciado con Gestión Territorial")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# CARGA DE DATOS Y VALIDACIONES
# ==============================================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@st.cache_data(show_spinner=False)
def cargar_y_preparar_datos():
    """Carga datos del Anexo 3 y valida estructura."""
    try:
        data = cargar_datos()
        df = data.get("a3")

        if df is None or df.empty:
            st.warning("No se encontró el archivo `anexo3_consolidado.xlsx` en `/data/processed/`.")
            return None

        if "MES" in df.columns:
            df["MES"] = pd.to_numeric(df["MES"], errors="coerce")

        cols_min = {"UNIDAD_TERRITORIAL", "MES", "SUPERVISOR"}
        if not cols_min.issubset(set(df.columns)):
            faltantes = cols_min - set(df.columns)
            st.error(f"Faltan columnas requeridas: {', '.join(faltantes)}")
            return None

        return df

    except Exception as e:
        st.error(f"❌ Error al cargar datos: {e}")
        logging.exception(e)
        return None

df = cargar_y_preparar_datos()
if df is None:
    st.stop()

# ==============================================================
# CONFIGURACIÓN YAML
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = BASE_DIR / "config" / "settings_anexo3.yaml"

try:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        config_a3 = yaml.safe_load(f)
        mapa_items = config_a3.get("items_nombres", {})
        grupos_items = config_a3.get("grupos_items", {})
except Exception as e:
    st.error(f"❌ Error al leer {YAML_PATH.name}: {e}")
    mapa_items, grupos_items = {}, {}

# ==============================================================
# FILTROS CON PERSISTENCIA
# ==============================================================

if "filters_a3" not in st.session_state:
    st.session_state.filters_a3 = {"ut": [], "mes": [], "sup": []}

col1, col2, col3 = st.columns(3)
with col1:
    ut_sel = st.multiselect("Unidad Territorial:", sorted(df["UNIDAD_TERRITORIAL"].dropna().unique()),
                            default=st.session_state.filters_a3["ut"])
with col2:
    mes_sel = st.multiselect("Mes:", sorted(df["MES"].dropna().unique()),
                             default=st.session_state.filters_a3["mes"])
with col3:
    sup_sel = st.multiselect("Supervisor:", sorted(df["SUPERVISOR"].dropna().unique()),
                             default=st.session_state.filters_a3["sup"])

st.session_state.filters_a3.update({"ut": ut_sel, "mes": mes_sel, "sup": sup_sel})

df_filtrado = df.copy()
if ut_sel:
    df_filtrado = df_filtrado[df_filtrado["UNIDAD_TERRITORIAL"].isin(ut_sel)]
if mes_sel:
    df_filtrado = df_filtrado[df_filtrado["MES"].isin(mes_sel)]
if sup_sel:
    df_filtrado = df_filtrado[df_filtrado["SUPERVISOR"].isin(sup_sel)]

if df_filtrado.empty:
    st.warning("No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================================================
# 🚨 TARJETAS DE ÍTEMS 'NO CUMPLE' – Estilo Anexo 2
# ==============================================================

import streamlit.components.v1 as components

st.markdown("###### Actividades con riesgo o incumplimiento detectado")
cols_items = [c for c in df_filtrado.columns if c.startswith("ITEM_")]

# Calcular frecuencia y porcentaje de 'no cumple'
freq_0 = (df_filtrado[cols_items] == 0).sum()
total_eval = len(df_filtrado)
pct_0 = ((df_filtrado[cols_items] == 0).sum() / total_eval * 100).round(1)
no_cumple = pct_0[pct_0 > 0].sort_values(ascending=False)

if no_cumple.empty:
    st.info("No se registran ítems con valor 'No cumple' en la selección actual.")
else:
    tarjetas_html = """
    <style>
    .grid-container {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 18px;
        padding: 20px 0;
    }
    .tarjeta {
        flex: 0 1 calc(33.333% - 18px);
        box-sizing: border-box;
        border-radius: 10px;
        background-color: #FDEAEA;
        border: 1.5px solid #C62828;
        padding: 18px 20px;
        font-family: 'Source Sans Pro', sans-serif;
        text-align: left;
        min-width: 280px;
        max-width: 340px;
    }
    .tarjeta p {
        margin: 0;
        color: #B71C1C;
        font-weight: 700;
        font-size: 17px;
        line-height: 1.4;
    }
    .tarjeta .porcentaje {
        display: block;
        margin-top: 10px;
        font-size: 13px;
        font-weight: 700;
        color: #5C0000;
    }
    @media (max-width: 1000px) {
        .tarjeta { flex: 0 1 calc(45% - 18px); }
    }
    @media (max-width: 600px) {
        .tarjeta { flex: 0 1 100%; }
    }
    </style>

    <div class="grid-container">
    """

    for item, porcentaje in no_cumple.items():
        nombre = mapa_items.get(item, item)
        freq = int(freq_0[item])
        tarjetas_html += f"""
        <div class="tarjeta">
            <p>{nombre}</p>
            <span class="porcentaje">{freq} de {total_eval} fichas ({porcentaje}%) con 'No cumple'</span>
        </div>
        """

    tarjetas_html += "</div>"
    components.html(tarjetas_html, height=500, scrolling=False)

# ==============================================================
# 💬 RESUMEN AUTOMÁTICO (IA)
# ==============================================================

cols_items = [c for c in df_filtrado.columns if c.startswith("ITEM_")]
df_items = df_filtrado[cols_items].copy()
valores = df_items.values.flatten()
valores = valores[~pd.isna(valores)]

total_validos = int(len(valores))
total_0 = int((valores == 0).sum())
total_1 = int((valores == 1).sum())
total_2 = int((valores == 2).sum())

contexto_llm = {
    "total_registros": len(df_filtrado),
    "porcentajes": {
        "no_cumple": round(total_0 / total_validos * 100, 1) if total_validos else 0,
        "en_desarrollo": round(total_1 / total_validos * 100, 1) if total_validos else 0,
        "cumple": round(total_2 / total_validos * 100, 1) if total_validos else 0
    },
    "filtros": {
        "unidad_territorial": ut_sel or "todas",
        "mes": mes_sel or "todos",
        "supervisor": sup_sel or "todos"
    }
}

try:
    with st.spinner("Generando resumen analítico..."):
        texto = generate_anexo3_summary(contexto_llm)
        st.markdown(
            f"""
            <div style="margin-top:25px; font-size:15.5px; line-height:1.7;
            color:#333; font-family:'Source Sans Pro',sans-serif;">{texto}</div>
            """,
            unsafe_allow_html=True
        )
except Exception as e:
    st.warning("No fue posible generar el resumen automático.")
    st.text(str(e))

st.markdown("<br><hr style='border:0.5px solid #ddd;margin:25px 0;'>", unsafe_allow_html=True)

# ==============================================================
# 🔸 MAPA DE CALOR DE ÍTEMS
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
