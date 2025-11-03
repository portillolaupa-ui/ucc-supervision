import pandas as pd

def normalizar_anexo2(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.upper() for c in df.columns]
    rename_map = {
        "REGION": "Región",
        "UNIDAD_TERRITORIAL": "Unidad Territorial",
        "DISTRITO": "Distrito",
        "SUPERVISOR": "Supervisor",
        "FECHA_SUPERVISIÓN": "Fecha Supervisión",
        "PORCENTAJE": "Puntaje (%)",
    }
    for k, v in rename_map.items():
        if k in df.columns:
            df.rename(columns={k: v}, inplace=True)
    if "Puntaje (%)" not in df.columns:
        for alt in ["PORCENTAJE", "PUNTAJE", "PUNTAJE(%)", "PUNTAJE %"]:
            if alt in df.columns:
                df["Puntaje (%)"] = pd.to_numeric(df[alt], errors="coerce")
                break
    return df
