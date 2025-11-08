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

st.title("Acompañamiento al Hogar con Gestión Territorial")
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
            st.warning("⚠️ No se encontró el archivo `anexo2_consolidado.xlsx` en `/data/processed/`.")
            return None

        # Convertir tipos una sola vez
        if "MES" in df.columns:
            df["MES"] = pd.to_numeric(df["MES"], errors="coerce")

        # Validar columnas esenciales
        cols_min = {"UNIDAD_TERRITORIAL", "MES", "SUPERVISOR"}
        if not cols_min.issubset(set(df.columns)):
            faltantes = cols_min - set(df.columns)
            st.error(f"❌ Faltan columnas requeridas: {', '.join(faltantes)}")
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
    st.warning("⚠️ No hay registros que coincidan con los filtros seleccionados.")
    st.stop()

# ==============================================================
# 🚨 TARJETAS DE ÍTEMS 'NO CUMPLE' – ALERTAS OPERATIVAS
# ==============================================================

import streamlit.components.v1 as components

st.markdown("### 🚨 Actividades con riesgo o incumplimiento detectado")
cols_items = [f"ITEM_{i}" for i in range(1, 21)]

# Calcular frecuencia y porcentaje de 'no cumple'
freq_0 = (df_filtrado[cols_items] == 0).sum()
total_eval = len(df_filtrado)
pct_0 = ((df_filtrado[cols_items] == 0).sum() / total_eval * 100).round(1)
no_cumple = pct_0[pct_0 > 0].sort_values(ascending=False)

if no_cumple.empty:
    st.info("✅ No se registran ítems con valor 'No cumple' en la selección actual.")
else:
    def color_fondo(p):
        if p >= 40:
            return "#FFEBEE"  # rojo claro
        elif p >= 20:
            return "#FFF8E1"  # amarillo claro
        else:
            return "#FFFDE7"  # beige claro

    def color_borde(p):
        if p >= 40:
            return "#C62828"  # rojo fuerte
        elif p >= 20:
            return "#F57C00"  # naranja
        else:
            return "#FBC02D"  # amarillo

    tarjetas_html = """
    <style>
    .carousel-container {
        position: relative;
        display: flex;
        align-items: center;
    }
    .scroll-container {
        display: flex;
        overflow-x: auto;
        gap: 18px;
        scroll-behavior: smooth;
        padding: 10px 0 14px 0;
        scrollbar-color: #004C97 #E8EEF5;
        scrollbar-width: thin;
    }
    .tarjeta {
        flex: 0 0 auto;
        border-radius: 10px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        min-width: 300px;
        max-width: 330px;
        padding: 18px 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        font-family: 'Source Sans Pro', sans-serif;
    }
    .tarjeta:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .tarjeta h4 {
        margin: 0 0 6px 0;
        color: #C62828;
        font-size: 13px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .tarjeta h4::before {
        content: "⚠️";
        font-size: 13px;
    }
    .tarjeta p {
        margin: 0;
        color: #2C2C2C;
        font-weight: 600;
        font-size: 18px;
        line-height: 1.4;
    }
    .tarjeta .porcentaje {
        display: block;
        margin-top: 12px;
        font-size: 13px;
        font-weight: 800;
        color: #B71C1C;
    }
    .tarjeta .responsable {
        display: block;
        margin-top: 6px;
        font-size: 13px;
        font-weight: 600;
        color: #004C97;
    }
    .nav-btn {
        position: absolute;
        top: 40%;
        transform: translateY(-50%);
        background-color: rgba(0, 76, 151, 0.1);
        color: #004C97;
        border: none;
        border-radius: 50%;
        width: 34px;
        height: 34px;
        font-size: 18px;
        cursor: pointer;
        opacity: 0.7;
        transition: all 0.2s ease;
        z-index: 10;
    }
    .nav-btn:hover {
        opacity: 1;
        background-color: rgba(0, 76, 151, 0.25);
    }
    .prev-btn { left: -6px; }
    .next-btn { right: -6px; }
    </style>

    <div class="carousel-container">
        <button class="nav-btn prev-btn" onclick="scrollTarjetas(-1)">&#10094;</button>
        <div id="scrollContainer" class="scroll-container">
    """

    for item, porcentaje in no_cumple.items():
        nombre = mapa_items.get(item, item)
        grupo = obtener_grupo(item)
        fondo = color_fondo(porcentaje)
        borde = color_borde(porcentaje)
        freq = int(freq_0[item])

        tarjetas_html += f"""
        <div class="tarjeta" style="background-color:{fondo};border-left:6px solid {borde};">
            <h4>
                Ítem en riesgo
                <span class="responsable-inline"> | {grupo}</span>
            </h4>
            <p>{nombre}</p>
            <span class="porcentaje">{freq} de {total_eval} fichas ({porcentaje}%) registró incumplimiento en este ítem</span>
        </div>
        """

    tarjetas_html += """
        </div>
        <button class="nav-btn next-btn" onclick="scrollTarjetas(1)">&#10095;</button>
    </div>

    <script>
    const scrollContainer = document.getElementById("scrollContainer");
    function scrollTarjetas(direction) {
        const scrollAmount = 340;
        scrollContainer.scrollBy({ left: scrollAmount * direction, behavior: 'smooth' });
    }

    // Ajuste automático de altura para Streamlit
    const observer = new ResizeObserver(entries => {
      const height = document.body.scrollHeight;
      window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:resize", height: height}, "*");
    });
    observer.observe(document.body);
    </script>
    """

    components.html(tarjetas_html, height=220)

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
# 📈 EVOLUCIÓN MENSUAL DEL % DE "NO CUMPLE" POR ÍTEM + IA
# ==============================================================

