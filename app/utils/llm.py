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
# 🔎 INTERPRETACIÓN AUTOMÁTICA DE GRÁFICOS (IA)
# ==============================================================

def generar_interpretacion_grafico(titulo: str, resumen_datos: str) -> str:
    """
    Genera una interpretación técnica breve (2–3 líneas) de un gráfico
    basado en un resumen de datos en texto (df.to_string()).
    """
    try:
        client = _get_client()
        modelo = _get_model()

        prompt = f"""
Eres un analista institucional del Programa JUNTOS – MIDIS Perú,
especializado en supervisión y monitoreo territorial.

Se te muestra un gráfico titulado "{titulo}", con resultados de supervisión
de las fichas de campo (Anexos 2, 3 y 4).

Debes redactar una **interpretación técnica breve** (máximo 3 líneas) que:
- Describa la tendencia general (niveles de cumplimiento, brechas o mejoras).
- Destaque si existe una unidad territorial con valores altos o bajos.
- Si hay un valor extremo (por ejemplo, 100%), menciónalo como posible sesgo puntual.
- Use lenguaje institucional y objetivo, sin listas ni adjetivos enfáticos.

Datos resumidos:
{resumen_datos}
"""

        respuesta = client.chat.completions.create(
            model=modelo,
            messages=[
                {"role": "system", "content": "Eres un analista institucional experto en monitoreo territorial."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=160,
            temperature=0.4,
        )

        return respuesta.choices[0].message.content.strip()

    except Exception:
        return "💬 ⚠️ No se pudo generar la interpretación automática"


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
# 💬 GENERADOR DE RESUMEN – ANEXO 3 (versión breve y ejecutiva)
# ==============================================================

def generate_anexo3_summary(contexto: dict) -> str:
    """
    Genera un resumen analítico breve y recomendaciones operativas
    del Anexo 3 – Acompañamiento Diferenciado.
    Redacta un texto claro, técnico y conciso (máx. 6 líneas).
    """

    try:
        import json
        from openai import OpenAI
        import streamlit as st

        # Inicializar cliente
        api_key = st.secrets.get("openai_api_key")
        base_url = st.secrets.get("openai_base_url", "https://api.openai.com/v1")
        client = OpenAI(api_key=api_key, base_url=base_url)

        # Convertir contexto a JSON legible
        contexto_json = json.dumps(contexto, ensure_ascii=False, indent=2)

        prompt = f"""
        Eres un analista del Programa JUNTOS.
        Resume de forma breve y profesional los resultados del Anexo 3 – Acompañamiento Diferenciado.
        
        Instrucciones:
        - Máximo 6 líneas.
        - No incluyas títulos como “Resumen Ejecutivo”.
        - Usa tono técnico y directo.
        - Incluye: síntesis del cumplimiento, una conclusión global y 1 o 2 recomendaciones concretas.

        CONTEXTO:
        {contexto_json}
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "Eres un especialista en monitoreo y evaluación del MIDIS."},
                {"role": "user", "content": prompt}
            ]
        )

        texto = completion.choices[0].message.content.strip()
        return texto

    except Exception:
        return "💬 ⚠️ No se pudo generar la interpretación automática"

# ==============================================================
# 💬 GENERADOR DE RESUMEN – ANEXO 4 (versión breve)
# ==============================================================

def generate_anexo4_summary(contexto: dict) -> str:
    """
    Genera un resumen operativo breve del Anexo 4 – Acompañamiento a Jóvenes.
    Incluye síntesis de resultados y 2 recomendaciones clave.
    """
    try:
        import json
        from openai import OpenAI
        import streamlit as st

        api_key = st.secrets.get("openai_api_key")
        base_url = st.secrets.get("openai_base_url", "https://api.openai.com/v1")
        client = OpenAI(api_key=api_key, base_url=base_url)

        contexto_json = json.dumps(contexto, ensure_ascii=False, indent=2)
        prompt = f"""
        Redacta un resumen técnico breve (máximo 6 líneas) sobre el Anexo 4 – Acompañamiento a Jóvenes.
        Usa tono institucional, directo y analítico.
        No incluyas títulos ni encabezados.
        Menciona los resultados generales y 2 recomendaciones operativas.

        CONTEXTO:
        {contexto_json}
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "Eres un especialista en monitoreo territorial y análisis operativo del MIDIS."},
                {"role": "user", "content": prompt}
            ]
        )

        texto = completion.choices[0].message.content.strip()
        return texto

    except Exception:
        return "💬 ⚠️ No se pudo generar la interpretación automática"

# ==============================================================
# 💬 GENERADOR DE ANÁLISIS – ANEXO 5 (ACUERDOS Y PUNTOS CRÍTICOS)
# ==============================================================

def generate_anexo5_summary(contexto: dict) -> str:
    """
    Resume los principales hallazgos, acuerdos y puntos críticos del Anexo 5.
    Redacta máximo 7 líneas, con enfoque en seguimiento operativo.
    """
    try:
        import json
        from openai import OpenAI
        import streamlit as st

        api_key = st.secrets.get("openai_api_key")
        base_url = st.secrets.get("openai_base_url", "https://api.openai.com/v1")
        client = OpenAI(api_key=api_key, base_url=base_url)

        contexto_json = json.dumps(contexto, ensure_ascii=False, indent=2)
        prompt = f"""
        Eres un analista del MIDIS encargado del seguimiento de supervisiones.
        Resume los acuerdos y puntos críticos del Anexo 5 en máximo 7 líneas.
        Evita títulos. Usa lenguaje técnico y conciso.
        Menciona:
        - Problemas recurrentes.
        - Áreas o roles más involucrados.
        - Tipos de acuerdos más frecuentes.
        - Plazos comunes o urgencias detectadas.
        - Recomendaciones operativas para seguimiento.

        CONTEXTO:
        {contexto_json}
        """

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {"role": "system", "content": "Eres un especialista en supervisión y seguimiento operativo del MIDIS."},
                {"role": "user", "content": prompt}
            ]
        )

        texto = completion.choices[0].message.content.strip()
        return texto

    except Exception:
        return "💬 ⚠️ No se pudo generar la interpretación automática"
