# ==============================================================
# DASHBOARD UCC 2025 – Versión Ejecutiva Institucional MIDIS (Paleta Armonizada)
# ==============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from utils.style import aplicar_estilo
from utils.loaders import cargar_datos
from utils.normalizers import normalizar_anexo2

# ==============================================================
# ⚙️ CONFIGURACIÓN GENERAL
# ==============================================================

st.set_page_config(
    page_title="Dashboard UCC - Supervisión y Monitoreo",
    page_icon="📊",
    layout="wide"
)

aplicar_estilo()

# ==============================================================
# 🏠 CABECERA
# ==============================================================

st.title("Dashboard de Supervisión y Monitoreo – UCC")
st.caption("Unidad de Cumplimiento de Corresponsabilidades – Programa JUNTOS | Ministerio de Desarrollo e Inclusión Social del Perú (MIDIS)")
st.markdown("---")

# ==============================================================
# 📂 CARGA DE DATOS
# ==============================================================

data = cargar_datos()

# ==============================================================
# 📊 VISIÓN GENERAL
# ==============================================================

st.header("Panorama Nacional")
st.caption("Resumen consolidado del desempeño del componente de Acompañamiento al Hogar (Anexo 2).")

try:
    df_a2 = data.get("a2")

    if df_a2 is not None:
        df_a2 = normalizar_anexo2(df_a2)

        # --- Métricas principales ---
        total_ut = len(df_a2["Unidad Territorial"].dropna().unique()) if "Unidad Territorial" in df_a2.columns else 0
        total_fichas = len(df_a2)
        prom_a2 = round(df_a2["Puntaje (%)"].mean(), 1) if "Puntaje (%)" in df_a2.columns else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("Unidades Territoriales Supervisadas", total_ut)
        col2.metric("Fichas Procesadas", total_fichas)
        col3.metric("Promedio AFA (%)", f"{prom_a2}")

        # --- Gráfico principal ---
        resumen = pd.DataFrame({
            "Componente": ["Acompañamiento al Hogar"],
            "Promedio Puntaje (%)": [prom_a2]
        })
        fig = px.bar(
            resumen,
            x="Componente",
            y="Promedio Puntaje (%)",
            text="Promedio Puntaje (%)",
            color="Componente",
            color_discrete_sequence=["#004C97"],
            title="Promedio de Desempeño – Acompañamiento al Hogar"
        )
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFFFFF",
            font=dict(size=13, color="#003A70"),
            title_font=dict(size=18, color="#003A70"),
            margin=dict(t=60, b=40)
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("No se encontró el archivo del Anexo 2 en data/processed/anexo2_consolidado.xlsx.")

except Exception as e:
    st.error(f"No se pudo generar el resumen: {e}")

# ==============================================================
# 🔄 INSTRUCCIONES DE NAVEGACIÓN
# ==============================================================

st.markdown("---")
st.info("""
🧭 Usa el menú lateral (📄 *Pages*) para acceder a:
- **Anexo 2:** Acompañamiento al Hogar  
- **Anexo 3:** Acompañamiento Diferenciado  
- **Anexo 5:** Seguimiento de Acuerdos  
- **Carga de Anexos:** Administración y procesamiento de nuevos archivos
""")

# ==============================================================
# 📜 FOOTER
# ==============================================================

st.markdown("---")
st.caption("© 2025 | Unidad de Cumplimiento de Corresponsabilidades (UCC) – MIDIS Perú | Elaborado con Streamlit y Plotly.")
