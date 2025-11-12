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