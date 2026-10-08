from datetime import datetime
from pathlib import Path

import base64
import json
import random
import time

import streamlit as st

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None


# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Simulador DEA Profesional",
    page_icon="⚡",
    layout="centered"
)

ASSETS = Path(__file__).parent

BD_PATH = (
    Path(__file__).parent
    / "historial_simulaciones.json"
)

if not BD_PATH.exists():

    BD_PATH.write_text(
        "[]",
        encoding="utf-8"
    )


# =====================================================
# SVG
# =====================================================

def svg(nombre, clase="art"):

    archivo = ASSETS / nombre

    if archivo.exists():

        contenido = archivo.read_text(
            encoding="utf-8"
        )

        return f"""
        <div class="{clase}">
        {contenido}
        </div>
        """

    return f"""
    <div class="{clase}">
    SVG NO ENCONTRADO:
    {nombre}
    </div>
    """


def uri(nombre):

    archivo = ASSETS / nombre

    if archivo.exists():

        return (
            "data:image/svg+xml;base64,"
            +
            base64.b64encode(
                archivo.read_bytes()
            ).decode("ascii")
        )

    return ""


# =====================================================
# ECG SVG ORIGINALES
# =====================================================

RITMOS = {

    "Fibrilación ventricular":
    "ecg_fibrilacion_ventricular.svg",

    "TV sin pulso":
    "ecg_taquicardia_ventricular.svg",

    "Asistolia":
    "ecg_asistolia.svg",

    "AESP":
    "ecg_aesp.svg",

    "Ritmo sinusal":
    "senal_ecg.svg"
}


# =====================================================
# BASE DE CONOCIMIENTO IA
# =====================================================

BASE_CONOCIMIENTO = {

    "dea": """
Un DEA (Desfibrilador Externo Automático) analiza automáticamente el ritmo cardíaco para determinar si una descarga puede estar indicada.

Funciones:

• Análisis automático.
• Identificación de ritmos desfibrilables.
• Guía paso a paso.
• Apoyo al operador.

No sustituye la RCP.
""",

    "fv": """
La fibrilación ventricular es un ritmo eléctrico caótico de los ventrículos.

Características:

• Pulso ausente.
• Inconsciencia rápida.
• Paro cardíaco.

Conducta:

• Descarga inmediata.
• Continuar RCP.
""",

    "tvsp": """
La taquicardia ventricular sin pulso es una arritmia ventricular rápida sin gasto cardíaco efectivo.

Es un ritmo desfibrilable.
""",

    "asistolia": """
La asistolia representa ausencia casi completa de actividad eléctrica ventricular.

No debe desfibrilarse.
""",

    "aesp": """
La actividad eléctrica sin pulso muestra actividad eléctrica organizada pero sin circulación efectiva.

No debe desfibrilarse.
""",

    "rosc": """
ROSC significa Return Of Spontaneous Circulation.

Representa el retorno de la circulación espontánea.
""",

    "rcp": """
La RCP debe realizarse a:

• 100 a 120 compresiones por minuto.
• Profundidad de 5 a 6 cm.
• Interrupciones mínimas.
""",

    "parches": """
Posición de los parches DEA:

• Debajo de la clavícula derecha.
• Línea axilar media izquierda.
""",

    "energia": """
La mayoría de DEA modernos utilizan descargas bifásicas.

En esta simulación se utilizan 200 J virtuales.
""",

    "acls": """
ACLS significa Advanced Cardiovascular Life Support.

Es el soporte vital cardiovascular avanzado.
""",

    "adrenalina": """
La adrenalina se utiliza dentro de protocolos avanzados de reanimación cardiopulmonar.
""",

    "ecg": """
Un ECG registra la actividad eléctrica cardíaca y permite reconocer múltiples ritmos.
""",

    "causas": """
Las causas reversibles del paro incluyen:

• Hipoxia
• Hipovolemia
• Hipo/Hipercaliemia
• Taponamiento cardíaco
• Tromboembolismo
• Neumotórax a tensión
"""
}


