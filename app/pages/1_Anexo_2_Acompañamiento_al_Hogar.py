# ==============================================================
# MONITOREO A LAS ACCIONES DE ACOMPAÑAMIENTO AL HOGAR
# CON GESTIÓN TERRITORIAL – ANEXO 2 (versión final optimizada)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import yaml
from utils.loaders import cargar_datos
from utils.style import aplicar_estilos
from utils.llm import generate_anexo2_summary


# ==============================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================

st.set_page_config(
    page_title="Anexo 2 – Acompañamiento al Hogar",
    page_icon="📋",
    layout="wide"
)
aplicar_estilos()

# ==============================================================
# CABECERA
# ==============================================================

st.title("Monitoreo del Acompañamiento al Hogar con Gestión Territorial")
st.markdown("<br>", unsafe_allow_html=True)

# ==============================================================
# CARGA DE DATOS Y VALIDACIONES
# ==============================================================

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@st.cache_data(show_spinner=False)
def cargar_y_preparar_datos():
    """Carga datos procesados, convierte tipos críticos y valida columnas requeridas."""
    try:
        data = cargar_datos()
        df = data.get("a2")

        if df is None or df.empty:
            logging.warning("Archivo anexo2_consolidado.xlsx no encontrado o vacío.")
            st.warning("No se encontró el archivo `anexo2_consolidado.xlsx` en `/data/processed/`.")
            return None

        # Convertir tipos una sola vez
        if "MES" in df.columns:
            df["MES"] = pd.to_numeric(df["MES"], errors="coerce")

        # Validar columnas esenciales
        cols_min = {"UNIDAD_TERRITORIAL", "MES", "SUPERVISOR"}
        if not cols_min.issubset(set(df.columns)):
            faltantes = cols_min - set(df.columns)
            st.error(f"Faltan columnas requeridas: {', '.join(faltantes)}")
            logging.error(f"Columnas faltantes: {faltantes}")
            return None

        logging.info(f"Datos cargados correctamente: {len(df)} registros, {len(df.columns)} columnas.")
        return df

    except Exception as e:
        logging.exception("Error al cargar datos:")
        st.error(f"❌ Error al cargar datos: {e}")
        return None

df = cargar_y_preparar_datos()
if df is None:
    st.stop()

# ==============================================================
# CARGAR CONFIGURACIÓN YAML (nombres, grupos dinámicos)
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
YAML_PATH = BASE_DIR / "config" / "settings_anexo2.yaml"

try:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        config_a2 = yaml.safe_load(f)
        mapa_items = config_a2.get("items_nombres", {})
        grupos_items = config_a2.get("grupos_items", {})
    logging.info("YAML de configuración cargado correctamente.")
except Exception as e:
    st.error(f"❌ Error al leer {YAML_PATH.name}: {e}")
    logging.exception("Error al leer YAML:")
    mapa_items, grupos_items = {}, {}

# ==============================================================
# HELPERS REUTILIZABLES
# ==============================================================

def truncar(texto: str, maxlen: int = 42) -> str:
    """Trunca texto con elipsis para tooltips/etiquetas."""
    if not isinstance(texto, str):
        texto = "" if pd.isna(texto) else str(texto)
    texto = texto.strip()
    return (texto[:maxlen-1] + "…") if len(texto) > maxlen else texto

# Mapa inverso item -> grupo (desde YAML)
item_to_group = {}
for grupo, items in grupos_items.items():
    for it in items:
        item_to_group[it] = grupo

def obtener_grupo(item_key: str) -> str:
    """Obtiene el grupo del ítem desde YAML; fallback si no existe."""
    return item_to_group.get(item_key, "—")


# ==============================================================
# FILTROS CON PERSISTENCIA DE ESTADO
# ==============================================================

# Inicializar sesión si no existe
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

# Actualizar sesión si cambia
st.session_state.filters.update({"ut": ut_sel, "mes": mes_sel, "sup": sup_sel})

# Aplicar filtros
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
# 📊 GRÁFICO COMPARATIVO POR UNIDAD TERRITORIAL
# ==============================================================

