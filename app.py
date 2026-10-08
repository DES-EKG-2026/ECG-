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
# ECG ORIGINALES
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
# HISTORIAL JSON
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
# PREGUNTAS FRECUENTES
# =====================================================

PREGUNTAS_FRECUENTES = [

    "¿Qué ritmos cardíacos son desfibrilables por un DEA?",

    "¿Por qué la asistolia y la AESP no se desfibrilan?",

    "¿Qué diferencia hay entre FV y TVSP?",

    "¿Cómo detecta el DEA si un ritmo es desfibrilable?",

    "¿Qué pasa si muevo al paciente mientras el DEA analiza?",

    "¿Por qué el DEA pide que nadie toque al paciente?",

    "¿Qué se debe hacer inmediatamente después de una descarga?",

    "¿Cuántas descargas máximas administra seguidas un DEA?",

    "¿Qué significa cuando el DEA dice no se aconseja descarga?"
]


# =====================================================
# BASE DE CONOCIMIENTO IA
# =====================================================

BASE_CONOCIMIENTO = {

    "ritmos_desfibrilables":
    """
Los ritmos desfibrilables son:

- Fibrilación Ventricular (FV)

- Taquicardia Ventricular sin Pulso (TVSP)

Son los únicos ritmos que un DEA recomienda desfibrilar.
""",

    "asistolia_aesp":
    """
La asistolia y la AESP no son ritmos desfibrilables.

La descarga eléctrica no aporta beneficio porque no existe una actividad susceptible de reorganizarse mediante desfibrilación.
""",

    "fv_tvsp":
    """
FV:
- Actividad completamente caótica.

TVSP:
- Ritmo rápido y organizado.

Ambos producen ausencia de circulación efectiva.
""",

    "analisis_dea":
    """
El DEA analiza la actividad eléctrica mediante los parches colocados en el tórax.

Posteriormente aplica algoritmos para decidir si la descarga es apropiada.
""",

    "movimiento":
    """
Mover al paciente durante el análisis puede producir artefactos eléctricos y errores de interpretación.
""",

    "nadie_toque":
    """
Nadie debe tocar al paciente durante el análisis ni durante la descarga.

Esto evita errores de lectura y aumenta la seguridad.
""",

    "post_descarga":
    """
Después de una descarga debe reiniciarse inmediatamente la RCP durante aproximadamente 2 minutos.
""",

    "numero_descargas":
    """
El DEA realiza ciclos de análisis.

Tras cada ciclo decide nuevamente si la descarga está indicada.
""",

    "no_descarga":
    """
Cuando el DEA dice 'No se aconseja descarga' significa que el ritmo detectado no es desfibrilable.

Debe continuarse la RCP.
"""
}


# =====================================================
# PALABRAS CLAVE
# =====================================================

TOPICOS = {

    "ritmos_desfibrilables":[
        "ritmos desfibrilables",
        "ritmo desfibrilable",
        "que ritmos desfibrila"
    ],

    "asistolia_aesp":[
        "asistolia",
        "aesp",
        "no se desfibrilan"
    ],

    "fv_tvsp":[
        "fv y tvsp",
        "diferencia fv y tvsp"
    ],

    "analisis_dea":[
        "como detecta el dea",
        "analisis del dea"
    ],

    "movimiento":[
        "muevo al paciente",
        "movimiento durante analisis"
    ],

    "nadie_toque":[
        "nadie toque",
        "despejar area"
    ],

    "post_descarga":[
        "despues de descarga",
        "despues del choque"
    ],

    "numero_descargas":[
        "cuantas descargas"
    ],

    "no_descarga":[
        "no se aconseja descarga"
    ]
}


# =====================================================
# IA LOCAL
# =====================================================

def responder_ia(pregunta):

    pregunta = pregunta.lower()

    if fuzz:

        mejor = None

        score_max = 0

        for tema, palabras in TOPICOS.items():

            score = fuzz.partial_ratio(

                pregunta,

                " ".join(palabras)

            )

            if score > score_max:

                score_max = score

                mejor = tema

        if mejor:

            return BASE_CONOCIMIENTO[mejor]

    return """
Pregunte sobre:

- DEA
- FV
- TVSP
- AESP
- Asistolia
- Descargas
- RCP
- ROSC
"""


# =====================================================
# SESSION STATE
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

        "energia": 0,

        "conectado": False,

        "analizado": False,

        "descarga_recomendada": False
    }

    for clave, valor in defaults.items():

        if clave not in st.session_state:

            st.session_state[clave] = valor


