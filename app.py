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
# =====================================================
# MOTOR IA LOCAL
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
        "taquicardia ventricular"
    ],

    "asistolia": [
        "asistolia",
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
        "retorno de la circulacion",
        "circulación espontánea"
    ]
}


def responder_ia(pregunta):

    pregunta = pregunta.lower()

    if fuzz is None:

        for tema in TOPICOS:

            if tema in pregunta:
                return BASE_CONOCIMIENTO[tema]

        return """
Puedo responder preguntas sobre:

• DEA
• FV
• TVSP
• AESP
• Asistolia
• RCP
• ROSC
"""

    mejor_tema = None
    mejor_score = 0

    for tema, palabras in TOPICOS.items():

        texto = " ".join(palabras)

        score = fuzz.partial_ratio(
            pregunta,
            texto
        )

        if score > mejor_score:

            mejor_score = score
            mejor_tema = tema

    if mejor_score > 45:
        return BASE_CONOCIMIENTO[mejor_tema]

    return """
No encontré una coincidencia exacta.

Temas disponibles:

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
# ESTADO GLOBAL
# =====================================================

def init():

    defaults = {

        "pagina":
        "MENU",

        "chat":
        [],

        "inicio":
        None,

        "fin":
        None,

        "descargas":
        0,

        "energia":
        0,

        "resultado":
        "",

        "caso":
        "Fibrilación ventricular"
    }

    for k, v in defaults.items():

        st.session_state.setdefault(
            k,
            v
        )


init()


# =====================================================
# CSS PROFESIONAL
# =====================================================

st.markdown(
"""
<style>

/* APP */

.stApp{
background:#ececec;
}

/* LOGO */

.logo{
text-align:center;
font-size:42px;
font-weight:900;
margin-bottom:20px;
}

.bolt{
color:#ffbf00;
}

/* CONTENEDORES */

.panel{

background:white;

border:4px solid black;

border-radius:25px;

padding:25px;

margin-top:15px;
}

/* BOTONES */

.stButton button{

width:100%;

height:58px;

border:3px solid black;

border-radius:12px;

background:white;

font-size:18px;

font-weight:800;

transition:0.2s;
}

.stButton button:hover{

background:black;

color:white;
}

/* PACIENTE */

.human{

display:flex;

flex-direction:column;

align-items:center;

margin:25px;
}

.head{

width:90px;

height:90px;

border-radius:50%;

background:black;
}

.body{

width:180px;

height:260px;

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

position:absolute;

width:28px;

height:28px;

background:#d72626;
}

.patch1{
top:30px;
left:30px;
}

.patch2{
top:110px;
right:30px;
}

/* ECG */

.ecg-container{

height:120px;

width:100%;

background:black;

border-radius:15px;

overflow:hidden;

position:relative;

margin-top:20px;
}

.ecg-track{

position:absolute;

width:200%;

height:100%;

animation:scroll 3s linear infinite;
}

/* SINUSAL */

.sinusal{

width:100%;
height:100%;

background:#00ff66;

clip-path:polygon(

0% 50%,
10% 50%,
15% 40%,
17% 60%,
19% 50%,
25% 50%,
28% 10%,
30% 90%,
32% 0%,
34% 50%,
45% 50%,
100% 50%

);
}

/* FV */

.fv{

width:100%;
height:100%;

background:#00ff66;

clip-path:polygon(

0% 60%,
3% 25%,
6% 80%,
9% 30%,
12% 70%,
15% 25%,
18% 80%,
21% 35%,
24% 85%,
27% 20%,
30% 70%,
33% 30%,
36% 90%,
39% 20%,
42% 75%,
45% 35%,
48% 85%,
51% 20%,
54% 70%,
57% 40%,
60% 80%,
63% 25%,
66% 75%,
69% 20%,
72% 90%,
75% 35%,
78% 75%,
81% 20%,
84% 80%,
87% 35%,
90% 70%,
93% 30%,
96% 60%,
100% 50%

);
}

/* TV */

.tv{

width:100%;
height:100%;

background:#00ff66;

clip-path:polygon(

0% 50%,

10% 90%,
20% 10%,
30% 90%,
40% 10%,
50% 90%,
60% 10%,
70% 90%,
80% 10%,
90% 90%,

100% 50%

);
}

/* ASISTOLIA */

.asistolia{

width:100%;
height:100%;

background:#00ff66;

clip-path:polygon(

0% 50%,
100% 50%

);
}

/* AESP */

.aesp{

width:100%;
height:100%;

background:#00ff66;

clip-path:polygon(

0% 50%,

15% 50%,
18% 30%,
20% 70%,
22% 50%,

40% 50%,

43% 25%,
45% 75%,
47% 50%,

70% 50%,

73% 30%,
75% 70%,
77% 50%,

100% 50%

);
}

@keyframes scroll{

from{
transform:translateX(0%);
}

to{
transform:translateX(-50%);
}

}

</style>
""",
unsafe_allow_html=True
)


# =====================================================
# COMPONENTES VISUALES
# =====================================================

def logo():

    st.markdown(
    """
    <div class='logo'>
    DESFIBRILAD
    <span class='bolt'>⚡</span>
    R
    </div>
    """,
    unsafe_allow_html=True
    )


def paciente():

    st.markdown(
    """
    <div class='human'>

        <div class='head'></div>

        <div class='body'>

            <div class='patch patch1'></div>

            <div class='patch patch2'></div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
    )


