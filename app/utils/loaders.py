# ==============================================================
# 📦 MÓDULO DE CARGA DE DATOS – DASHBOARD UCC
# ==============================================================

from pathlib import Path
import pandas as pd
import streamlit as st
import yaml

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

BASE_DIR = Path(__file__).resolve().parents[2]  # /tu_proyecto
CONFIG_PATH = BASE_DIR / "config" / "settings_general.yaml"
DATA_DIR = BASE_DIR / "data" / "processed"

# ==============================================================
# 📘 FUNCIONES AUXILIARES
# ==============================================================

def leer_configuracion():
    """Lee el archivo YAML de configuración general."""
    if not CONFIG_PATH.exists():
        st.warning(f"⚠️ No se encontró el archivo de configuración: {CONFIG_PATH}")
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        st.error(f"❌ Error al leer settings_general.yaml: {e}")
        return {}

def ttl_cache():
    """Convierte minutos a segundos según la configuración YAML."""
    config = leer_configuracion()
    try:
        minutos = config.get("cache", {}).get("ttl_minutos", 60)
        return int(minutos) * 60
    except Exception:
        return 3600  # valor por defecto

# ==============================================================
# 🧩 CARGA DE ARCHIVOS EXCEL
# ==============================================================

@st.cache_data(ttl=ttl_cache(), show_spinner="Cargando datos procesados...")
def cargar_datos():
    """Carga los 4 anexos desde /data/processed."""
    archivos = {
        "a2": DATA_DIR / "anexo2_consolidado.xlsx",
        "a3": DATA_DIR / "anexo3_consolidado.xlsx",
        "a4": DATA_DIR / "anexo4_consolidado.xlsx",
        "a5": DATA_DIR / "anexo5_consolidado.xlsx",
    }

    data = {}

    for clave, ruta in archivos.items():
        if not ruta.exists():
            st.warning(f"⚠️ No se encontró el archivo: {ruta.name}")
            data[clave] = None
            continue

        try:
            data[clave] = pd.read_excel(ruta)
        except Exception as e:
            st.error(f"❌ Error al cargar {ruta.name}: {e}")
            data[clave] = None

    return data

# ==============================================================
# 🧪 FUNCIÓN DE PRUEBA
# ==============================================================

def mostrar_diagnostico():
    """Muestra rutas de carga y existencia de archivos."""
    st.markdown("### 🔍 Diagnóstico de archivos procesados")
    for clave, ruta in {
        "Anexo 2": DATA_DIR / "anexo2_consolidado.xlsx",
        "Anexo 3": DATA_DIR / "anexo3_consolidado.xlsx",
        "Anexo 4": DATA_DIR / "anexo4_consolidado.xlsx",
        "Anexo 5": DATA_DIR / "anexo5_consolidado.xlsx",
    }.items():
        existe = "✅" if ruta.exists() else "❌"
        st.write(f"{existe} **{clave}** — {ruta.name}")