init()

# =====================================================
# FUNCIONES FALTANTES AGREGADAS (Para evitar errores)
# =====================================================

def reiniciar_simulacion():
    st.session_state.inicio = datetime.now()
    st.session_state.fin = None
    st.session_state.resultado = ""
    st.session_state.descargas = 0
    st.session_state.energia = 0
    st.session_state.conectado = False
    st.session_state.analizado = False
    st.session_state.descarga_recomendada = False

def icono_info():
    st.markdown("<div style='text-align:center; font-size:40px;'>ℹ️</div>", unsafe_allow_html=True)

def icono_confirmacion():
    st.markdown("<div style='text-align:center; font-size:40px;'>✅</div>", unsafe_allow_html=True)

def mostrar_paciente():
    st.markdown("<div style='text-align:center; font-size:50px;'>🧍‍♂️</div>", unsafe_allow_html=True)

def mostrar_ecg(caso):
    if caso in RITMOS:
        st.markdown(svg(RITMOS[caso], "ecg-art"), unsafe_allow_html=True)
    else:
        st.info(f"Monitor ECG: {caso}")

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.stApp{
    background:#eeeeee;
}

.block-container{
    max-width:900px;
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

    margin-bottom:15px;
}

.bolt{

    color:#ffb300;
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

    border-radius:12px;

    background:white;

    color:black;

    font-size:18px;

    font-weight:800;
}

.stButton > button:hover{

    background:black !important;

    color:white !important;
}

/* SELECT */

div[data-baseweb="select"] *{

    color:black !important;
}

/* SVG GENERALES */

.art{

    text-align:center;
}

.art svg{

    width:220px;

    height:auto;

    display:block;

    margin:auto;
}

/* ECG */

.ecg-art{

    width:100%;
}

.ecg-art svg{

    width:100%;

    height:160px;

    display:block;
}

/* INFORMACIÓN */

.info{

    border:2px solid black;

    border-radius:12px;

    padding:12px;

    margin-top:10px;

    background:white;
}

/* ALERTAS */

.warning{

    background:#fff3cd;

    border:2px solid #d4a900;

    border-radius:12px;

    padding:12px;
}

.ok{

    background:#d4edda;

    border:2px solid #198754;

    border-radius:12px;

    padding:12px;
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
            <span class="bolt">⚡</span> Simulador DEA
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

    icono_info()

    st.subheader(
        "Simulador DEA"
    )

    st.write(
        "Entrenamiento educativo para reconocimiento de ritmos cardíacos y uso de desfibriladores externos automáticos."
    )

    if st.button(
        "📚 APRENDIZAJE"
    ):

        st.session_state.pagina = (
            "APRENDIZAJE"
        )

        st.rerun()

    if st.button(
        "⚡ OPERAR DEA"
    ):

        reiniciar_simulacion()

        st.session_state.pagina = (
            "SIMULACION"
        )

        st.rerun()

    if st.button(
        "📊 ESTADÍSTICAS"
    ):

        st.session_state.pagina = (
            "ESTADISTICAS"
        )

        st.rerun()

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )


# =====================================================
# CENTRO DE APRENDIZAJE
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

    st.markdown("""
### Temas disponibles

- DEA

- Fibrilación Ventricular

- TV sin Pulso

- AESP

- Asistolia

- RCP

- ROSC

- ACLS

- ECG

- Desfibrilación
""")

    if st.button(
        "🤖 ABRIR ASISTENTE IA"
    ):

        st.session_state.pagina = (
            "CHAT"
        )

        st.rerun()

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

    st.markdown(
        "### Preguntas frecuentes"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Ritmos desfibrilables"
        ):

            pregunta = (
                "¿Qué ritmos cardíacos son desfibrilables por un DEA?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "FV vs TVSP"
        ):

            pregunta = (
                "¿Qué diferencia hay entre FV y TVSP?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "¿Cómo analiza el DEA?"
        ):

            pregunta = (
                "¿Cómo detecta el DEA si un ritmo es desfibrilable?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "Después de la descarga"
        ):

            pregunta = (
                "¿Qué se debe hacer inmediatamente después de una descarga?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

    with col2:

        if st.button(
            "AESP y Asistolia"
        ):

            pregunta = (
                "¿Por qué la asistolia y la AESP no se desfibrilan?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "¿Mover paciente?"
        ):

            pregunta = (
                "¿Qué pasa si muevo al paciente mientras el DEA analiza?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "¿Por qué nadie toca?"
        ):

            pregunta = (
                "¿Por qué el DEA pide que nadie toque al paciente?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

        if st.button(
            "No se aconseja descarga"
        ):

            pregunta = (
                "¿Qué significa cuando el DEA dice no se aconseja descarga?"
            )

            st.session_state.chat.append(
                ("user", pregunta)
            )

            st.session_state.chat.append(
                (
                    "assistant",
                    responder_ia(
                        pregunta
                    )
                )
            )

    pregunta = st.chat_input(
        "Escriba una pregunta..."
    )

    if pregunta:

        st.session_state.chat.append(
            ("user", pregunta)
        )

        st.session_state.chat.append(
            (
                "assistant",
                responder_ia(
                    pregunta
                )
            )
        )

    for rol, mensaje in st.session_state.chat:

        with st.chat_message(rol):

            st.write(mensaje)

    if st.button(
        "⬅ VOLVER"
    ):

        st.session_state.pagina = (
            "APRENDIZAJE"
        )

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

    st.markdown("---")

    # ==========================================
    # PASO 1 - CONECTAR DEA
    # ==========================================

    if not st.session_state.conectado:

        st.warning(
            "🔌 Conecte el DEA al paciente para iniciar el análisis."
        )

        if st.button(
            "🔌 CONECTAR DEA"
        ):

            st.session_state.conectado = True

            st.rerun()

    # ==========================================
    # PASO 2 - DEA CONECTADO
    # ==========================================

    else:

        st.success(
            "✅ DEA conectado correctamente."
        )

        st.markdown(
            "### Monitor ECG"
        )

        mostrar_ecg(caso)

        st.info(
            "Paciente conectado. Puede iniciar el análisis."
        )

        # ======================================
        # ANALIZAR
        # ======================================

        if st.button("ANALIZAR"):

            st.session_state.analizado = True

            if datos["desfibrilable"]:
                st.session_state.pagina = "DESCARGA"
            else:
                st.session_state.resultado = "Persistencia del ritmo"
                st.session_state.pagina = "POSTDESCARGA"

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

    mostrar_ecg(
        st.session_state.caso
    )

    st.markdown(
        """
<div class="warning">

<b>DESCARGA RECOMENDADA</b>

El DEA ha detectado un ritmo desfibrilable.

Asegúrese de que nadie toque al paciente.

</div>
""",
        unsafe_allow_html=True
    )

    if st.button(
        "⚡ APLICAR DESCARGA"
    ):

        st.session_state.descargas += 1

        st.session_state.energia += 200

        with st.spinner(
            "Aplicando descarga..."
        ):

            time.sleep(2)

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

    # ----------------------------------------------
    # ROSC
    # ----------------------------------------------

    if (
        st.session_state.resultado
        ==
        "ROSC"
    ):

        icono_confirmacion()

        st.success(
            "✅ Retorno de circulación espontánea"
        )

        st.markdown(
            """
<div class="ok">

El paciente presenta recuperación
de la circulación espontánea.

</div>
""",
            unsafe_allow_html=True
        )

        mostrar_ecg(
            "Ritmo sinusal"
        )

    # ----------------------------------------------
    # SIN ROSC
    # ----------------------------------------------

    else:

        icono_info()

        st.error(
            "❌ Persiste el ritmo inicial"
        )

        st.markdown(
            """
<div class="warning">

La reanimación debe continuar.

El DEA volverá a requerir un análisis.

</div>
""",
            unsafe_allow_html=True
        )

        mostrar_ecg(
            st.session_state.caso
        )

    st.markdown("---")

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

            file_name=
            "historial_simulaciones.json",

            mime=
            "application/json"
        )

    if st.button(
        "🔄 NUEVA SIMULACIÓN"
    ):

        reiniciar_simulacion()

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
        "Total simulaciones",
        total
    )

    if total > 0:

        exitos = len(

            [
                x
                for x in historial

                if x["resultado"] == "ROSC"
            ]
        )

        porcentaje = round(

            exitos
            /
            total
            *
            100,

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

    else:

        st.warning(
            "Todavía no existen simulaciones registradas."
        )

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
# FOOTER
# =====================================================

st.markdown(
"""
---

### Simulador Académico DEA

Uso exclusivamente educativo.

No interpreta ECG reales.

No controla dispositivos biomédicos.

No sustituye entrenamiento clínico certificado.
"""
)
