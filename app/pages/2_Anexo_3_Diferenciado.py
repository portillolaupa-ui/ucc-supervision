import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import aplicar_estilo
from utils.loaders import cargar_datos

aplicar_estilo()
st.title("Anexo 3 – Acompañamiento Diferenciado (Vida sin Anemia)")

data = cargar_datos()
df_ctz = data.get("a3_ctz")
df_fac = data.get("a3_fac")
df_rol = data.get("a3_rol")

tab1, tab2, tab3 = st.tabs(["Monitoreo CTZ", "Facilitador Externo", "Rol del Gestor Local"])

with tab1:
    if isinstance(df_ctz, pd.DataFrame):
        st.metric("Registros CTZ", len(df_ctz))
        st.dataframe(df_ctz.head(15))
    else:
        st.warning("No hay datos de Monitoreo CTZ disponibles.")

with tab2:
    if isinstance(df_fac, pd.DataFrame):
        st.metric("Registros Facilitadores", len(df_fac))
        st.dataframe(df_fac.head(15))
    else:
        st.warning("No hay datos de Facilitadores disponibles.")

with tab3:
    if isinstance(df_rol, pd.DataFrame):
        st.metric("Registros Gestores", len(df_rol))
        st.dataframe(df_rol.head(15))
    else:
        st.warning("No hay datos del Rol del Gestor Local.")
