# ==============================================================
# DASHBOARD BASE – Versión Institucional UCC 2025
# ==============================================================

import streamlit as st
from pathlib import Path
from utils.style import aplicar_estilos

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = BASE_DIR / "config" / "settings_general.yaml"
DATA_DIR = BASE_DIR / "data" / "processed"

st.set_page_config(
    page_title="Dashboard UCC – Supervisión y Monitoreo",
    page_icon="📊",
    layout="wide"
)

# ==============================================================
# 🎨 APLICAR ESTILO INSTITUCIONAL
# ==============================================================

aplicar_estilos()

# ==============================================================
# 🏷️ CABECERA PRINCIPAL
# ==============================================================

st.title("Dashboard UCC – Supervisión y Monitoreo")
st.caption("Unidad de Cumplimiento de Corresponsabilidades – MIDIS Perú")
st.markdown("---")

from utils.loaders import cargar_datos, mostrar_diagnostico

st.subheader("🧭 Carga de Datos")
data = cargar_datos()
mostrar_diagnostico()

# ==============================================================
# 🧭 CONTENIDO TEMPORAL
# ==============================================================

st.info("🚧 Este es el inicio del dashboard base. Aquí se integrarán las páginas y la carga de datos.")
st.write("Ruta de trabajo actual:", str(BASE_DIR))
