from datetime import datetime
from pathlib import Path

import json
import random
import time

import streamlit as st

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


# =====================================================
# CONFIGURACIÓN GENERAL
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
# BASE DE CONOCIMIENTO IA
# =====================================================

BASE_CONOCIMIENTO = {

    "dea": """
Un DEA (Desfibrilador Externo Automático) es un dispositivo capaz de analizar ritmos cardíacos y determinar si una descarga puede estar indicada.

Funciones:

• Analizar el ritmo cardíaco.
• Detectar ritmos desfibrilables.
• Guiar al operador.
• Recomendar descarga cuando corresponda.

No sustituye el juicio clínico ni la RCP.
""",

    "fv": """
La fibrilación ventricular (FV) es una actividad eléctrica ventricular caótica.

Características:

• Ausencia de pulso.
• Inconsciencia.
• Paro cardiaco.
• Ritmo desfibrilable.

Conducta:

• Aplicar descarga.
• Reanudar RCP.
• Reevaluar posteriormente.
""",

    "tvsp": """
La taquicardia ventricular sin pulso es una arritmia rápida de origen ventricular.

Características:

• Complejos anchos.
• Pulso ausente.
• Colapso circulatorio.

Es un ritmo desfibrilable.
""",

    "asistolia": """
La asistolia representa ausencia de actividad eléctrica cardíaca útil.

Características:

• Línea plana.
• Ausencia de circulación.
• Ausencia de pulso.

No se desfibrila.
""",

    "aesp": """
La actividad eléctrica sin pulso (AESP) presenta actividad eléctrica organizada sin circulación efectiva.

Características:

• ECG aparentemente organizado.
• No existe pulso palpable.

No es desfibrilable.
""",

    "rcp": """
La RCP debe realizarse a:

• 100 a 120 compresiones por minuto.
• Profundidad de 5 a 6 cm.
• Mínimas interrupciones.

Es fundamental tras el análisis o la descarga.
""",

    "rosc": """
ROSC significa Return Of Spontaneous Circulation.

Representa:

• Recuperación del pulso.
• Recuperación de la presión arterial.
• Retorno de la circulación espontánea.
"""
}


# =====================================================
# PALABRAS CLAVE IA
# =====================================================

TOPICOS = {

    "dea": [
        "dea",
        "desa",
        "desfibrilador"
    ],

    "fv": [
        "fv",
        "fibrilacion ventricular",
        "fibrilación ventricular"
    ],

    "tvsp": [
        "tv",
        "tvsp",
        "taquicardia ventricular",
        "tv sin pulso"
    ],

    "asistolia": [
        "asistolia",
        "línea plana",
        "linea plana"
    ],

    "aesp": [
        "aesp",
        "actividad electrica sin pulso",
        "actividad eléctrica sin pulso"
    ],

    "rcp": [
        "rcp",
        "compresiones",
        "reanimacion",
        "reanimación"
    ],

    "rosc": [
        "rosc",
        "circulacion espontanea",
        "circulación espontánea"
    ]
}


# =====================================================
# MOTOR IA LOCAL
# =====================================================

def responder_ia(pregunta):

    pregunta = pregunta.lower()

    if fuzz is None:

        for tema in TOPICOS:

            if tema in pregunta:
                return BASE_CONOCIMIENTO[tema]

        return """
Temas disponibles:

• DEA
• FV
• TVSP
• AESP
• Asistolia
• RCP
• ROSC
"""

    mejor_score = 0
    mejor_tema = None

    for tema, palabras in TOPICOS.items():

        score = fuzz.partial_ratio(
            pregunta,
            " ".join(palabras)
        )

        if score > mejor_score:

            mejor_score = score
            mejor_tema = tema

    if mejor_score > 45:

        return BASE_CONOCIMIENTO[mejor_tema]

    return """
No encontré una coincidencia exacta.

Pruebe con temas relacionados con:

• DEA
• FV
• TVSP
• AESP
• Asistolia
• RCP
• ROSC
"""


# =====================================================
# BASE DE DATOS
# =====================================================

def cargar_historial():

    try:

        return json.loads(
            BD_PATH.read_text(
                encoding="utf-8"
            )
        )

    except Exception:

        return []


