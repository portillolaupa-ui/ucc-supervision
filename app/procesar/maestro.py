# =============================================
# maestro.py — Orquestador de procesamiento UCC
# =============================================
import os
import subprocess
from pathlib import Path
from datetime import datetime
import sys

# =============================================
# ⚙️ CONFIGURACIÓN DE RUTAS
# =============================================
BASE_DIR = Path(__file__).resolve().parents[1]
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"

ETL_SCRIPTS = [
    "procesar_anexo2.py",
    "procesar_anexo3.py",
    "procesar_anexo4.py",
    "procesar_anexo5.py",
]

# =============================================
# 🧩 FUNCIONES AUXILIARES
# =============================================
def log(mensaje, tipo="INFO"):
    hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    simbolo = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(tipo, "")
    print(f"{simbolo} [{hora}] {mensaje}")

def ejecutar_script(script_name):
    """Ejecuta un script Python y captura su salida."""
    script_path = APP_DIR / script_name
    if not script_path.exists():
        log(f"No se encontró el script: {script_path}", "ERROR")
        return False

    log(f"Ejecutando {script_name}...", "INFO")
    try:
        resultado = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            check=True
        )
        log(f"{script_name} completado correctamente ✅", "OK")
        print(resultado.stdout)
        return True
    except subprocess.CalledProcessError as e:
        log(f"Error ejecutando {script_name}: {e}", "ERROR")
        print(e.stdout)
        print(e.stderr)
        return False

# =============================================
# 🚀 EJECUCIÓN PRINCIPAL
# =============================================
if __name__ == "__main__":
    log("INICIO DEL PROCESAMIENTO AUTOMÁTICO DE ANEXOS UCC", "INFO")
    log(f"Directorio base: {BASE_DIR}", "INFO")

    if not DATA_DIR.exists():
        log(f"No existe la carpeta de datos: {DATA_DIR}", "ERROR")
        sys.exit(1)

    # Crear carpetas de salida si no existen
    (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)

    total_ok = 0
    for script in ETL_SCRIPTS:
        ok = ejecutar_script(script)
        if ok:
            total_ok += 1

    log(f"{total_ok}/{len(ETL_SCRIPTS)} anexos procesados correctamente.", "OK")

    if total_ok == len(ETL_SCRIPTS):
        log("🎯 Todos los anexos fueron procesados exitosamente. Archivos listos en /data/processed", "OK")
    else:
        log("⚠️ Algunos anexos tuvieron errores. Revisa los mensajes anteriores.", "WARN")

    log("FIN DEL PROCESAMIENTO AUTOMÁTICO DE ANEXOS", "INFO")