# Asegurar que existan las columnas necesarias
if all(col in df_filtrado.columns for col in ["UNIDAD_TERRITORIAL", "PORCENTAJE", "EVALUACION"]):
    # Agrupar por UT y evaluación, calcular promedio de porcentaje
    df_graf = (
        df_filtrado.groupby(["UNIDAD_TERRITORIAL", "EVALUACION"], as_index=False)["PORCENTAJE"]
        .mean()
    )

    # Crear gráfico de barras agrupadas
    fig = go.Figure()

    evaluaciones = df_graf["EVALUACION"].unique()
    colores = {
        "BUENO": "#2E7D32",
        "REGULAR": "#F9A825",
        "DEFICIENTE": "#C62828"
    }

    for eval_ in evaluaciones:
        df_sub = df_graf[df_graf["EVALUACION"] == eval_]
        fig.add_trace(go.Bar(
            x=df_sub["UNIDAD_TERRITORIAL"],
            y=df_sub["PORCENTAJE"],
            name=eval_,
            marker_color=colores.get(eval_, "#90A4AE"),
            text=(df_sub["PORCENTAJE"] * 100).round(1).astype(str) + "%",
            textposition="outside"
        ))

    fig.update_layout(
        barmode="group",
        xaxis_title="Unidad Territorial",
        yaxis_title="Porcentaje de cumplimiento",
        title="Desempeño por Unidad Territorial y resultado",
        template="simple_white",
        height=500,
        legend_title="Evaluación",
        margin=dict(t=70, l=40, r=40, b=70)
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No se encontraron las columnas 'UNIDAD_TERRITORIAL', 'PORCENTAJE' o 'EVALUACION' para generar el gráfico.")

# ==============================================================
# 🚨 TARJETAS DE ÍTEMS 'NO CUMPLE' – ALERTAS OPERATIVAS (versión visual mejorada)
# ==============================================================

import streamlit.components.v1 as components

st.markdown("###### Actividades con riesgo o incumplimiento detectado")
cols_items = [f"ITEM_{i}" for i in range(1, 21)]

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
        justify-content: center;  /* centra las filas */
        gap: 18px;
        padding: 20px 0;
    }
    .tarjeta {
        flex: 0 1 calc(33.333% - 18px); /* tres por fila */
        box-sizing: border-box;
        border-radius: 10px;
        background-color: #FDEAEA; /* rojo claro */
        border: 1.5px solid #C62828; /* borde rojo fuerte */
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
    .tarjeta .grupo {
        display: block;
        margin-top: 8px;
        font-size: 12.5px;
        font-weight: 600;
        color: #7B1C1C;
    }

    /* Responsivo: 2 tarjetas por fila en pantallas medianas */
    @media (max-width: 1000px) {
        .tarjeta {
            flex: 0 1 calc(45% - 18px);
        }
    }

    /* Responsivo: 1 tarjeta por fila en pantallas pequeñas */
    @media (max-width: 600px) {
        .tarjeta {
            flex: 0 1 100%;
        }
    }
    </style>

    <div class="grid-container">
    """

    for item, porcentaje in no_cumple.items():
        nombre = mapa_items.get(item, item)
        grupo = obtener_grupo(item)
        freq = int(freq_0[item])

        tarjetas_html += f"""
        <div class="tarjeta">
            <p>{nombre}</p>
            <span class="porcentaje">{freq} de {total_eval} fichas ({porcentaje}%) con 'No cumple'</span>
            <span class="grupo">Categoría: {grupo}</span>
        </div>
        """

    tarjetas_html += "</div>"

components.html(tarjetas_html, height=210, scrolling=False)

# ==============================================================
# 🧩 CONTEXTO PARA EL RESUMEN AUTOMÁTICO ASISTIDO POR IA
# ==============================================================

cols_items = [f"ITEM_{i}" for i in range(1, 21)]
df_items = df_filtrado[cols_items].copy()

# Calcular totales globales
valores = df_items.values.flatten()
valores = valores[~pd.isna(valores)]
total_validos = int(len(valores))
total_0 = int((valores == 0).sum())
total_1 = int((valores == 1).sum())
total_2 = int((valores == 2).sum())

pct_0 = round((total_0 / total_validos) * 100, 1) if total_validos else 0.0
pct_1 = round((total_1 / total_validos) * 100, 1) if total_validos else 0.0
pct_2 = round((total_2 / total_validos) * 100, 1) if total_validos else 0.0

# Agrupar ítems según YAML (CTZ, Gestor, Hogar, Acompañamiento)
def totales_por_valor(df, items, valor):
    if not items:
        return 0
    subset = df[items]
    return int((subset == valor).sum().sum())

nombres_humanos = {
    "Al CTZ": "las actividades sobre CTZ",
    "Al Gestor Local": "las actividades sobre el Gestor Local",
    "Al Hogar": "las actividades en el Hogar",
    "Durante el Acompañamiento": "las actividades Durante la Visita"
}

resumen_grupos = []
for nombre, items in grupos_items.items():
    resumen_grupos.append({
        "categoria_actividades": nombres_humanos.get(nombre, nombre),
        "total_0": totales_por_valor(df_filtrado, items, 0),
        "total_1": totales_por_valor(df_filtrado, items, 1),
        "total_validos_en_categoria": int(df_filtrado[items].notna().sum().sum())
    })

def ranking_items(df, items, valor, etiqueta_map):
    s = df[items].apply(lambda col: (col == valor).sum())
    s = s[s > 0].sort_values(ascending=False)
    return [
        {"item": k, "nombre": etiqueta_map.get(k, k), "freq": int(v)}
        for k, v in s.items()
    ]

rank_0 = ranking_items(df_filtrado, cols_items, 0, mapa_items)
rank_1 = ranking_items(df_filtrado, cols_items, 1, mapa_items)

contexto_llm = {
    "filtros_aplicados": {
        "unidad_territorial": ut_sel or "todas",
        "mes": mes_sel or "todos",
        "supervisor": sup_sel or "todos",
    },
    "global": {
        "total_registros": int(len(df_filtrado)),
        "total_respuestas_validas": total_validos,
        "porcentajes": {"no_cumple_0": pct_0, "en_desarrollo_1": pct_1, "cumple_2": pct_2}
    },
    "categorias_de_actividades": resumen_grupos,
    "ranking_no_cumple": rank_0,
    "ranking_en_desarrollo": rank_1
}

# ==============================================================
# 💬 RECOMENDACIONES INMEDIATAS (IA) – MOVIDO DE col_der
# ==============================================================

try:
    with st.spinner("Generando recomendaciones operativas..."):
        texto = generate_anexo2_summary(contexto_llm)
        import re

        # Limpieza del texto generado
        texto_limpio = re.sub(r"</?(?:s|b|i|u|em|strong|br|p|span|div)[^>]*>", "", texto)
        texto_limpio = re.sub(r"<[^>]+>", "", texto_limpio)
        texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
        texto_html = texto_limpio.replace("\\n", "<br>")

        st.markdown(
            f"""
            <div style="margin-top:25px; font-size:15.5px; line-height:1.7; color:#333333; font-family:'Source Sans Pro',sans-serif;">
                {texto_html}
            </div>
            """,
            unsafe_allow_html=True
        )

except Exception as e:
    st.warning("No fue posible generar el resumen automático.")
    st.text(str(e))