def guardar_evento(evento):

    datos = cargar_historial()

    datos.append(evento)

    BD_PATH.write_text(
        json.dumps(
            datos,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# =====================================================
# ESTADO GLOBAL
# =====================================================

def init():

    defaults = {

        "pagina": "MENU",

        "chat": [],

        "inicio": None,

        "fin": None,

        "caso": "Fibrilación ventricular",

        "resultado": "",

        "descargas": 0,

        "energia": 0
    }

    for clave, valor in defaults.items():

        st.session_state.setdefault(
            clave,
            valor
        )


init()
# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.stApp{
    background:#f2f2f2;
}

/* Texto */

html,
body,
p,
span,
label,
li,
h1,
h2,
h3,
h4{
    color:#111111 !important;
}

/* Logo */

.logo{
    text-align:center;
    font-size:42px;
    font-weight:900;
    color:#111111;
    margin-bottom:20px;
}

.bolt{
    color:#f5b300;
}

/* Paneles */

.panel{

    background:white;

    border:4px solid black;

    border-radius:20px;

    padding:20px;

    margin-top:15px;

    color:black;
}

/* Botones */

.stButton button{

    width:100%;

    height:55px;

    border:3px solid black;

    border-radius:12px;

    background:white;

    color:black;

    font-size:18px;

    font-weight:bold;
}

.stButton button:hover{

    background:black;

    color:white;
}

/* Paciente */

.human{

    display:flex;

    flex-direction:column;

    align-items:center;

    margin:20px;
}

.head{

    width:90px;

    height:90px;

    border-radius:50%;

    background:black;
}

.body{

    width:170px;

    height:250px;

    background:black;

    margin-top:10px;

    position:relative;

    clip-path:polygon(
    15% 0%,
    85% 0%,
    95% 100%,
    5% 100%
    );
}

.patch{

    width:28px;

    height:28px;

    background:red;

    position:absolute;
}

.patch1{

    top:30px;

    left:30px;
}

.patch2{

    top:100px;

    right:30px;
}

/* ECG */

.monitor{

    background:black;

    color:#00ff66;

    height:120px;

    border-radius:15px;

    margin-top:15px;

    padding:20px;

    font-family:monospace;

    font-size:28px;

    display:flex;

    align-items:center;

    overflow:hidden;
}

</style>
""",
unsafe_allow_html=True)

# =====================================================
# COMPONENTES
# =====================================================

def logo():

    st.markdown(
        """
        <div class="logo">
        DESFIBRILAD<span class="bolt">⚡</span>R
        </div>
        """,
        unsafe_allow_html=True
    )


def paciente():

    st.markdown(
        """
        <div class="human">

            <div class="head"></div>

            <div class="body">

                <div class="patch patch1"></div>

                <div class="patch patch2"></div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# ECG
# =====================================================

def mostrar_ecg(tipo):

    if tipo == "Fibrilación ventricular":

        señal = "▄▂▆▃▇▂▄▆▂▇▄▃▅▂▆▄▂▇▃▄▆"

    elif tipo == "TV sin pulso":

        señal = "/\\/\\/\\/\\/\\/\\/\\/\\/\\/\\/"

    elif tipo == "Asistolia":

        señal = "___________________________"

    elif tipo == "AESP":

        señal = "__/\\____/\\____/\\____/\\___"

    else:

        señal = "__/\\____/\\_______/\\______"

    st.markdown(
        f"""
        <div class="monitor">
        {señal}
        </div>
        """,
        unsafe_allow_html=True
    )
    # =====================================================
# CASOS CLÍNICOS
# =====================================================

CASOS = {

    "Fibrilación ventricular": {
        "conciencia": "Inconsciente",
        "respiracion": "Agónica",
        "pulso": "Ausente",
        "desfibrilable": True
    },

    "TV sin pulso": {
        "conciencia": "Inconsciente",
        "respiracion": "Ausente",
        "pulso": "Ausente",
        "desfibrilable": True
    },

    "Asistolia": {
        "conciencia": "Inconsciente",
        "respiracion": "Ausente",
        "pulso": "Ausente",
        "desfibrilable": False
    },

    "AESP": {
        "conciencia": "Inconsciente",
        "respiracion": "Agónica",
        "pulso": "Ausente",
        "desfibrilable": False
    }
}


# =====================================================
# CABECERA
# =====================================================

logo()


# =====================================================
# MENU PRINCIPAL
# =====================================================

if st.session_state.pagina == "MENU":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader("Simulador DEA")

    st.write(
        "Entrenamiento educativo para análisis de ritmos y uso de DEA."
    )

    if st.button("📚 Aprendizaje"):

        st.session_state.pagina = "APRENDIZAJE"
        st.rerun()

    if st.button("⚡ Simulación DEA"):

        st.session_state.pagina = "SIMULACION"
        st.rerun()

    if st.button("📊 Estadísticas"):

        st.session_state.pagina = "ESTADISTICAS"
        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# APRENDIZAJE
# =====================================================

elif st.session_state.pagina == "APRENDIZAJE":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "Centro de aprendizaje"
    )

    st.markdown("""
### Preguntas sugeridas

• ¿Qué es un DEA?

• ¿Qué es una FV?

• ¿Qué es una TVSP?

• ¿Qué significa ROSC?

• ¿Qué es AESP?

• ¿Por qué la asistolia no se desfibrila?

• ¿Cómo se realiza la RCP?
""")

    if st.button("🤖 Abrir asistente"):

        st.session_state.pagina = "CHAT"
        st.rerun()

    if st.button("⬅ Volver"):

        st.session_state.pagina = "MENU"
        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# CHAT IA
