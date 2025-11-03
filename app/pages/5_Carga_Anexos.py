import streamlit as st
from pathlib import Path
import subprocess, sys, datetime
from utils.style import aplicar_estilo

aplicar_estilo()
st.title("Administración de Archivos y Cargas de Anexos")
st.caption("Carga, procesamiento y revisión del historial de anexos.")

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data" / "processed"

subtab1, subtab2 = st.tabs(["Cargar Nuevos Anexos", "Historial de Cargas"])

with subtab1:
    password = st.text_input("Clave de acceso", type="password")
    if password != st.secrets.get("admin_password", "ucc2025"):
        st.warning("Acceso restringido. Ingrese la clave correcta para continuar.")
        st.stop()

    tipo_anexo = st.selectbox("Tipo de anexo:", ["Anexo 2", "Anexo 3", "Anexo 4", "Anexo 5"])
    region = st.text_input("Región:", placeholder="Ejemplo: PIURA").upper()
    mes = st.text_input("Mes:", placeholder="Ejemplo: OCTUBRE").upper()
    anio = st.text_input("Año:", value=str(datetime.datetime.now().year))
    archivo = st.file_uploader("Seleccionar archivo Excel (.xlsx)", type=["xlsx"])

    if archivo and st.button("Subir y procesar"):
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
        script_path = BASE_DIR / app / scripts[tipo_anexo]

        with st.spinner(f"Procesando {tipo_anexo} ({region}, {mes} {anio})..."):
            result = subprocess.run([sys.executable, str(script_path)],
                                    capture_output=True, text=True)
            if result.returncode == 0:
                st.success(f"{tipo_anexo} procesado correctamente.")
                st.cache_data.clear()
                st.toast("Caché limpiado y dashboard actualizado.")
                st.rerun()
            else:
                st.error("Error procesando el archivo.")
                st.text(result.stderr)

with subtab2:
    log_path = DATA_DIR / "uploads_log.csv"
    if log_path.exists():
        import pandas as pd
        log_df = pd.read_csv(log_path)
        st.dataframe(log_df)
        st.download_button("Descargar registro", data=log_df.to_csv(index=False),
                           file_name="historial_cargas.csv", mime="text/csv")
    else:
        st.info("Aún no existen registros de carga de anexos.")
