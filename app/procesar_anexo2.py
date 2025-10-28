import pandas as pd
from openpyxl import load_workbook
from pathlib import Path

# ============================================================
# 📁 CONFIGURACIÓN DE RUTAS
# ============================================================
CARPETA = Path(__file__).resolve().parent / "../data/raw/2025/OCTUBRE/LA_LIBERTAD"
CARPETA = CARPETA.resolve()
ARCHIVOS = [CARPETA / "2025_OCTUBRE_LA_LIBERTAD_SUPERVISION_ANEXO_2.xlsx"]

# ============================================================
# 🧩 FUNCIÓN PARA EXTRAER DATOS DE UNA FICHA
# ============================================================
def procesar_ficha(ruta_excel):
    wb = load_workbook(ruta_excel, data_only=True)
    hoja = wb.active

    # --- Metadatos generales ---
    ut = hoja["C2"].value or ""
    distrito = hoja["F2"].value or ""
    supervisor = hoja["C3"].value or ""
    fecha = hoja["C4"].value or ""

    # --- Extraer valores de ítems (filas esperadas) ---
    items = {}
    for fila in hoja.iter_rows(min_row=8, max_row=35, min_col=3, max_col=7, values_only=True):
        pregunta = str(fila[0]).strip() if fila[0] else None
        valores = fila[1:]  # columnas D:E:F:G (0,1,2,NA)
        if pregunta:
            # Tomar el valor no nulo
            valor = next((v for v in valores if v not in [None, ""]), None)
            items[pregunta[:120]] = valor  # recorte a 120 caracteres máx

    # --- Extraer totales (últimas filas) ---
    subtotal = hoja["F33"].value
    total = hoja["F34"].value
    porcentaje = hoja["G34"].value

    # --- Consolidar ---
    data = {
        "Unidad Territorial": ut,
        "Distrito": distrito,
        "Supervisor": supervisor,
        "Fecha Supervisión": fecha,
        "Subtotal": subtotal,
        "Total": total,
        "Porcentaje": porcentaje,
        **items
    }

    return data

# ============================================================
# 🚀 PROCESAR TODAS LAS FICHAS
# ============================================================
registros = []
for archivo in ARCHIVOS:
    try:
        registros.append(procesar_ficha(archivo))
    except Exception as e:
        print(f"❌ Error procesando {archivo.name}: {e}")

# ============================================================
# 💾 CREAR DATAFRAME CONSOLIDADO
# ============================================================
df = pd.DataFrame(registros)
print(f"✅ Se procesaron {len(df)} fichas.")
print(df.head())

# Guardar a Excel
df.to_excel("consolidado_supervision.xlsx", index=False)
print("📊 Archivo generado: consolidado_supervision.xlsx")