# =====================================================

elif st.session_state.pagina == "CHAT":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader("Asistente IA")

    pregunta = st.chat_input(
        "Escriba una pregunta..."
    )

    if pregunta:

        respuesta = responder_ia(
            pregunta
        )

        st.session_state.chat.append(
            ("user", pregunta)
        )

        st.session_state.chat.append(
            ("assistant", respuesta)
        )

    for rol, mensaje in st.session_state.chat:

        with st.chat_message(rol):

            st.write(mensaje)

    if st.button("⬅ Volver"):

        st.session_state.pagina = "APRENDIZAJE"
        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# SIMULACIÓN
# =====================================================

elif st.session_state.pagina == "SIMULACION":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "Preparar paciente"
    )

    paciente()

    caso = st.selectbox(
        "Seleccione un caso",
        list(CASOS.keys())
    )

    st.session_state.caso = caso

    datos = CASOS[caso]

    st.info(
        f"""
Conciencia: {datos['conciencia']}

Respiración: {datos['respiracion']}

Pulso: {datos['pulso']}
"""
    )

    mostrar_ecg(caso)

    if st.button("ANALIZAR"):

        st.session_state.inicio = datetime.now()

        barra = st.progress(0)

        for i in range(100):

            barra.progress(i + 1)

            time.sleep(0.01)

        if datos["desfibrilable"]:

            st.session_state.pagina = "DESCARGA"

        else:

            st.session_state.resultado = \
                "Ritmo no desfibrilable"

            st.session_state.fin = \
                datetime.now()

            guardar_evento({

                "fecha":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "caso":
                caso,

                "resultado":
                "Ritmo no desfibrilable",

                "descargas":
                0,

                "energia":
                0
            })

            st.session_state.pagina = \
                "RESUMEN"

        st.rerun()

    if st.button("⬅ Volver al menú"):

        st.session_state.pagina = "MENU"
        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )
    # =====================================================
# DESCARGA DEA
# =====================================================

elif st.session_state.pagina == "DESCARGA":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "⚡ DESCARGA RECOMENDADA"
    )

    st.success(
        "El DEA recomienda una descarga virtual de 200 J."
    )

    mostrar_ecg(
        st.session_state.caso
    )

    st.warning(
        "Simulación educativa. No se genera energía real."
    )

    if st.button(
        "⚡ APLICAR DESCARGA"
    ):

        st.session_state.descargas += 1

        st.session_state.energia += 200

        exito = random.choice(
            [True, False]
        )

        if exito:

            st.session_state.resultado = \
                "ROSC"

        else:

            st.session_state.resultado = \
                "Persistencia del ritmo"

        st.session_state.fin = datetime.now()

        guardar_evento({

            "fecha":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),

            "caso":
            st.session_state.caso,

            "resultado":
            st.session_state.resultado,

            "descargas":
            st.session_state.descargas,

            "energia":
            st.session_state.energia

        })

        st.session_state.pagina = \
            "POSTDESCARGA"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# POST DESCARGA