# =====================================================
# PALABRAS CLAVE IA
# =====================================================

TOPICOS = {

    "dea":[
        "dea",
        "desa",
        "desfibrilador"
    ],

    "fv":[
        "fv",
        "fibrilacion ventricular",
        "ritmo desfibrilable"
    ],

    "tvsp":[
        "tv",
        "tvsp",
        "tv sin pulso",
        "taquicardia ventricular"
    ],

    "aesp":[
        "aesp",
        "actividad electrica sin pulso"
    ],

    "asistolia":[
        "asistolia",
        "linea plana"
    ],

    "rosc":[
        "rosc",
        "circulacion espontanea"
    ],

    "rcp":[
        "rcp",
        "compresiones",
        "masaje cardiaco"
    ],

    "parches":[
        "parche",
        "electrodos",
        "colocacion"
    ],

    "energia":[
        "energia",
        "julios",
        "200j"
    ],

    "acls":[
        "acls"
    ],

    "adrenalina":[
        "adrenalina"
    ],

    "ecg":[
        "ecg",
        "electrocardiograma"
    ],

    "causas":[
        "4h",
        "4t",
        "causas reversibles"
    ]
}


# =====================================================
# IA LOCAL
# =====================================================

def responder_ia(pregunta):

    pregunta = pregunta.lower()

    if fuzz:

        mejor_tema = None
        mejor_score = 0

        for tema, keywords in TOPICOS.items():

            score = fuzz.partial_ratio(
                pregunta,
                " ".join(keywords)
            )

            if score > mejor_score:

                mejor_score = score
                mejor_tema = tema

        if mejor_score > 45:

            return BASE_CONOCIMIENTO[
                mejor_tema
            ]

    for tema in TOPICOS:

        if tema in pregunta:

            return BASE_CONOCIMIENTO[
                tema
            ]

    return """
Puedo responder preguntas sobre:

• DEA
• FV
• TV sin pulso
• AESP
• Asistolia
• ROSC
• RCP
• ACLS
• Adrenalina
• ECG
• Parches
• Energía de descarga
• Causas reversibles del paro
"""


# =====================================================
# HISTORIAL
# =====================================================

def cargar_historial():

    try:

        return json.loads(
            BD_PATH.read_text(
                encoding="utf-8"
            )
        )

    except:

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
# SESSION STATE
# =====================================================

def init():

    defaults = {

        "pagina":"MENU",

        "chat":[],

        "inicio":None,

        "fin":None,

        "caso":
        "Fibrilación ventricular",

        "resultado":"",

        "descargas":0,

        "energia":0
    }

    for k, v in defaults.items():

        st.session_state.setdefault(
            k,
            v
        )
# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.stApp{
    background:#eeeeee;
}

/* TEXTO */

html,
body,
p,
span,
label,
li,
h1,
h2,
h3,
h4,
h5,
h6{
    color:#111111 !important;
}

/* LOGO */

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

/* PANEL */

.panel{

    background:white;

    border:3px solid black;

    border-radius:20px;

    padding:20px;

    margin-top:15px;
}

/* BOTONES */

.stButton > button{

    width:100%;

    height:60px;

    border:3px solid black;

    border-radius:10px;

    background:white;

    color:black;

    font-size:18px;

    font-weight:800;
}

.stButton > button:hover{

    background:black;

    color:white;
}

/* SELECTORES */

div[data-baseweb="select"] *{

    color:black !important;
}

/* SVG PACIENTE */

.art svg{

    width:220px;

    height:auto;

    display:block;

    margin:auto;
}

/* ECG */

.ecg-art svg{

    width:100%;

    height:150px;

    display:block;
}

/* INFO */

.info{

    border:2px solid black;

    border-radius:10px;

    padding:10px;

    margin-top:10px;

    background:white;
}

.warning{

    background:#fff3cd;

    border:2px solid #d6aa00;

    padding:10px;

    border-radius:10px;
}

