import streamlit as st

def aplicar_estilo():
    st.markdown("""
    <style>
    .main {background-color:#F7F9FB;padding:0 2rem;}
    h1,h2,h3{color:#004C97;font-weight:700;}
    div[data-testid="stMetric"]{
        background:linear-gradient(135deg,#FFFFFF 60%,#E3F2FD 100%);
        padding:25px;border-radius:18px;
        border-left:6px solid #004C97;
    }
    footer{visibility:hidden;}
    </style>
    """, unsafe_allow_html=True)