def mostrar_ecg(tipo):

    clase = {

        "Fibrilación ventricular":
        "fv",

        "TV sin pulso":
        "tv",

        "Asistolia":
        "asistolia",

        "AESP":
        "aesp",

        "Ritmo sinusal":
        "sinusal"

    }.get(tipo, "sinusal")

    st.markdown(
    f"""
    <div class="ecg-container">

        <div class="ecg-track">

            <div class="{clase}"></div>

        </div>

    </div>
    """,
    unsafe_allow_html=True
    )  
    # =====================================================
# CASOS CLÍNICOS
# =====================================================

CASOS = {

    "Fibrilación ventricular": {

        "conciencia":
        "Inconsciente",

        "respiracion":
        "Agónica",

        "pulso":
        "Ausente",

        "descarga":
        True
    },

    "TV sin pulso": {

        "conciencia":
        "Inconsciente",

        "respiracion":
        "Ausente",

        "pulso":
        "Ausente",

        "descarga":
        True
    },

    "Asistolia": {

        "conciencia":
        "Inconsciente",

        "respiracion":
        "Ausente",

        "pulso":
        "Ausente",

        "descarga":
        False
    },

    "AESP": {

        "conciencia":
        "Inconsciente",

        "respiracion":
        "Agónica",

        "pulso":
        "Ausente",

        "descarga":
        False
    }
}


# =====================================================
# LOGO
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

    st.subheader(
        "Simulador Académico DEA"
    )

    st.write(
        "Entrenamiento virtual y educativo."
    )

    if st.button("📚 Aprendizaje"):
        st.session_state.pagina = "APRENDIZAJE"
        st.rerun()

    if st.button("⚡ Operar DEA"):
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

- ¿Qué es un DEA?
- ¿Qué es la fibrilación ventricular?
- ¿Qué es una TV sin pulso?
- ¿Qué significa ROSC?
- ¿Qué es la AESP?
- ¿Cuándo se realiza RCP?
- ¿Por qué la asistolia no se desfibrila?
""")

    if st.button("🤖 Abrir Asistente IA"):
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

    for rol, texto in st.session_state.chat:

        with st.chat_message(rol):

            st.write(texto)

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
        "Preparación del usuario"
    )

    paciente()

    caso = st.selectbox(
        "Caso clínico",
        list(CASOS.keys())
    )

    st.session_state.caso = caso

    info = CASOS[caso]

    st.info(
        f"""
Estado: {info['conciencia']}
Respiración: {info['respiracion']}
Pulso: {info['pulso']}
"""
    )

    mostrar_ecg(caso)

    if st.button(
        "ANALIZAR"
    ):

        st.session_state.inicio = datetime.now()

        barra = st.progress(0)

        for i in range(100):

            barra.progress(
                i + 1
            )

            time.sleep(
                0.01
            )

        if info["descarga"]:

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
                st.session_state.resultado,

                "descargas":
                0,

                "energia":
                0
            })

            st.session_state.pagina = \
                "RESUMEN"

        st.rerun()

    if st.button("⬅ Volver"):

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

    if st.button("⚡ APLICAR DESCARGA"):

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

        st.session_state.fin = \
            datetime.now()

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
            "✅ Circulación espontánea recuperada"
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
        "VER RESUMEN"
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
        "Resumen del evento"
    )

    tiempo = "0:00:00"

    if (
        st.session_state.inicio
        and
        st.session_state.fin
    ):

        tiempo = str(
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
        f"**Tiempo:** {tiempo}"
    )

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

ENERGIA:
{st.session_state.energia} J

TIEMPO:
{tiempo}

FECHA:
{datetime.now()}
"""

    st.download_button(

        "📄 Descargar resumen TXT",

        reporte,

        file_name=
        "resumen_dea.txt"
    )

    if st.button(
        "Nueva simulación"
    ):

        st.session_state.descargas = 0

        st.session_state.energia = 0

        st.session_state.resultado = ""

        st.session_state.inicio = None

        st.session_state.fin = None

        st.session_state.pagina = "MENU"

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

    datos = cargar_historial()

    total = len(datos)

    st.metric(
        "Total simulaciones",
        total
    )

    if total > 0:

        exitos = len(

            [
                x for x in datos

                if x["resultado"] == "ROSC"
            ]
        )

        st.metric(
            "ROSC",
            exitos
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
            "% éxito",
            porcentaje
        )

        st.markdown(
            "---"
        )

        st.write(
            "Últimos registros"
        )

        for evento in reversed(
            datos[-10:]
        ):

            st.write(

                f"""
📅 {evento['fecha']}

Caso: {evento['caso']}

Resultado: {evento['resultado']}
"""
            )

        st.download_button(

            "⬇ Descargar base JSON",

            json.dumps(
                datos,
                indent=4,
                ensure_ascii=False
            ),

            file_name=
            "historial_simulaciones.json",

            mime=
            "application/json"
        )

    else:

        st.info(
            "No hay simulaciones almacenadas."
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
Simulador académico DEA.

No interpreta señales reales.

No controla hardware biomédico.

Uso exclusivamente educativo.
"""
)