.ok{

    background:#d4edda;

    border:2px solid #28a745;

    padding:10px;

    border-radius:10px;
}

</style>
""",
unsafe_allow_html=True)


# =====================================================
# LOGO
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


# =====================================================
# ECG SVG
# =====================================================

def mostrar_ecg(ritmo):

    archivo = RITMOS.get(
        ritmo,
        "senal_ecg.svg"
    )

    st.markdown(
        svg(
            archivo,
            "ecg-art"
        ),
        unsafe_allow_html=True
    )


# =====================================================
# PACIENTE SVG
# =====================================================

def mostrar_paciente():

    st.markdown(
        svg(
            "usuario_con_parches.svg",
            "art"
        ),
        unsafe_allow_html=True
    )


# =====================================================
# ICONOS
# =====================================================

def icono_info():

    st.markdown(
        svg(
            "corazon_informacion.svg",
            "art"
        ),
        unsafe_allow_html=True
    )


def icono_confirmacion():

    st.markdown(
        svg(
            "corazon_confirmacion.svg",
            "art"
        ),
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
# MENÚ PRINCIPAL
# =====================================================

if st.session_state.pagina == "MENU":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    icono_info()

    st.subheader(
        "Simulador Académico DEA"
    )

    st.write(
        "Entrenamiento virtual para reconocimiento de ritmos cardíacos y uso educativo del DEA."
    )

    if st.button("📚 APRENDIZAJE"):

        st.session_state.pagina = "APRENDIZAJE"
        st.rerun()

    if st.button("⚡ OPERAR DEA"):

        st.session_state.pagina = "SIMULACION"
        st.rerun()

    if st.button("📊 ESTADÍSTICAS"):

        st.session_state.pagina = "ESTADISTICAS"
        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# PANTALLA APRENDIZAJE
# =====================================================

elif st.session_state.pagina == "APRENDIZAJE":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    icono_info()

    st.subheader(
        "Centro de aprendizaje"
    )

    st.markdown(
        """
### Preguntas sugeridas

• ¿Qué es un DEA?

• ¿Qué es la fibrilación ventricular?

• ¿Qué es una TV sin pulso?

• ¿Qué significa ROSC?

• ¿Qué es una AESP?

• ¿Qué es ACLS?

• ¿Qué son las 4H y 4T?

• ¿Cómo se colocan los parches?

• ¿Qué es la desfibrilación?

• ¿Qué energía utiliza un DEA?

• ¿Cuál es la frecuencia correcta de RCP?
"""
    )

    if st.button(
        "🤖 ABRIR ASISTENTE IA"
    ):

        st.session_state.pagina = "CHAT"
        st.rerun()

    if st.button(
        "⬅ VOLVER"
    ):

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

    st.subheader(
        "Asistente IA Biomédico"
    )

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

    if st.button(
        "⬅ VOLVER"
    ):

        st.session_state.pagina = "APRENDIZAJE"

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# SIMULACIÓN DEA
# =====================================================

elif st.session_state.pagina == "SIMULACION":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "Preparar paciente"
    )

    mostrar_paciente()

    caso = st.selectbox(
        "Seleccione un caso clínico",
        list(CASOS.keys())
    )

    st.session_state.caso = caso

    datos = CASOS[caso]

    st.markdown(
        f"""
<div class="info">

<b>Conciencia:</b> {datos['conciencia']}<br>

<b>Respiración:</b> {datos['respiracion']}<br>

<b>Pulso:</b> {datos['pulso']}

