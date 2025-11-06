import pandas as pd

def _rename_keep(df, mapping):
    for k, v in mapping.items():
        if k in df.columns:
            df.rename(columns={k: v}, inplace=True)

def normalizar_anexo2(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.upper() for c in df.columns]
    mapping = {
        "REGION": "Región",
        "UNIDAD_TERRITORIAL": "Unidad Territorial",
        "DISTRITO": "Distrito",
        "SUPERVISOR": "Supervisor",
        "FECHA_SUPERVISIÓN": "Fecha Supervisión",
        "PORCENTAJE": "Puntaje (%)",
    }
    _rename_keep(df, mapping)
    if "Puntaje (%)" not in df.columns:
        for alt in ["PORCENTAJE", "PUNTAJE", "PUNTAJE(%)", "PUNTAJE %"]:
            if alt in df.columns:
                df["Puntaje (%)"] = pd.to_numeric(df[alt], errors="coerce")
                break
    else:
        df["Puntaje (%)"] = pd.to_numeric(df["Puntaje (%)"], errors="coerce")
    return df

def normalizar_anexo4(df: pd.DataFrame) -> pd.DataFrame:
    # Asegura que Puntaje sea numérico si existe
    if "Puntaje (%)" in df.columns:
        df["Puntaje (%)"] = pd.to_numeric(df["Puntaje (%)"], errors="coerce")
    return df

def normalizar_anexo5(df: pd.DataFrame) -> pd.DataFrame:
    # Homogeneiza nombre de UT
    if "UNIDAD_TERRITORIAL" in df.columns:
        df.rename(columns={"UNIDAD_TERRITORIAL": "Unidad Territorial"}, inplace=True)

    # Normaliza plazo en días
    if "PLAZO_DÍAS" in df.columns:
        df["PLAZO_DÍAS"] = pd.to_numeric(df["PLAZO_DÍAS"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    elif "PLAZO" in df.columns:
        df["PLAZO_DÍAS"] = pd.to_numeric(df["PLAZO"].astype(str).str.extract(r"(\d+)")[0], errors="coerce")
    else:
        df["PLAZO_DÍAS"] = None

    return df
