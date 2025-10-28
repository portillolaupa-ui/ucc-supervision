# -*- coding: utf-8 -*-
"""
Procesador de Fichas - ANEXO 3 (Seguimiento de Sesiones Educativas)
-------------------------------------------------------------------
- Lee archivos Excel tipo formulario (ANEXO 3)
- Extrae metadatos superiores (Responsable, distrito, fecha, facilitador, etc.)
- Lee bloques de ítems con cabeceras que contienen: Cumple (2), Parcial(1), No cumple (0)
- Mapea la marca a score: 2/1/0 y status: Cumple/Parcialmente/No cumple
- Exporta:
  - anexo3_wide.xlsx  (ancho: 1 fila por ficha)
  - anexo3_long.xlsx  (largo: 1 fila por ítem)

Requisitos:
  pip install pandas openpyxl

Uso:
  # 1) Un solo archivo
  python procesar_anexo3.py --input "LA_LIBERTAD_SUPERVISION_ANEXO_3.xlsx" --outdir "salidas"

  # 2) Carpeta con varios .xlsx
  python procesar_anexo3.py --input "carpeta_fichas" --outdir "salidas"

Notas:
- Ajusta BLOQUES si cambian las posiciones de las filas en otros anexos/plantillas.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
from openpyxl import load_workbook

# =========================
# 🔧 Configuración general
# =========================
# Cabeceras (filas) e ítems (rangos) detectados en tu plantilla
# (header_row, start_row, end_row)
BLOQUES: List[Tuple[int, int, int]] = [
    (8, 9, 14),
    (23, 24, 29),
    (39, 40, 44),
]

# Palabras clave para cabeceras
KEYS_CUMPLE = ("cumple",)
KEYS_PARCIAL = ("parcial",)
KEYS_NOCUMPLE = ("no cumple", "no cumple")  # incluye espacio no-breaking


# =========================
# 🧩 Utilidades
# =========================
def clean_text(x: Any) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    return s if s and s.lower() != "nan" else None


def get_cell(ws, r: int, c: int):
    try:
        return ws.cell(r, c).value
    except Exception:
        return None


def parse_meta(ws) -> Dict[str, str]:
    """
    Extrae metadatos del encabezado (primeras filas), buscando pares "clave: valor".
    """
    meta = {}
    for r in range(1, 20):
        for c in range(1, 8):
            v = get_cell(ws, r, c)
            if isinstance(v, str) and ":" in v:
                left, right = v.split(":", 1)
                k = clean_text(left)
                val = clean_text(right)
                if k and val:
                    meta[k] = val
    return meta


def localizar_columna_por_keywords(ws, header_row: int, keywords: Tuple[str, ...], scan_cols: int = 25) -> int | None:
    """
    Encuentra índice de columna cuya cabecera contenga todas las palabras clave indicadas.
    (Búsqueda flexible por 'in' en minúsculas)
    """
    for c in range(1, scan_cols + 1):
        v = get_cell(ws, header_row, c)
        if isinstance(v, str):
            s = v.lower().replace("\xa0", " ")  # normaliza NBSP
            if all(k in s for k in keywords):
                return c
    return None


def detectar_columnas_estado(ws, header_row: int) -> Tuple[int | None, int | None, int | None]:
    """
    Identifica columnas de Cumple(2), Parcial(1), No cumple(0) en una fila de cabecera dada.
    """
    col_cumple = localizar_columna_por_keywords(ws, header_row, KEYS_CUMPLE)
    col_parcial = localizar_columna_por_keywords(ws, header_row, KEYS_PARCIAL)
    col_nocumple = localizar_columna_por_keywords(ws, header_row, KEYS_NOCUMPLE)
    return col_cumple, col_parcial, col_nocumple


def descripcion_fila(ws, r: int, prefer_col: int = 3, scan_cols: int = 30) -> str:
    """
    Devuelve una descripción del ítem:
    - Intenta la columna 3 (suele ser 'Aspecto a evaluar'/'Actividades')
    - Si está vacía, busca el texto más largo en la fila (excluyendo celdas vacías y cortas)
    """
    desc = clean_text(get_cell(ws, r, prefer_col))
    if desc:
        return desc
    textos: List[str] = []
    for c in range(1, scan_cols + 1):
        v = clean_text(get_cell(ws, r, c))
        if v and len(v) >= 4 and "ítem" not in v.lower():
            textos.append(v)
    if textos:
        # Elige el texto más largo (suele ser la descripción completa)
        return max(textos, key=len)
    return f"Item_fila_{r}"


def leer_bloque(ws, header_row: int, start_row: int, end_row: int, bloque_id: int) -> List[Dict[str, Any]]:
    """
    Lee un bloque de ítems (entre start_row y end_row) mapeando la primera
    columna marcada (cumple/parcial/no cumple) a un score/status.
    """
    col_cumple, col_parcial, col_nocumple = detectar_columnas_estado(ws, header_row)

    results: List[Dict[str, Any]] = []
    for r in range(start_row, end_row + 1):
        desc = descripcion_fila(ws, r)
        v2 = get_cell(ws, r, col_cumple) if col_cumple else None
        v1 = get_cell(ws, r, col_parcial) if col_parcial else None
        v0 = get_cell(ws, r, col_nocumple) if col_nocumple else None

        score = None
        status = None
        # Considera marca si no es None/""/0
        def marcado(x): return (x is not None) and (str(x).strip() != "") and (str(x).strip() != "0")

        if marcado(v2):
            score, status = 2, "Cumple"
        elif marcado(v1):
            score, status = 1, "Parcialmente"
        elif marcado(v0):
            score, status = 0, "No cumple"

        results.append({
            "bloque": bloque_id,
            "fila_excel": r,
            "descripcion": desc,
            "score": score,
            "status": status,
        })
    return results


def procesar_archivo_anexo3(path_xlsx: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Procesa un archivo ANEXO 3 y devuelve (df_wide, df_long)
    df_wide: 1 fila por ficha con metadatos + items como columnas (score)
    df_long: 1 fila por ítem con detalle
    """
    wb = load_workbook(str(path_xlsx), data_only=True)
    ws = wb.active

    meta = parse_meta(ws)

    # Lee todos los bloques declarados
    all_items: List[Dict[str, Any]] = []
    for i, (h, a, b) in enumerate(BLOQUES, start=1):
        items = leer_bloque(ws, header_row=h, start_row=a, end_row=b, bloque_id=i)
        all_items.extend(items)

    # -------- Formato largo
    df_long = pd.DataFrame(all_items)
    df_long.insert(0, "archivo", path_xlsx.name)
    # añade metadatos útiles
    df_long["responsable"] = meta.get("Responsable del seguimiento")
    df_long["comunidad_distrito"] = meta.get("Nombre de la comunidad / distrito")
    df_long["fecha_sesion"] = meta.get("Fecha de la sesión")
    df_long["sesion_observada"] = meta.get("Número y nombre de la Sesión observada")
    df_long["facilitador"] = meta.get("Facilitador(a) local")

    # -------- Formato ancho
    # Una fila por ficha; columnas: metadatos + cada ítem como "Item{n}: descripcion"
    wide_row = {
        "archivo": path_xlsx.name,
        "Responsable del seguimiento": meta.get("Responsable del seguimiento"),
        "Nombre de la comunidad / distrito": meta.get("Nombre de la comunidad / distrito"),
        "Fecha de la sesión": meta.get("Fecha de la sesión"),
        "Número y nombre de la Sesión observada": meta.get("Número y nombre de la Sesión observada"),
        "Facilitador(a) local": meta.get("Facilitador(a) local"),
        "tipo_ficha": "Anexo 3",
    }
    for idx, it in enumerate(all_items, start=1):
        col = f"Item{idx}: {it['descripcion'][:80]}"
        wide_row[col] = it["score"]

    df_wide = pd.DataFrame([wide_row])

    return df_wide, df_long