st.markdown("### 📈 Evolución mensual y recomendaciones operativas")

# Disposición en columnas: gráfico (izquierda) + resumen IA (derecha)
col_izq, col_der = st.columns([2.2, 1], gap="large")

with col_izq:
    if not no_cumple.empty:
        mapa_meses = {
            1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
            7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
        }

        # Asegurar que MES sea numérico
        df_filtrado["MES"] = pd.to_numeric(df_filtrado["MES"], errors="coerce")
        meses_disponibles = sorted(df_filtrado["MES"].dropna().unique())

        if not meses_disponibles:
            st.info("⚠️ No hay datos válidos de meses numéricos para graficar.")
        else:
            x_vals = [mapa_meses.get(int(m), str(m)) for m in meses_disponibles]
            fig_line = go.Figure()

            for it in no_cumple.index:
                serie = []
                for mes in meses_disponibles:
                    df_mes = df_filtrado[df_filtrado["MES"] == mes]
                    total_validos = df_mes[it].notna().sum()
                    pct0 = ((df_mes[it] == 0).sum() / total_validos * 100) if total_validos else None
                    serie.append(round(pct0, 1) if pct0 is not None else None)

                nombre_largo = mapa_items.get(it, it)
                fig_line.add_trace(go.Scatter(
                    x=x_vals, y=serie, mode="lines+markers",
                    name=f"{it}: {nombre_largo[:40]}{'…' if len(nombre_largo) > 40 else ''}",
                    hovertemplate="<b>%{x}</b><br>%{y:.1f}% 'No cumple'<extra></extra>"
                ))

            fig_line.update_layout(
                title="Evolución mensual del % de 'No cumple' por ítem (mostrar/ocultar desde la leyenda)",
                xaxis=dict(title="Mes", tickangle=0, showgrid=True, gridcolor="#ECEFF1"),
                yaxis=dict(title="% No cumple", range=[0, 100], showgrid=True, gridcolor="#ECEFF1"),
                plot_bgcolor="#FFFFFF",
                paper_bgcolor="#FFFFFF",
                font=dict(size=12, color="#003A70"),
                title_font=dict(size=16, color="#003A70"),
                legend_title_text="Ítems",
                margin=dict(t=60, b=40, l=70, r=40),
                height=480,
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.25,   # posición debajo del gráfico
                    xanchor="center",
                    x=0.5
                )
            )

            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("✅ No hay datos de 'No cumple' para graficar.")

with col_der:
    st.markdown("#### 💡 Recomendaciones operativas inmediatas")
    try:
        with st.spinner("Generando resumen ejecutivo..."):
            texto = generate_anexo2_summary(contexto_llm)
            import re

            # Limpieza del texto generado
            texto_limpio = re.sub(r"</?(?:s|b|i|u|em|strong|br|p|span|div)[^>]*>", "", texto)
            texto_limpio = re.sub(r"<[^>]+>", "", texto_limpio)
            texto_limpio = re.sub(r"\[[^\]]+\]", "", texto_limpio)
            texto_html = texto_limpio.replace("\\n", "<br>")

            # Mostrar en tarjeta
            st.markdown(
                f"""
                <div style="background:#F9FAFB; padding:16px; border-radius:10px; 
                            border-left:6px solid #004C97; font-size:15px; line-height:1.6; color:#1C1C1C;">
                    {texto_html}
                </div>
                """,
                unsafe_allow_html=True
            )
    except Exception as e:
        st.warning("⚠️ No fue posible generar el resumen automático.")
        st.text(str(e))
