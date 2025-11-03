# ==============================================================
# DASHBOARD UCC 2025 – Versión Ejecutiva Institucional MIDIS (Paleta Armonizada)
# ==============================================================

import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.express as px
import datetime
import subprocess
import sys

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Dashboard UCC - Supervisión y Monitoreo",
    page_icon="📊",
    layout="wide"
)

# ==============================================================
# 🎨 ESTILO VISUAL INSTITUCIONAL
# ==============================================================

st.markdown("""
<style>
/* --- Fondo general --- */
.main {
    background-color: #F7F9FB;
    padding: 0 2rem;
}

/* --- Encabezados --- */
h1, h2, h3 {
    color: #004C97;
    font-weight: 700;
}

/* --- Tarjetas (métricas) --- */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #FFFFFF 60%, #E3F2FD 100%);
    padding: 25px;
    border-radius: 18px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
    text-align: center;
    border-left: 6px solid #004C97;
    transition: all 0.25s ease-in-out;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0px 8px 20px rgba(0,0,0,0.15);
}
div[data-testid="stMetricValue"] {
    color: #004C97;
    font-size: 1.8rem;
    font-weight: 700;
}
div[data-testid="stMetricLabel"] {
    color: #444;
    font-size: 1rem;
}

/* --- Sidebar --- */
[data-testid="stSidebar"] {
    background-color: #E8EEF5;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: #003A70;
}

/* --- Botones --- */
div.stButton>button {
    background: linear-gradient(90deg, #004C97, #1976D2);
    color: white;
    border-radius: 10px;
    border: none;
    padding: 0.6rem 1.3rem;
    font-weight: 600;
}
div.stButton>button:hover {
    background: linear-gradient(90deg, #003B78, #1259A0);
}

/* --- Tablas --- */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    border: 1px solid #E5EAF0;
}

/* --- Mensajes tipo alerta --- */
.stAlert>div {
    border-radius: 10px;
}

/* --- Footer oculto --- */
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==============================================================
# CABECERA
# ==============================================================

st.title("Dashboard de Supervisión y Monitoreo – UCC")
st.caption("Unidad de Cumplimiento de Corresponsabilidades – Programa JUNTOS | Ministerio de Desarrollo e Inclusión Social del Perú (MIDIS)")
st.markdown("---")

# ==============================================================
# CARGA DE DATOS
# ==============================================================

@st.cache_data(ttl=3600, show_spinner="Cargando datos...")
def cargar_datos():
    data = {}
    rutas = {
        "a2": DATA_DIR / "anexo2_consolidado.xlsx",
        "a3_ctz": DATA_DIR / "anexo3_monitoreo_ctz_consolidado.xlsx",
        "a3_fac": DATA_DIR / "anexo3_facilitador_externo_consolidado.xlsx",
        "a3_rol": DATA_DIR / "anexo3_rol_del_gestor_local_consolidado.xlsx",
        "a4": DATA_DIR / "anexo4_consolidado.xlsx",
        "a5": DATA_DIR / "anexo5_consolidado.xlsx",
    }

    for clave, ruta in rutas.items():
        try:
            data[clave] = pd.read_excel(ruta)
        except FileNotFoundError:
            st.warning(f"⚠️ Archivo no encontrado: {ruta.name}")
        except Exception as e:
            st.error(f"Error al cargar {ruta.name}: {e}")
    return data

data = cargar_datos()

# ==============================================================
# SIDEBAR
# ==============================================================

st.sidebar.title("📍 Navegación")
menu = st.sidebar.radio(
    "Seleccione una sección:",
    [
        "Visión General",
        "Acompañamiento al Hogar",
        "Acompañamiento Diferenciado",
        "Intervenciones Complementarias",
        "Seguimiento de Acuerdos",
        "Análisis",
        "Carga de Anexos"
    ]
)

# ==============================================================
# VISIÓN GENERAL
# ==============================================================

if menu == "Visión General":
    st.header("Panorama Nacional")
    st.caption("Resumen consolidado del desempeño de los componentes supervisados (Anexos 2–4).")

    try:
        total_ut = len(data["a2"]["Unidad Territorial"].unique())
        total_fichas = sum(len(df) for df in data.values() if df is not None)
        prom_a2 = round(data["a2"]["Puntaje (%)"].mean(), 1)
        prom_a4 = round(data["a4"]["Puntaje (%)"].mean(), 1)

        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades Territoriales Supervisadas", total_ut)
        col2.metric("Fichas Procesadas", total_fichas)
        col3.metric("Promedio AFA (%)", f"{prom_a2}")

        resumen = pd.DataFrame({
            "Componente": ["Acompañamiento al Hogar", "Intervenciones Complementarias"],
            "Promedio Puntaje (%)": [prom_a2, prom_a4]
        })
        fig = px.bar(
            resumen,
            x="Componente",
            y="Promedio Puntaje (%)",
            text="Promedio Puntaje (%)",
            color="Componente",
            color_discrete_sequence=["#004C97", "#00ADEF"],
            title="Promedio de Desempeño por Componente"
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(size=13, color="#003A70"),
            title_font=dict(size=18, color="#003A70"),
            margin=dict(t=60, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"No se pudo generar el resumen: {e}")

    st.markdown("---")
    st.subheader("Actualización de Base de Datos")
    if st.button("Ejecutar procesamiento maestro"):
        maestro_path = Path(__file__).resolve().parent / "maestro.py"
        with st.spinner("Ejecutando procesamiento completo..."):
            result = subprocess.run([sys.executable, str(maestro_path)],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                st.success("Procesamiento completado correctamente.")
                st.cache_data.clear()
                st.toast("Caché limpiado y dashboard actualizado.")
                st.rerun()
            else:
                st.error("Error en el procesamiento maestro.")
                st.text(result.stderr)

# ==============================================================
# ANEXO 2 – ACOMPAÑAMIENTO AL HOGAR
# ==============================================================

elif menu == "Acompañamiento al Hogar":
    st.header("Anexo 2 – Acompañamiento al Hogar con Gestión Territorial")
    df = data.get("a2")
    if df is None:
        st.warning("No se encontró el archivo del Anexo 2.")
    else:
        regiones = st.multiselect("Filtrar por Región:", df["Región"].unique())
        if regiones:
            df = df[df["Región"].isin(regiones)]

        prom = df.groupby("Región")["Puntaje (%)"].mean().reset_index()
        fig = px.bar(
            prom,
            x="Puntaje (%)",
            y="Región",
            orientation="h",
            color="Puntaje (%)",
            color_continuous_scale="Blues",
            title="Promedio de Puntaje por Región"
        )
        fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver datos detallados"):
            st.dataframe(df)

# ==============================================================
# ANEXO 3 – ACOMPAÑAMIENTO DIFERENCIADO
# ==============================================================

elif menu == "Acompañamiento Diferenciado":
    st.header("Anexo 3 – Acompañamiento Diferenciado (Vida sin Anemia)")
    tab1, tab2, tab3 = st.tabs(["Monitoreo CTZ", "Facilitador Externo", "Rol del Gestor Local"])

    with tab1:
        df_ctz = data.get("a3_ctz")
        if df_ctz is not None:
            st.metric("Registros CTZ", len(df_ctz))
            st.dataframe(df_ctz.head(10))
        else:
            st.warning("No hay datos de Monitoreo CTZ disponibles.")

    with tab2:
        df_fac = data.get("a3_fac")
        if df_fac is not None:
            st.metric("Registros Facilitadores", len(df_fac))
            st.dataframe(df_fac.head(10))
        else:
            st.warning("No hay datos de Facilitadores disponibles.")

    with tab3:
        df_rol = data.get("a3_rol")
        if df_rol is not None:
            st.metric("Registros Gestores", len(df_rol))
            st.dataframe(df_rol.head(10))
        else:
            st.warning("No hay datos del Rol del Gestor Local disponibles.")

# ==============================================================
# ANEXO 4 – INTERVENCIONES COMPLEMENTARIAS
# ==============================================================

elif menu == "Intervenciones Complementarias":
    st.header("Anexo 4 – Intervenciones Complementarias")
    df = data.get("a4")
    if df is None:
        st.warning("No se encontró el archivo del Anexo 4.")
    else:
        st.metric("Promedio Puntaje (%)", round(df["Puntaje (%)"].mean(), 1))
        fig = px.box(
            df,
            x="Región",
            y="Puntaje (%)",
            color="Región",
            color_discrete_sequence=px.colors.qualitative.Safe,
            title="Distribución de Puntajes por Región"
        )
        fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver datos detallados"):
            st.dataframe(df)

# ==============================================================
# ANEXO 5 – SEGUIMIENTO DE ACUERDOS
# ==============================================================

elif menu == "Seguimiento de Acuerdos":
    st.header("Anexo 5 – Hallazgos y Acuerdos de Mejora")
    df = data.get("a5")
    if df is None:
        st.warning("No se encontró el archivo del Anexo 5.")
    else:
        regiones = st.multiselect("Filtrar por Unidad Territorial:", df["UNIDAD_TERRITORIAL"].unique())
        if regiones:
            df = df[df["UNIDAD_TERRITORIAL"].isin(regiones)]

        df["PLAZO_DIAS"] = df["PLAZO"].astype(str).str.extract(r"(\d+)").astype(float)
        df["Estado"] = df["PLAZO_DIAS"].apply(
            lambda x: "Cumplido" if pd.notna(x) and x <= 3 else
                      "En curso" if pd.notna(x) and 3 < x <= 7 else
                      "Vencido" if pd.notna(x) and x > 7 else "Sin definir"
        )

        estado_df = df["Estado"].value_counts().reset_index()
        estado_df.columns = ["Estado", "Cantidad"]
        fig = px.bar(
            estado_df,
            x="Cantidad",
            y="Estado",
            orientation="h",
            color="Estado",
            color_discrete_map={
                "Cumplido": "#2E7D32",
                "En curso": "#FBC02D",
                "Vencido": "#D9534F",
                "Sin definir": "#9E9E9E"
            },
            title="Estado de Cumplimiento de Acuerdos"
        )
        fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF")
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Ver detalles de acuerdos"):
            st.dataframe(df)

# ==============================================================
# ANÁLISIS CUALITATIVO
# ==============================================================

elif menu == "Análisis":
    st.header("Análisis Cualitativo de Hallazgos y Acuerdos (Anexo 5)")
    analysis_dir = DATA_DIR.parent / "analysis"
    excel_path = analysis_dir / "anexo5_analisis_cualitativo.xlsx"
    nube_path = analysis_dir / "nube_palabras_anexo5.png"
    temas_html = analysis_dir / "temas_anexo5.html"
    sent_html = analysis_dir / "sentimientos_anexo5.html"

    if not excel_path.exists():
        st.warning("Aún no se ha generado el análisis cualitativo. Ejecute el script correspondiente.")
    else:
        df_ana = pd.read_excel(excel_path)
        st.dataframe(df_ana[["UNIDAD_TERRITORIAL", "tema_label", "sentimiento"]])

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Nube de Palabras")
            if nube_path.exists():
                st.image(str(nube_path), use_column_width=True)
            else:
                st.info("No se encontró la imagen de la nube de palabras.")

        with col2:
            st.subheader("Distribución de Temas")
            if temas_html.exists():
                st.components.v1.html(open(temas_html).read(), height=400)
            else:
                st.info("No se encontró el archivo HTML de temas.")

        st.subheader("Análisis de Sentimiento")
        if sent_html.exists():
            st.components.v1.html(open(sent_html).read(), height=450)
        else:
            st.info("No se encontró el archivo de análisis de sentimiento.")

# ==============================================================
# ADMINISTRACIÓN – CARGA DE ANEXOS
# ==============================================================

elif menu == "Carga de Anexos":
    st.header("Administración de Archivos y Cargas de Anexos")
    st.caption("Carga, procesamiento y revisión del historial de anexos.")

    subtab1, subtab2 = st.tabs(["Cargar Nuevos Anexos", "Historial de Cargas"])

    with subtab1:
        password = st.text_input("Clave de acceso", type="password")
        if password != st.secrets.get("admin_password", "ucc2025"):
            st.warning("Acceso restringido. Ingrese la clave correcta para continuar.")
            st.stop()

        tipo_anexo = st.selectbox("Seleccionar tipo de anexo:", ["Anexo 2", "Anexo 3", "Anexo 4", "Anexo 5"])
        region = st.text_input("Región:", placeholder="Ejemplo: PIURA").upper()
        mes = st.text_input("Mes:", placeholder="Ejemplo: OCTUBRE").upper()
        anio = st.text_input("Año:", value=str(datetime.datetime.now().year))
        archivo = st.file_uploader("Seleccionar archivo Excel (.xlsx)", type=["xlsx"])

        if archivo and st.button("Subir y procesar archivo"):
            try:
                raw_dir = DATA_DIR.parent / "raw" / anio / mes
                raw_dir.mkdir(parents=True, exist_ok=True)
                destino = raw_dir / archivo.name
                with open(destino, "wb") as f:
                    f.write(archivo.getbuffer())
                st.success(f"Archivo guardado en: {destino}")

                scripts = {
                    "Anexo 2": "procesar_anexo2.py",
                    "Anexo 3": "procesar_anexo3.py",
                    "Anexo 4": "procesar_anexo4.py",
                    "Anexo 5": "procesar_anexo5.py",
                }
                script_path = Path(__file__).resolve().parent / scripts[tipo_anexo]

                with st.spinner(f"Procesando {tipo_anexo} ({region}, {mes} {anio})..."):
                    result = subprocess.run([sys.executable, str(script_path)],
                                            capture_output=True, text=True)
                    if result.returncode == 0:
                        st.success(f"{tipo_anexo} procesado correctamente y dashboard actualizado.")
                        st.cache_data.clear()
                        st.toast("Caché limpiado y dashboard actualizado.")
                        st.rerun()
                    else:
                        st.error("Error procesando el archivo.")
                        st.text(result.stderr)

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")

    with subtab2:
        log_path = DATA_DIR / "uploads_log.csv"
        if log_path.exists():
            log_df = pd.read_csv(log_path)
            st.dataframe(log_df)
            st.download_button("Descargar registro", data=log_df.to_csv(index=False),
                               file_name="historial_cargas.csv", mime="text/csv")
        else:
            st.info("Aún no existen registros de carga de anexos.")

# ==============================================================
# FOOTER
# ==============================================================

st.markdown("---")
st.caption("© 2025 | Unidad de Cumplimiento de Corresponsabilidades (UCC) – MIDIS Perú | Elaborado con Streamlit y Plotly.")