</div>
""",
        unsafe_allow_html=True
    )

    st.markdown("### ECG")

    mostrar_ecg(caso)

    if st.button(
        "ANALIZAR RITMO"
    ):

        st.session_state.inicio = (
            datetime.now()
        )

        barra = st.progress(0)

        for i in range(100):

            barra.progress(
                i + 1
            )

            time.sleep(0.01)

        if datos["desfibrilable"]:

            st.session_state.pagina = (
                "DESCARGA"
            )

        else:

            st.session_state.resultado = (
                "Ritmo no desfibrilable"
            )

            st.session_state.fin = (
                datetime.now()
            )

            guardar_evento({

                "fecha":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                "caso":
                caso,

                "resultado":
                st.session_state.resultado,

                "descargas":
                0,

                "energia":
                0
            })

            st.session_state.pagina = (
                "RESUMEN"
            )

        st.rerun()

    if st.button(
        "⬅ VOLVER AL MENÚ"
    ):

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )
    # =====================================================
# DESCARGA RECOMENDADA
# =====================================================

elif st.session_state.pagina == "DESCARGA":

    st.markdown(
        "<div class='panel'>",
        unsafe_allow_html=True
    )

    st.subheader(
        "⚡ DESCARGA RECOMENDADA"
    )

    mostrar_ecg(
        st.session_state.caso
    )

    st.markdown(
        """
        <div class="warning">

        El DEA recomienda una descarga virtual
        de 200 J.

        Esta simulación es exclusivamente
        educativa.

        </div>
        """,
        unsafe_allow_html=True
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

            st.session_state.resultado = (
                "ROSC"
            )

        else:

            st.session_state.resultado = (
                "Persistencia del ritmo"
            )

        st.session_state.fin = (
            datetime.now()
        )

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

        st.session_state.pagina = (
            "POSTDESCARGA"
        )

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

    if (
        st.session_state.resultado
        ==
        "ROSC"
    ):

        icono_confirmacion()

        st.success(
            "✅ Retorno de circulación espontánea"
        )

        mostrar_ecg(
            "Ritmo sinusal"
        )

    else:

        icono_info()

        st.error(
            "❌ Persiste el ritmo inicial"
        )

        mostrar_ecg(
            st.session_state.caso
        )

    if st.button(
        "📋 VER RESUMEN"
    ):

        st.session_state.pagina = (
            "RESUMEN"
        )

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
        "Resumen del evento"
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
        f"**Energía:** {st.session_state.energia} J"
    )

    st.write(
        f"**Tiempo total:** {tiempo_total}"
    )

    st.markdown("---")

    if (
        st.session_state.resultado
        ==
        "ROSC"
    ):

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

ENERGIA:
{st.session_state.energia} J

TIEMPO:
{tiempo_total}

FECHA:
{datetime.now().strftime('%Y-%m-%d')}

HORA:
{datetime.now().strftime('%H:%M:%S')}
"""

    st.download_button(

        "📄 DESCARGAR RESUMEN",

        reporte,

        file_name="resumen_dea.txt"
    )

    if BD_PATH.exists():

        st.download_button(

            "⬇ DESCARGAR HISTORIAL JSON",

            BD_PATH.read_text(
                encoding="utf-8"
            ),

            "historial_simulaciones.json",

            "application/json"
        )

    if st.button(
        "🔄 NUEVA SIMULACIÓN"
    ):

        st.session_state.descargas = 0

        st.session_state.energia = 0

        st.session_state.resultado = ""

        st.session_state.inicio = None

        st.session_state.fin = None

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# ESTADISTICAS
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
            x
            for x in historial
            if x["resultado"] == "ROSC"
        ])

        porcentaje = round(
            (
                exitos
                /
                total
            )
            * 100,
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
            "Últimos eventos"
        )

        for evento in reversed(
            historial[-10:]
        ):

            st.markdown(
                f"""
**Fecha:** {evento['fecha']}

**Caso:** {evento['caso']}

**Resultado:** {evento['resultado']}
"""
            )

            st.markdown("---")

    if st.button(
        "⬅ VOLVER"
    ):

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# PIE DE PAGINA
# =====================================================

st.markdown(
"""
---

**SIMULADOR ACADÉMICO DEA**

Uso exclusivo para formación y entrenamiento.

No analiza ECG reales.

No controla hardware.

No sustituye formación clínica oficial.
"""
)
init()