# =====================================================

elif st.session_state.pagina == "POSTDESCARGA":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    if st.session_state.resultado == "ROSC":

        st.success(
            "✅ Retorno de circulación espontánea (ROSC)"
        )

        mostrar_ecg(
            "Ritmo sinusal"
        )

    else:

        st.error(
            "❌ Persiste el ritmo inicial"
        )

        mostrar_ecg(
            st.session_state.caso
        )

    if st.button(
        "📋 VER RESUMEN"
    ):

        st.session_state.pagina = \
            "RESUMEN"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# RESUMEN
# =====================================================

elif st.session_state.pagina == "RESUMEN":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "Resumen clínico"
    )

    tiempo_total = "0:00:00"

    if (
        st.session_state.inicio
        and
        st.session_state.fin
    ):

        tiempo_total = str(

            st.session_state.fin
            -
            st.session_state.inicio

        ).split(".")[0]

    st.write(
        f"**Caso:** {st.session_state.caso}"
    )

    st.write(
        f"**Resultado:** {st.session_state.resultado}"
    )

    st.write(
        f"**Descargas:** {st.session_state.descargas}"
    )

    st.write(
        f"**Energía total:** {st.session_state.energia} J"
    )

    st.write(
        f"**Duración:** {tiempo_total}"
    )

    st.markdown("---")

    if st.session_state.resultado == "ROSC":

        mostrar_ecg(
            "Ritmo sinusal"
        )

    else:

        mostrar_ecg(
            st.session_state.caso
        )

    reporte = f"""
SIMULADOR DEA

CASO:
{st.session_state.caso}

RESULTADO:
{st.session_state.resultado}

DESCARGAS:
{st.session_state.descargas}

ENERGÍA:
{st.session_state.energia} J

DURACIÓN:
{tiempo_total}

FECHA:
{datetime.now().strftime('%Y-%m-%d')}

HORA:
{datetime.now().strftime('%H:%M:%S')}
"""

    st.download_button(
        "📄 Descargar resumen",
        reporte,
        file_name="resumen_dea.txt"
    )

    if st.button(
        "🔄 Nueva simulación"
    ):

        st.session_state.descargas = 0
        st.session_state.energia = 0
        st.session_state.resultado = ""
        st.session_state.inicio = None
        st.session_state.fin = None

        st.session_state.pagina = \
            "MENU"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# ESTADÍSTICAS
# =====================================================

elif st.session_state.pagina == "ESTADISTICAS":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "Estadísticas"
    )

    historial = cargar_historial()

    total = len(historial)

    st.metric(
        "Simulaciones",
        total
    )

    if total > 0:

        exitos = len([
            e
            for e in historial
            if e["resultado"] == "ROSC"
        ])

        porcentaje = round(
            (exitos / total) * 100,
            1
        )

        st.metric(
            "ROSC",
            exitos
        )

        st.metric(
            "% Éxito",
            porcentaje
        )

        st.markdown("---")

        st.subheader(
            "Últimas simulaciones"
        )

        for evento in reversed(
            historial[-10:]
        ):

            st.info(
                f"""
Fecha: {evento['fecha']}

Caso: {evento['caso']}

Resultado: {evento['resultado']}
"""
            )

        st.download_button(
            "⬇ Descargar historial JSON",
            json.dumps(
                historial,
                indent=4,
                ensure_ascii=False
            ),
            file_name=
            "historial_simulaciones.json"
        )

    else:

        st.warning(
            "No existen simulaciones guardadas."
        )

    if st.button(
        "⬅ Volver"
    ):

        st.session_state.pagina = \
            "MENU"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# PIE DE PÁGINA
# =====================================================

st.markdown(
    """
---
**Simulador DEA Académico**

Uso exclusivamente educativo.

No analiza señales reales.

No controla dispositivos biomédicos.
"""
)