def es_excel(path: Path) -> bool:
    return path.suffix.lower() in {".xlsx", ".xlsm"}


def recolectar_archivos(input_path: Path) -> List[Path]:
    if input_path.is_dir():
        return sorted([p for p in input_path.glob("*.xlsx") if p.is_file()])
    elif input_path.is_file() and es_excel(input_path):
        return [input_path]
    return []


def main():
    parser = argparse.ArgumentParser(description="Procesar fichas ANEXO 3 a DataFrames (ancho/largo).")
    parser.add_argument("--input", required=True, help="Ruta a archivo .xlsx o carpeta con .xlsx")
    parser.add_argument("--outdir", default="salidas", help="Carpeta de salida (se creará si no existe)")
    args = parser.parse_args()

    in_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    archivos = recolectar_archivos(in_path)
    if not archivos:
        print(f"❌ No se encontraron Excel en: {in_path}")
        return

    all_wide = []
    all_long = []

    for x in archivos:
        try:
            dfw, dfl = procesar_archivo_anexo3(x)
            all_wide.append(dfw)
            all_long.append(dfl)
            print(f"✅ Procesado: {x.name}  | ítems: {len(dfl)}")
        except Exception as e:
            print(f"❌ Error procesando {x.name}: {e}")

    if not all_wide:
        print("⚠️ No se generaron filas (revisa la plantilla o los rangos BLOQUES)")
        return

    df_wide_total = pd.concat(all_wide, ignore_index=True)
    df_long_total = pd.concat(all_long, ignore_index=True)

    out_wide = outdir / "anexo3_wide.xlsx"
    out_long = outdir / "anexo3_long.xlsx"

    df_wide_total.to_excel(out_wide, index=False)
    df_long_total.to_excel(out_long, index=False)

    print(f"📊 Guardado formato ANCHO: {out_wide}")
    print(f"📄 Guardado formato LARGO: {out_long}")


if __name__ == "__main__":
    input_path = Path("data/raw/LA_LIBERTAD/LA_LIBERTAD_SUPERVISION_ANEXO_3.xlsx")
    outdir = Path("data/processed")
    dfw, dfl = procesar_archivo_anexo3(input_path)
    dfw.to_excel(outdir / "anexo3_wide.xlsx", index=False)
    dfl.to_excel(outdir / "anexo3_long.xlsx", index=False)
    print("✅ Procesamiento completado sin argumentos CLI")