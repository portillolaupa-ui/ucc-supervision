from pathlib import Path
import pandas as pd
import yaml
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

@st.cache_data(ttl=3600)
def cargar_datos():
    rutas = {
        "a2": DATA_DIR / "anexo2_consolidado.xlsx",
        "a3_ctz": DATA_DIR / "anexo3_monitoreo_ctz_consolidado.xlsx",
        "a3_fac": DATA_DIR / "anexo3_facilitador_externo_consolidado.xlsx",
        "a3_rol": DATA_DIR / "anexo3_rol_del_gestor_local_consolidado.xlsx",
        "a4": DATA_DIR / "anexo4_consolidado.xlsx",
        "a5": DATA_DIR / "anexo5_consolidado.xlsx",
    }
    data = {}
    for k, v in rutas.items():
        try:
            data[k] = pd.read_excel(v)
        except Exception as e:
            st.warning(f"No se pudo cargar {v.name}: {e}")
    return data

def cargar_yaml(path: Path):
    if not path.exists():
        st.warning(f"No existe el archivo: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
