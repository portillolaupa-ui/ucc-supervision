# ==============================================================
# utils/llm.py
# Módulo unificado para generación de resúmenes IA (Anexo 2 y Anexo 3)
# ==============================================================

from __future__ import annotations
from typing import Dict, Any
import json
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# ==============================================================
# ⚙️ CONFIGURACIÓN BASE CLIENTE
# ==============================================================

def _get_client():
    if OpenAI is None:
        raise ImportError("El paquete openai no está instalado o no se pudo importar correctamente.")

    api_key = st.secrets.get("openai_api_key")
    base_url = st.secrets.get("openai_base_url", "https://api.openai.com/v1")
    if not api_key:
        raise RuntimeError("Falta 'openai_api_key' en .streamlit/secrets.toml")
    return OpenAI(api_key=api_key, base_url=base_url)

def _get_model():
    return st.secrets.get("openai_model", "gpt-4o-mini")

# ==============================================================
# 🧩 FUNCIÓN 1 – SÍNTESIS OPERATIVA (Anexo 2 optimizada para dashboard)
# ==============================================================

def generate_anexo2_summary(
    contexto: Dict[str, Any],
    *,
    model: str | None = None,
    max_tokens: int = 200
) -> str:
    """
    Genera una síntesis operativa breve (3 líneas) para la toma de decisiones
    sobre el Anexo 2, orientada a Especialistas de Acompañamiento Familiar y Unidades Territoriales (UT).
    """

    client = _get_client()
    modelo = model or _get_model()
    contenido_json = json.dumps(contexto, ensure_ascii=False)

    system_msg = (
        "Eres un analista operativo del Programa JUNTOS del MIDIS especializado en supervisión territorial. "
        "Los Especialistas de Acompañamiento Familiar han recogido esta información en sus supervisiones en campo a cada UT"
        "La evaluación se centra en las actividades de cumplimiento de los Getsores Locales y Coordinadores Técnico Zonales (CTZ) de cada UT supervisada"
        "Tu función es redactar una síntesis de tres líneas que oriente la toma de decisiones "
        "de los Especialistas de Acompañamiento Familiar del Programa Juntos. "
        "Nada de párrafos largos, ni porcentajes, ni introducciones. "
        "Solo tres líneas claras, técnicas y operativas, sin emojis ni listas. "
        "Usa este formato:\n"
        "Acción inmediata sugerida (qué hacer, cuándo hacerlo, cómo hacerlo y quién debe hacerlo)."
    )

    user_msg = (
        f"A partir del siguiente JSON, redacta la síntesis de tres líneas:\n"
        f"{contenido_json}\n\n"
        "Evita repetir porcentajes, cifras o tendencias ya visibles en el dashboard. "
        "Cita actores como 'CTZ', 'Gestor Local' según el contexto. "
        "En la última línea, formula una acción concreta"
    )

    resp = client.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=max_tokens,
        temperature=0.25,
    )

    return resp.choices[0].message.content.strip()

# ==============================================================
# 🧩 FUNCIÓN 2 – RESUMEN POR SECCIÓN (Anexo 3)
# ==============================================================

def generate_section_summary(contexto: dict) -> str:
    """Genera un resumen analítico y operativo por sección del Anexo 3."""
    client = _get_client()
    model = _get_model()

    system_msg = (
        "Eres un analista institucional del MIDIS. Redacta en tono técnico y claro (6–10 líneas). "
        "No uses emojis. No menciones otros anexos. "
        "Usa expresiones como 'las actividades sobre el Gestor Local', 'las actividades del Facilitador', "
        "o 'las actividades del CTZ'. Evita usar la palabra 'grupo'."
    )

    user_msg = (
        f"Genera un resumen del {contexto.get('anexo')} – {contexto.get('seccion')}.\n"
        f"Porcentajes: No cumple={contexto['porcentajes']['no_cumple']}%, "
        f"En desarrollo={contexto['porcentajes']['en_desarrollo']}%, "
        f"Cumple={contexto['porcentajes']['cumple']}%.\n"
        f"Ítems más frecuentes en NO CUMPLE: {[i['nombre'] for i in contexto.get('top_no_cumple', [])]}.\n"
        f"Ítems más frecuentes en DESARROLLO: {[i['nombre'] for i in contexto.get('top_en_desarrollo', [])]}.\n"
        "Escribe un único párrafo con hallazgos, interpretación y 2–3 recomendaciones prácticas."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=280,
    )
    return resp.choices[0].message.content.strip()

