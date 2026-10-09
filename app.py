from datetime import datetime
from pathlib import Path

import base64
import json
import os
import random
import re
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
    page_title="Simulador DEA",
    layout="centered",
    initial_sidebar_state="collapsed",
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
    if not archivo.exists():
        archivo = ASSETS / "ECG" / nombre
    if not archivo.exists():
        archivo = ASSETS / "ecg" / nombre

    if archivo.exists():

        contenido = archivo.read_text(
            encoding="utf-8"
        )

        return (
            f'<div class="{clase}">'
            f'{contenido}'
            '</div>'
        )

    return f"""
    <div class="{clase}">
    SVG NO ENCONTRADO:
    {nombre}
    </div>
    """


def uri(nombre):

    archivo = ASSETS / nombre
    if not archivo.exists():
        archivo = ASSETS / "ECG" / nombre
    if not archivo.exists():
        archivo = ASSETS / "ecg" / nombre

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
# IA CON GROQ (uso sujeto a los límites de la cuenta)
# =====================================================
def responder_ia(pregunta):
    """Responde con Groq y mantiene el contexto reciente del chat."""
    try:
        from groq import Groq
    except ImportError:
        return (
            "Falta instalar la biblioteca de Groq. Añade 'groq' a "
            "requirements.txt y espera a que Streamlit Cloud termine el despliegue."
        )

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        try:
            api_key = str(st.secrets.get("GROQ_API_KEY", "")).strip()
        except Exception:
            api_key = ""

    if not api_key:
        return (
            "La IA todavía no está conectada. En Streamlit Cloud abre "
            "Settings → Secrets y configura GROQ_API_KEY = \"tu_clave_real\". "
            "No publiques ni compartas tu clave API."
        )

    instrucciones = """Eres un asistente educativo biomédico especializado en DEA, RCP, ECG y soporte vital básico. Responde en español claro, cercano y organizado. Comprende preguntas abiertas, explicaciones paso a paso, comparaciones, casos hipotéticos y preguntas de seguimiento. Usa el contexto reciente del chat, explica el porqué y reconoce honestamente cuando no sabes algo. Presenta las respuestas con títulos breves y listas numeradas o viñetas cuando ayuden a leer. Evita tablas anchas salvo que sean necesarias. No escribas etiquetas HTML como <br>, <div> o <p>; utiliza Markdown normal y saltos de línea. Usa negritas con moderación para destacar acciones importantes.

El propósito es educativo y no sustituye a personal sanitario ni formación certificada. Prioriza recomendaciones de guías clínicas reconocidas y aclara que los protocolos pueden variar. Si describen una emergencia real, indica llamar al servicio local de emergencias, iniciar RCP si corresponde y seguir las instrucciones del operador y del DEA. Nunca indiques tocar al paciente durante el análisis o la descarga. Después de una descarga, reanudar inmediatamente la RCP siguiendo las instrucciones del DEA y el protocolo local."""

    historial = st.session_state.get("chat", [])[-17:]
    if historial and historial[-1] == ("user", pregunta):
        historial = historial[:-1]

    mensajes = [{"role": "system", "content": instrucciones}]
    for rol, contenido in historial[-16:]:
        if not isinstance(contenido, str):
            continue
        role = "user" if rol == "user" else "assistant"
        mensajes.append({"role": role, "content": contenido})
    mensajes.append({"role": "user", "content": pregunta})

    modelo = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    cliente = Groq(api_key=api_key, timeout=35.0, max_retries=1)

    try:
        respuesta = cliente.chat.completions.create(
            model=modelo,
            messages=mensajes,
            temperature=0.4,
            max_completion_tokens=1200,
        )
        texto = respuesta.choices[0].message.content
        if texto and texto.strip():
            return texto.strip()
        return "No pude generar una respuesta. Intenta hacer la pregunta de otra manera."
    except Exception as error:
        nombre_error = type(error).__name__
        detalle = str(error).lower()
        if "401" in detalle or "authentication" in detalle or "invalid api key" in detalle:
            return "No se pudo autenticar con Groq. Revisa que GROQ_API_KEY esté copiada correctamente en Streamlit Cloud → Settings → Secrets."
        if "429" in detalle or "rate limit" in detalle or "quota" in detalle:
            return "Groq alcanzó temporalmente el límite de solicitudes o tokens de tu cuenta. Espera un poco y vuelve a intentarlo; no necesitas publicar tu clave."
        if any(codigo in detalle for codigo in ("500", "502", "503", "504")):
            return "El servicio de Groq está teniendo un problema temporal. Espera unos segundos y vuelve a intentarlo."
        return f"No pude completar la consulta con Groq ({nombre_error}). Comprueba tu conexión, la clave y el modelo configurado."


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
    st.markdown(svg("corazon_informacion.svg", "art icon-art"), unsafe_allow_html=True)


