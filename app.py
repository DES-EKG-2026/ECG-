from datetime import datetime
from pathlib import Path

import json
import random
import time

import streamlit as st

try:
    from rapidfuzz import fuzz
except:
    fuzz = None


# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Simulador DEA Profesional",
    page_icon="⚡",
    layout="centered"
)

BD_PATH = Path("historial_simulaciones.json")

if not BD_PATH.exists():
    BD_PATH.write_text(
        "[]",
        encoding="utf-8"
    )


# =====================================================
# CONOCIMIENTO IA
# =====================================================

BASE_CONOCIMIENTO = {

    "dea": """
Un DEA (Desfibrilador Externo Automático) es un dispositivo diseñado para reconocer ritmos cardíacos desfibrilables y guiar al operador mediante instrucciones visuales y auditivas.

Funciones:

• Analizar ritmo cardíaco.
• Identificar FV y TV sin pulso.
• Recomendar descarga.
• Guiar la RCP.

No sustituye la valoración clínica.
""",

    "fv": """
La fibrilación ventricular es una actividad eléctrica caótica originada en los ventrículos.

Características:

• Inconsciencia.
• Ausencia de pulso.
• Paro cardíaco.
• Ritmo desfibrilable.

Conducta:

• Descarga inmediata.
• Reiniciar RCP.
""",

    "tvsp": """
La taquicardia ventricular sin pulso es una taquicardia ventricular rápida sin gasto cardíaco efectivo.

Características:

• QRS ancho.
• Pulso ausente.
• Inestabilidad extrema.

Es desfibrilable.
""",

    "asistolia": """
La asistolia representa ausencia de actividad eléctrica ventricular efectiva.

Características:

• Línea plana.
• Pulso ausente.

No es desfibrilable.
""",

    "aesp": """
La actividad eléctrica sin pulso presenta actividad eléctrica organizada sin circulación efectiva.

Características:

• ECG puede parecer organizado.
• Pulso ausente.

No es desfibrilable.
""",

    "rcp": """
La RCP debe realizarse a:

• 100-120 compresiones por minuto.
• Profundidad de 5-6 cm.
• Expansión completa del tórax.
""",

    "rosc": """
ROSC significa Return Of Spontaneous Circulation.

Representa:

• Recuperación del pulso.
• Recuperación de la presión arterial.
• Recuperación del flujo sanguíneo.
"""
}