# ==============================================================
# 🧩 FUNCIÓN 3 – RESUMEN POR SECCIÓN (Anexo 4)
# ==============================================================

def generate_section_insight(contexto: dict) -> str:
    """
    Resumen SOLO con interpretación y recomendaciones operativas.
    No repite hallazgos porque ya están en KPI y gráficos.
    contexto: { anexo, seccion, porcentajes:{0/1/2}, top_no_cumple, top_en_desarrollo }
    """
    client = _get_client()
    model = _get_model()

    system_msg = (
        "Eres un analista institucional del MIDIS. Redacta en tono técnico y sobrio (5–8 líneas). "
        "No uses emojis. No repitas hallazgos ni porcentajes: céntrate en interpretar lo visto "
        "y cerrar con 2–3 recomendaciones accionables. Evita 'grupo'. Usa expresiones como "
        "'las actividades del Proyecto Vida Adolescente', 'las actividades de Independencia Económica', "
        "o equivalentes de la sección. No menciones otros anexos."
    )

    user_msg = (
        f"Sección: {contexto.get('seccion')} del {contexto.get('anexo')}.\n"
        f"Ítems con más No Cumple: {[i['nombre'] for i in contexto.get('top_no_cumple', [])]}.\n"
        f"Ítems con más En Desarrollo: {[i['nombre'] for i in contexto.get('top_en_desarrollo', [])]}.\n"
        "Redacta un único párrafo con: (1) interpretación de los patrones; "
        "y (2) recomendaciones operativas concretas para mejorar en el corto plazo."
    )

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.3,
        max_tokens=260,
    )
    return resp.choices[0].message.content.strip()

# ==============================================================
# 🧩 FUNCIÓN 4 – ANÁLISIS Y RECOMENDACIONES (Anexo 5)
# ==============================================================

def generate_section_insight(contexto: dict) -> str:
    """
    Genera análisis e interpretación o recomendaciones cualitativas
    para el Anexo 5 (Seguimiento de Acuerdos y Compromisos),
    centradas en el contenido de 'PUNTOS_CRITICOS'.
    """
    client = _get_client()
    model = _get_model()

    modo = contexto.get("modo", "analisis")
    contenido_json = json.dumps(contexto, ensure_ascii=False)

    # --- Mensaje del sistema ---
    system_msg = (
        "Eres un analista institucional del MIDIS especializado en supervisión territorial. "
        "Redacta en tono técnico, sobrio y analítico, sin emojis ni viñetas. "
        "Tu análisis debe basarse en el contenido cualitativo de los puntos críticos"
        "no en fechas ni plazos ni acuerdos"
        "Identifica patrones, temas recurrentes."
    )

    # --- Mensaje del usuario según modo ---
    if modo == "analisis":
        user_msg = (
            "Analiza el contenido de los puntos críticos"
            "a partir del siguiente resumen de datos:\n"
            f"{contenido_json}\n\n"
            "Redacta un único párrafo (3 líneas) que:\n"
            "- Analice los temas o problemáticas recurrentes en los puntos críticos.\n"
            "- Interprete el sentido general de los acuerdos de mejora (orientación, alcance, nivel de acción).\n"
        )
    elif modo == "recomendaciones":
        user_msg = (
            "Con base en los temas abordados en los puntos críticos del siguiente JSON:\n"
            f"{contenido_json}\n\n"
            "Redacta recomendaciones operativas, separadas por horizonte temporal:\n"
            "- **Corto plazo:** medidas inmediatas o ajustes operativos.\n"
            "- **Mediano plazo:** mejoras estructurales, fortalecimiento de capacidades, articulación intersectorial.\n"
            "Evita mencionar cifras o fechas; enfócate en la calidad de los procesos y la gestión."
        )
    else:
        user_msg = f"Redacta un breve análisis cualitativo a partir de este contexto: {contenido_json}"

    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        temperature=0.25,
        max_tokens=400,
    )

    return resp.choices[0].message.content.strip()