def icono_confirmacion():
    st.markdown(svg("corazon_confirmacion.svg", "art icon-art"), unsafe_allow_html=True)


def icono_descarga():
    st.markdown(svg("corazon_descarga.svg", "art icon-art"), unsafe_allow_html=True)


def mostrar_paciente():
    # Se reutiliza el corazón informativo disponible en el repositorio.
    st.markdown(svg("corazon_informacion.svg", "art icon-art"), unsafe_allow_html=True)


def mostrar_ecg(caso):
    if caso in RITMOS:
        st.markdown(svg(RITMOS[caso], "ecg-art"), unsafe_allow_html=True)
    else:
        st.info(f"Monitor ECG: {caso}")

def preparar_mensaje_chat(texto):
    """Normaliza saltos de línea HTML accidentales para que el chat se lea bien."""
    texto = str(texto or "")
    texto = re.sub(r"(?i)&lt;\s*br\s*/?\s*&gt;", "\n", texto)
    texto = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", texto)
    texto = re.sub(r"(?i)</\s*p\s*>", "\n\n", texto)
    texto = re.sub(r"(?i)<\s*p(?:\s+[^>]*)?>", "", texto)
    texto = re.sub(r"(?i)</?\s*div(?:\s+[^>]*)?>", "", texto)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.stApp{
    background:linear-gradient(135deg, #fbf8ff 0%, #f2eaff 48%, #f8f5ff 100%);
}

.block-container{
    max-width:1080px;
    padding-top: 1.6rem;
    padding-bottom: 2.8rem;
}

/* TEXTO */

html, body, p, span, label, li, h1, h2, h3, h4, h5, h6 {
    color: #30234a;
}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: #30234a !important;
    line-height: 1.7;
}

[data-testid="stMarkdownContainer"] strong {
    color: #4c268a !important;
}

[data-testid="stMarkdownContainer"] table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #ded0f5;
    background: #ffffff;
    color: #30234a !important;
    font-size: 0.94rem;
}

[data-testid="stMarkdownContainer"] thead tr th {
    background: #6d3bb5 !important;
    color: #ffffff !important;
    font-weight: 750;
    padding: 12px 14px !important;
    border-bottom: 1px solid #d8c5f4 !important;
}

[data-testid="stMarkdownContainer"] tbody tr td {
    background: #ffffff !important;
    color: #30234a !important;
    padding: 12px 14px !important;
    border-bottom: 1px solid #eee6fa !important;
}

[data-testid="stMarkdownContainer"] tbody tr:nth-child(even) td {
    background: #f7f2ff !important;
}

[data-testid="stMarkdownContainer"] tbody tr:last-child td {
    border-bottom: none !important;
}

/* LOGO */

.logo{

    text-align:center;

    display:flex;
    align-items:center;
    justify-content:center;
    gap:14px;
    font-size:clamp(30px, 4vw, 44px);
    font-weight:900;
    color:#54258b;
    margin: 0 auto 24px auto;
    letter-spacing:-0.8px;
}

.logo-icon {
    width:48px;
    height:48px;
    object-fit:contain;
}

.bolt{

    color:#ffb300;
}

/* PANEL */

