import streamlit as st

def aplicar_estilos():
    """Aplica estilos CSS institucionales MIDIS."""
    st.markdown("""
    <style>
    /* Fondo general */
    .main {
        background-color: #F7F9FB;
        padding: 0 2rem;
    }
    /* Encabezados */
    h1, h2, h3 {
        color: #004C97;
        font-weight: 700;
    }
    /* Tarjetas (métricas) */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #FFFFFF 60%, #E3F2FD 100%);
        padding: 25px;
        border-radius: 18px;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
        border-left: 6px solid #004C97;
        text-align: center;
    }
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #E8EEF5;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        color: #003A70;
    }
    /* Botones */
    div.stButton>button {
        background: linear-gradient(90deg, #004C97, #1976D2);
        color: white;
        border-radius: 10px;
        border: none;
        padding: 0.6rem 1.3rem;
        font-weight: 600;
    }
    div.stButton>button:hover {
        background: linear-gradient(90deg, #003B78, #1259A0);
    }
    /* Ocultar footer */
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