.panel{

    background:linear-gradient(145deg, #ffffff 0%, #faf6ff 100%);

    border:1px solid #e1d1f7;

    border-radius:22px;
    box-shadow:0 12px 30px rgba(93, 52, 150, .10);

    padding:20px;

    margin-top:15px;
}

/* BOTONES */

.stButton > button{

    width:min(100%, 360px);
    min-height:54px;
    border:1px solid #8d65c7;
    border-radius:16px;
    background:linear-gradient(135deg, #ffffff 0%, #f5edff 100%);
    color:#4d267f;
    font-size:16px;
    font-weight:750;
    box-shadow:0 3px 10px rgba(20, 45, 75, .08);
    transition:all .18s ease;
}

.stButton {
    display:flex;
    justify-content:center;
}

.stButton > button:hover{

    background:linear-gradient(135deg, #7540b5 0%, #5c2d91 100%) !important;
    color:white !important;
    border-color:#7540b5 !important;
    transform:translateY(-1px);
}

/* BOTONES DE DESCARGA */
[data-testid="stDownloadButton"] > button {
    width: min(100%, 360px);
    min-height: 50px;
    border: 1px solid #8d65c7 !important;
    border-radius: 16px !important;
    background: linear-gradient(135deg, #7540b5 0%, #5c2d91 100%) !important;
    color: #ffffff !important;
    font-size: 15px;
    font-weight: 750;
    box-shadow: 0 5px 14px rgba(93, 52, 150, .18);
}
[data-testid="stDownloadButton"] > button p {
    color: #ffffff !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: linear-gradient(135deg, #8b5bc8 0%, #65359e 100%) !important;
    border-color: #8b5bc8 !important;
    transform: translateY(-1px);
}

/* SELECT */

div[data-baseweb="select"] * {
    color:#34234e !important;
}

div[data-baseweb="select"] > div {
    border-color:#cdb8eb !important;
    border-radius:14px !important;
    background:#ffffff !important;
}

/* SVG GENERALES */

.art{

    text-align:center;
}

.art svg{
    width:150px;
    max-height:150px;
    height:auto;
    display:block;
    margin:10px auto 18px auto;
}

.icon-art svg {
    width:86px;
    max-height:86px;
    margin:8px auto 16px auto;
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
    border:1px solid #e1d2f5;
    border-radius:18px;
    padding:18px 20px;
    margin-top:12px;
    background:linear-gradient(145deg, #ffffff 0%, #faf6ff 100%);
    box-shadow:0 8px 22px rgba(93,52,150,.08);
}

/* ALERTAS */

.warning{
    background:#fff7df;
    border:1px solid #e8c86b;
    border-radius:14px;
    padding:16px;
}

.ok{
    background:#e6f6ed;
    border:1px solid #8ccca7;
    border-radius:14px;
    padding:16px;
}

.stChatMessage {
    border-radius:18px;
    padding:12px 14px;
    margin-bottom:12px;
    border:1px solid #e5d8f7;
    background:rgba(255,255,255,.88);
    box-shadow:0 5px 16px rgba(93,52,150,.06);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background:#f0e7ff;
    border-color:#d7c2f5;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
    color:#30234a !important;
}

[data-testid="stChatInput"] textarea {
    border:1px solid #cbb3ec !important;
    border-radius:16px !important;
    background:#ffffff !important;
    color:#30234a !important;
}

[data-testid="stChatInput"] textarea:focus {
    border-color:#7a48b8 !important;
    box-shadow:0 0 0 2px rgba(122,72,184,.15) !important;
}

.stAlert {
    border-radius:16px !important;
}

@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .logo-icon { width:38px; height:38px; }
}

</style>
""",
unsafe_allow_html=True)


# =====================================================
# LOGO
# =====================================================

def logo():
    icono = uri("boton_encendido.svg")
    imagen = f'<img class="logo-icon" src="{icono}" alt="Encendido">' if icono else ""
    st.markdown(
        f'<div class="logo">{imagen}<span>Simulador DEA</span></div>',
        unsafe_allow_html=True,
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


    icono_info()

    st.subheader(
        "Simulador DEA"
    )

    st.write(
        "Entrenamiento educativo para reconocimiento de ritmos cardíacos y uso de desfibriladores externos automáticos."
    )

    if st.button(
        "APRENDIZAJE"
    ):

        st.session_state.pagina = (
            "APRENDIZAJE"
        )

        st.rerun()

    if st.button(
        "OPERAR DEA"
    ):

        reiniciar_simulacion()

        st.session_state.pagina = (
            "SIMULACION"
        )

        st.rerun()

    if st.button(
        "ESTADÍSTICAS"
    ):

        st.session_state.pagina = (
            "ESTADISTICAS"
        )

        st.rerun()



# =====================================================
# CENTRO DE APRENDIZAJE
# =====================================================

elif st.session_state.pagina == "APRENDIZAJE":


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
        "ABRIR ASISTENTE IA"
    ):

        st.session_state.pagina = (
            "CHAT"
        )

        st.rerun()

    if st.button(
        "VOLVER"
    ):

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()



# =====================================================
# CHAT IA
# =====================================================

elif st.session_state.pagina == "CHAT":


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
            st.markdown(preparar_mensaje_chat(mensaje) if "preparar_mensaje_chat" in globals() else mensaje)

    if st.button(
        "VOLVER"
    ):

        st.session_state.pagina = (
            "APRENDIZAJE"
        )

        st.rerun()



# =====================================================
# SIMULACIÓN DEA
# =====================================================

elif st.session_state.pagina == "SIMULACION":


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
            "Conecte el DEA al paciente para iniciar el análisis."
        )

        if st.button(
            "CONECTAR DEA"
        ):

            st.session_state.conectado = True

            st.rerun()

    # ==========================================
    # PASO 2 - DEA CONECTADO
    # ==========================================

    else:

        st.success(
            "DEA conectado correctamente."
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


# =====================================================
# DESCARGA DEA
# =====================================================

elif st.session_state.pagina == "DESCARGA":


    st.subheader(
        "DESCARGA RECOMENDADA"
    )

    icono_descarga()

    mostrar_ecg(
        st.session_state.caso
    )

    st.info(
        "Ritmo desfibrilable detectado. En esta simulación, pulse el botón morado "
        "para registrar la descarga educativa de 200 J."
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
        "APLICAR DESCARGA"
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



# =====================================================
# POST DESCARGA
# =====================================================

elif st.session_state.pagina == "POSTDESCARGA":

    if st.session_state.descargas > 0:
        st.success(
            f"Descarga aplicada correctamente: {st.session_state.descargas} "
            f"descarga(s), {st.session_state.energia} J acumulados."
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
            "Retorno de circulación espontánea"
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

        if st.session_state.descargas == 0:
            st.warning("NO SE ACONSEJA DESCARGA")
            st.markdown(
                """
<div class="warning">
El ritmo seleccionado no es desfibrilable en este escenario.
Continúe RCP y siga las indicaciones del DEA.
</div>
""",
                unsafe_allow_html=True
            )
        else:
            st.error("Persiste el ritmo inicial")
            st.markdown(
                """
<div class="warning">
La descarga quedó registrada, pero el ritmo persiste.
Continúe RCP y vuelva a analizar cuando el simulador lo indique.
</div>
""",
                unsafe_allow_html=True
            )

        mostrar_ecg(
            st.session_state.caso
        )

    st.markdown("---")

    if st.session_state.resultado != "ROSC":
        if st.button("REANALIZAR DEA Y CONTINUAR RCP"):
            st.session_state.pagina = "SIMULACION"
            st.session_state.conectado = True
            st.session_state.analizado = False
            st.rerun()

    if st.button(
        "VER RESUMEN"
    ):

        st.session_state.pagina = (
            "RESUMEN"
        )

        st.rerun()



# =====================================================
# RESUMEN
# =====================================================

elif st.session_state.pagina == "RESUMEN":


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

        "DESCARGAR RESUMEN",

        reporte,

        file_name="resumen_dea.txt"
    )

    if BD_PATH.exists():

        st.download_button(

            "DESCARGAR HISTORIAL JSON",

            BD_PATH.read_text(
                encoding="utf-8"
            ),

            file_name=
            "historial_simulaciones.json",

            mime=
            "application/json"
        )

    if st.button(
        "NUEVA SIMULACIÓN"
    ):

        reiniciar_simulacion()

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()



# =====================================================
# ESTADISTICAS
# =====================================================

elif st.session_state.pagina == "ESTADISTICAS":


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
        "VOLVER"
    ):

        st.session_state.pagina = (
            "MENU"
        )

        st.rerun()

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
