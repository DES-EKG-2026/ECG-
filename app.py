"""
Simulador académico de DEA con Asistente IA y Base de Datos.
No interpreta señales reales ni controla hardware.
"""
from datetime import datetime
from pathlib import Path
import base64
import json
import random
import time
import streamlit as st

# Los archivos SVG están en la misma carpeta que app.py (raíz)
ASSETS = Path(__file__).parent 
BD_PATH = Path(__file__).parent / "historial_simulaciones.json"

# Nombres ajustados exactamente a los archivos de tu repositorio
RITMOS = {
    "Fibrilación ventricular": {"svg": "ecg_fibrilacion_ventricular.svg", "descarga": True},
    "Taquicardia ventricular sin pulso": {"svg": "ecg_taquicardia_ventricular.svg", "descarga": True},
    "Asistolia": {"svg": "ecg_asistolia.svg", "descarga": False},
    "Actividad eléctrica sin pulso (AESP)": {"svg": "ecg_aesp.svg", "descarga": False},
    "Ritmo sinusal": {"svg": "senal_ecg.svg", "descarga": False},
    "Bradicardia sinusal": {"svg": "ecg_bradicardia.svg", "descarga": False},
    "Taquicardia sinusal con pulso": {"svg": "ecg_taquicardia_sinusal.svg", "descarga": False},
    "Extrasístoles": {"svg": "ecg_etrasistole.svg", "descarga": False}, # Corregido al nombre de tu archivo
}

CASOS = {
    "Fibrilación ventricular": dict(ritmo="Fibrilación ventricular", conciencia="Inconsciente", respiracion="Agónica", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "TV sin pulso": dict(ritmo="Taquicardia ventricular sin pulso", conciencia="Inconsciente", respiracion="Ausente", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "Asistolia": dict(ritmo="Asistolia", conciencia="Inconsciente", respiracion="Ausente", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "AESP": dict(ritmo="Actividad eléctrica sin pulso (AESP)", conciencia="Inconsciente", respiracion="Agónica", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "Recuperación posterior": dict(ritmo="Ritmo sinusal", conciencia="Somnoliento", respiracion="Normal", pulso="Presente", saturacion="96%", presion="110/70 mmHg"),
}

EPICRISIS = {
    "FV con recuperación": "Usuario simulado inconsciente, con respiración agónica y sin pulso. El DEA identifica fibrilación ventricular, recomienda 200 J virtuales y, tras la descarga, el caso evoluciona a ritmo sinusal con circulación simulada restablecida.",
    "FV persistente": "Usuario simulado inconsciente y sin pulso. Tras una primera descarga virtual de 200 J persiste la fibrilación ventricular. El ejercicio indica continuar el protocolo docente y reevaluar el ritmo.",
    "TV sin pulso": "Usuario simulado inconsciente, sin pulso y con complejos rápidos y anchos. Se aplica una descarga virtual y se registra recuperación o persistencia según el desenlace configurado.",
    "Asistolia": "Usuario simulado inconsciente, sin respiración normal y sin pulso. El ECG muestra una línea casi plana; la aplicación bloquea la descarga y orienta continuar el protocolo del curso.",
    "AESP": "El monitor muestra actividad eléctrica organizada, pero el usuario simulado no tiene pulso ni presión detectable. Se clasifica como actividad eléctrica sin pulso y no se habilita la descarga.",
}

SATURACIONES = ["No detectable", "70%", "75%", "80%", "85%", "90%", "94%", "96%", "98%"]
PRESIONES = ["No detectable", "70/40 mmHg", "80/50 mmHg", "90/60 mmHg", "100/60 mmHg", "110/70 mmHg", "120/80 mmHg", "140/90 mmHg"]

# --- FUNCIONES DE BASE DE DATOS Y ASISTENTE IA ---

def guardar_en_bd(registro_datos):
    """Guarda cada resultado de simulación en una base de datos local JSON."""
    datos = []
    if BD_PATH.exists():
        try:
            datos = json.loads(BD_PATH.read_text(encoding="utf-8"))
        except Exception:
            datos = []
    datos.append(registro_datos)
    BD_PATH.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")

def responder_ia(pregunta):
    """Motor de IA básica para responder consultas sobre protocolos biomédicos."""
    p = pregunta.lower()
    if any(k in p for k in ["desfibrilable", "descarga", "choque"]):
        return "🤖 **Asistente IA:** Los ritmos desfibrilables son la **Fibrilación Ventricular (FV)** y la **Taquicardia Ventricular sin pulso (TVsp)**. La Asistolia y la AESP NO deben recibir descarga."
    elif any(k in p for k in ["parche", "electrodo", "donde", "colocar"]):
        return "🤖 **Asistente IA:** Coloque un parche debajo de la clavícula derecha y el otro en la línea axilar media izquierda del tórax del usuario."
    elif any(k in p for k in ["rcp", "reanimacion", "compresion"]):
        return "🤖 **Asistente IA:** Si la descarga no es recomendada o tras administrarla, inicie RCP inmediatamente (30 compresiones por 2 insuflaciones) a una frecuencia de 100-120 cpm."
    elif any(k in p for k in ["asistolia", "aesp", "sinusal"]):
        return "🤖 **Asistente IA:** La Asistolia y la AESP son ritmos de paro no desfibrilables. Debe mantenerse la RCP continua y verificar el ritmo cada 2 minutos."
    else:
        return "🤖 **Asistente IA:** Hola. Puedo responder dudas sobre ritmos desfibrilables, uso de parches, secuencias de RCP y protocolos de DEA."

# --- CONTROL DE ESTADO E INTERFAZ ---

def init():
    defaults = {
        "estado": "APAGADO", "modo": "Caso predeterminado", "caso": "Fibrilación ventricular",
        "ritmo": "Fibrilación ventricular", "conciencia": "Inconsciente", "respiracion": "Agónica",
        "pulso": "Ausente", "saturacion": "No detectable", "presion": "No detectable",
        "desenlace": "Selección aleatoria", "descargas": 0, "energia": 0, "inicio": None,
        "fin": None, "resultado": "Pendiente", "registro": []
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

def log(texto):
    st.session_state.registro.append(f"{datetime.now().strftime('%H:%M:%S')} - {texto}")

def reset():
    for key in list(st.session_state):
        del st.session_state[key]

def svg(nombre, clase="art"):
    archivo = ASSETS / nombre
    if archivo.exists():
        return f'<div class="{clase}">{archivo.read_text(encoding="utf-8")}</div>'
    return f'<div class="{clase}">[SVG no encontrado: {nombre}]</div>'

def uri(nombre):
    archivo = ASSETS / nombre
    if archivo.exists():
        return "data:image/svg+xml;base64," + base64.b64encode(archivo.read_bytes()).decode("ascii")
    return ""

def screen(title="", subtitle="", art=""):
    html_content = f'<div class="screen"><div class="brand">DESFIBRILAD<span>⚡</span>R</div><h1>{title}</h1><h2>{subtitle}</h2>{art}</div>'
    st.markdown(html_content, unsafe_allow_html=True)

def ir(estado):
    st.session_state.estado = estado
    st.rerun()

st.set_page_config(page_title="Simulador DEA", page_icon="⚡", layout="centered")
init()

# CSS corregido para botones claros/oscuros y contraste garantizado
st.markdown('''<style>
[data-testid="stHeader"], [data-testid="stToolbar"] {display:none}
.stApp{background:#eee;color:#111}
.block-container{max-width: 440px; padding: 8px}
.phone{background:#fff;border:2px solid #111;border-radius: 30px; padding: 13px 15px 24px; min-height: 700px; box-shadow:0 15px 35px #0002}
.speaker{width: 90px; height: 5px; border-radius: 5px; background: #111;margin: 2px auto 10px}
.note{text-align:center;color:#666; font:10px Arial;letter-spacing:1px; margin-bottom:8px}
.screen{position:relative; min-height: 390px; border:2px solid #111; border-radius: 18px; display: flex; flex-direction:column; align-items:center; justify-content: center; text-align:center;padding: 18px; margin-bottom: 12px}
.brand{position:absolute; top: 13px; font:800 20px Arial; color:#111}
.brand span{color:#c52828; font-size:25px}
.screen h1{font:800 28px/1 Arial; margin:8px 0; text-transform:uppercase; color:#111}
.screen h2{font:700 18px/1.2 Arial; margin:5px 0; white-space: pre-line; color:#111}

/* BOTONES DE STREAMLIT CORREGIDOS */
.stButton>button, .stDownloadButton>button {
    width: 100% !important;
    min-height: 52px !important;
    border: 2px solid #111 !important;
    border-radius: 5px !important;
    background-color: #ffffff !important;
    color: #111111 !important;
    font: 800 19px Arial !important;
    text-transform: uppercase !important;
}

/* Botones principales/destacados con texto blanco legible */
.stButton>button[kind="primary"] {
    background-color: #111111 !important;
    color: #ffffff !important;
}

.st-key-power button {
    width: 100px !important;
    height: 100px !important;
    min-height: 100px !important;
    border-radius: 50% !important;
    margin: 18px auto !important;
    display: block !important;
    font-size: 0px !important;
}

.st-key-shock button {
    height: 165px !important;
    border-radius: 85px !important;
    font-size: 0px !important;
}

/* ELEMENTOS GRÁFICOS */
.art svg{width: 185px;height:215px; margin-top: 10px}
.ecg-art svg{width:100%;height: 130px; margin-top:10px}
.info{border:1.5px solid #111;padding:11px; border-radius:5px; margin:7px 0;font: 13px/1.4 Arial; color:#111}
.info b{display:block; text-transform:uppercase; margin-bottom:4px}
.event{width: 100%; border-collapse:collapse; font:12px Arial; color:#111}
.event td{border:1.4px solid #111;padding:7px 11px}
.event td:first-child{font-weight:bold; text-transform:uppercase; width: 45%}
.parameter{font:bold 12px Arial; text-transform:uppercase; margin:9px 0 3px; color:#111}
.warning{font:11px/1.4 Arial; background:#fff2d9;border:1px solid #c78217; padding: 9px; border-radius: 5px; margin:8px 0; color:#111}
.ok{font:12px/1.4 Arial;background:#e8f7ef; border: 1px solid #25814f;padding:9px;border-radius: 5px; margin:8px 0; color:#111}

/* ETIQUETAS Y SELECCIONABLES EN FORMAS */
label, p, span, div[data-testid="stWidgetLabel"] p {
    color: #111111 !important;
    font-weight: bold !important;
}
div[data-baseweb="select"] > div {
    border: 2px solid #111 !important;
    min-height: 48px;
    background-color: #ffffff !important;
    color: #111111 !important;
}
div[data-baseweb="select"] span {
    color: #111111 !important;
}
div[role="listbox"] div {
    color: #111111 !important;
}

@media (max-width: 480px) {
    .block-container{padding:0}
    .phone{border:0;border-radius:0;box-shadow: none; min-height:100vh}
}
</style>''', unsafe_allow_html=True)

img_encendido = uri('boton_encendido.svg')
img_descarga = uri('corazon_descarga.svg')

st.markdown(f'''<style>
.st-key-power button {{
    background-color: #fff !important;
    background-image: url("{img_encendido}") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 70px 70px !important;
}}
.st-key-shock button {{
    background-color: #fff !important;
    background-image: url("{img_descarga}") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 140px 140px !important;
    border: 0 !important;
}}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="phone"><div class="speaker"></div><div class="note">SIMULACIÓN EDUCATIVA - NO ES UN EQUIPO MÉDICO</div>', unsafe_allow_html=True)

e = st.session_state.estado

# --- PANTALLAS ---

if e == "APAGADO":
    screen("DESFIBRILADOR", "Pulse el botón para encender")
    if st.button("🔴", key="power"):
        st.session_state.inicio = datetime.now()
        log("Simulador encendido")
        ir("MENU")

elif e == "MENU":
    screen("DESFIBRILADOR", "Seleccione una opción", svg("corazon_informacion.svg"))
    if st.button("INFORMACIÓN Y APRENDIZAJE"): ir("INFORMACION")
    if st.button("OPERE", type="primary"): ir("OPERAR")

elif e == "INFORMACION":
    screen("INFORMACIÓN Y APRENDIZAJE", "Seleccione un contenido", svg("corazon_informacion.svg"))
    if st.button("ASISTENTE IA DE CONSULTA"): ir("CHAT_IA")
    if st.button("RESEÑA HISTÓRICA"): ir("HISTORIA")
    if st.button("USO SEGURO"): ir("USO")
    if st.button("CASOS Y EPICRISIS"): ir("EPICRISIS")
    if st.button("MINI EVALUACIÓN"): ir("EVALUACION")
    if st.button("VOLVER"): ir("MENU")

elif e == "CHAT_IA":
    screen("ASISTENTE IA", "Consulta técnica")
    preg = st.text_input("Escriba su pregunta clínica:")
    if preg:
        st.info(responder_ia(preg))
    if st.button("VOLVER A APRENDIZAJE"): ir("INFORMACION")

elif e == "HISTORIA":
    screen("RESEÑA HISTÓRICA", "Evolución de la desfibrilación", svg("corazon_informacion.svg"))
    st.markdown('''<div class="info"><b>Primeras investigaciones</b>Los estudios sobre electricidad y corazón prepararon el camino para comprender que una corriente controlada podía modificar determinados ritmos.</div>
    <div class="info"><b>Siglo XX</b>La desfibrilación pasó de equipos experimentales a dispositivos más compactos y seguros.</div>
    <div class="info"><b>DEA moderno</b>Los desfibriladores externos automáticos incorporaron análisis del ritmo y guías interactivas.</div>''', unsafe_allow_html=True)
    if st.button("VOLVER A APRENDIZAJE"): ir("INFORMACION")

elif e == "USO":
    screen("USO SEGURO", "Secuencia educativa", svg("usuario_con_parches.svg"))
    st.markdown('''<div class="info"><b>1. Encender</b>Active el DEA y siga sus instrucciones.</div>
    <div class="info"><b>2. Preparar y colocar</b>Descubra el tórax y coloque los parches según las ilustraciones.</div>
    <div class="info"><b>3. Analizar</b>Nadie debe tocar al usuario mientras se analiza el ritmo.</div>
    <div class="info"><b>4. Descargar o continuar</b>Descargue solo si el DEA lo indica.</div>''', unsafe_allow_html=True)
    if st.button("VOLVER A APRENDIZAJE"): ir("INFORMACION")

elif e == "EPICRISIS":
    screen("CASOS Y EPICRISIS", "Seleccione un caso simulado")
    caso_edu = st.selectbox("Caso clínico educativo", list(EPICRISIS.keys()))
    st.markdown(f'<div class="info"><b>{caso_edu}</b>{EPICRISIS[caso_edu]}</div>', unsafe_allow_html=True)
    if st.button("VOLVER A APRENDIZAJE"): ir("INFORMACION")

elif e == "EVALUACION":
    screen("MINI EVALUACIÓN", "Compruebe lo aprendido")
    q1 = st.radio("1. ¿Qué ritmos habilitan la descarga?", ["FV y TV sin pulso", "Asistolia y AESP", "Todos los ritmos"], index=None)
    q2 = st.radio("2. Durante el análisis se debe:", ["Evitar que alguien toque al usuario", "Aplicar descarga de inmediato", "Retirar parches"], index=None)
    q3 = st.radio("3. Una señal organizada sin pulso puede corresponder a:", ["AESP", "Ritmo sinusal normal", "FV"], index=None)
    if st.button("VER RESULTADO", type="primary"):
        score = sum([q1 == "FV y TV sin pulso", q2 == "Evitar que alguien toque al usuario", q3 == "AESP"])
        st.success(f"Resultado: {score}/3 respuestas correctas")
    if st.button("VOLVER A APRENDIZAJE"): ir("INFORMACION")

elif e == "OPERAR":
    screen("", "Preparar usuario simulado", svg("usuario_con_parches.svg"))
    if st.button("SIMULE PARAMETROS", type="primary"): ir("PARAMETROS")

elif e == "PARAMETROS":
    screen("SIMULE PARAMETROS", "Complete el formulario")
    with st.form("parametros"):
        modo = st.radio("Modo", ["Caso predeterminado", "Configuración manual"], horizontal=True)
        if modo == "Caso predeterminado":
            caso = st.selectbox("Caso", list(CASOS.keys()))
            data = CASOS[caso]
            st.markdown(f'<div class="ok"><b>{data["ritmo"]}</b><br>{data["conciencia"]}, Respiración {data["respiracion"].lower()}, Pulso {data["pulso"].lower()}<br>SpO2 {data["saturacion"]}, PA {data["presion"]}</div>', unsafe_allow_html=True)
            ritmo, conciencia, respiracion, pulso, saturacion, presion = data.values()
        else:
            ritmo = st.selectbox("Ritmo ECG", list(RITMOS.keys()))
            conciencia = st.selectbox("Estado de conciencia", ["Consciente", "Somnoliento", "Inconsciente"])
            respiracion = st.selectbox("Respiración", ["Normal", "Agónica", "Ausente"])
            pulso = st.selectbox("Pulso", ["Presente", "Ausente"])
            saturacion = st.selectbox("Saturación", SATURACIONES)
            presion = st.selectbox("Presión arterial", PRESIONES)
            caso = "Configuración manual"
        
        desenlace = st.selectbox("Resultado esperado si hay descarga", ["Selección aleatoria", "Recupera circulación (ROSC)", "Persiste el ritmo"])
        submit = st.form_submit_button("SIGUIENTE", type="primary")
        
        if submit:
            requiere_sin_pulso = ritmo in ["Fibrilación ventricular", "Taquicardia ventricular sin pulso", "Asistolia", "Actividad eléctrica sin pulso (AESP)"]
            if requiere_sin_pulso and pulso != "Ausente":
                st.error("Para este escenario de paro, el pulso debe figurar como ausente.")
            else:
                for k, v in dict(modo=modo, caso=caso, ritmo=ritmo, conciencia=conciencia, respiracion=respiracion, pulso=pulso, saturacion=saturacion, presion=presion, desenlace=desenlace).items():
                    st.session_state[k] = v
                ir("ANALIZANDO")

elif e == "ANALIZANDO":
    log(f"Caso: {st.session_state.caso}; ritmo: {st.session_state.ritmo}; SpO2: {st.session_state.saturacion}; PA: {st.session_state.presion}")
    info = RITMOS[st.session_state.ritmo]
    screen("ANALIZANDO", f"{st.session_state.ritmo}\nSpO2 {st.session_state.saturacion} PA {st.session_state.presion}", svg(info["svg"], "ecg-art"))
    with st.spinner("Analizando escenario ficticio..."):
        time.sleep(1.5)
    log("Análisis ficticio completado")
    if info["descarga"]:
        ir("RECOMENDACION")
    else:
        st.session_state.resultado = "No aplica: ritmo no desfibrilable"
        st.session_state.fin = datetime.now()
        
        guardar_en_bd({
            "fecha": st.session_state.fin.strftime("%Y-%m-%d %H:%M:%S"),
            "ritmo": st.session_state.ritmo,
            "resultado": st.session_state.resultado,
            "descargas": 0, "energia_J": 0
        })
        ir("NO_DESCARGA")

elif e == "RECOMENDACION":
    screen("DESCARGA RECOMENDADA", "200 J", svg(RITMOS[st.session_state.ritmo]["svg"], "ecg-art"))
    st.markdown('<div class="warning">Despeje el área. La acción siguiente es exclusivamente virtual y no produce energía.</div>', unsafe_allow_html=True)
    if st.button("PREPARAR DESCARGA", type="primary"): ir("DESCARGAR")

elif e == "NO_DESCARGA":
    screen("DESCARGA NO RECOMENDADA", st.session_state.ritmo, svg(RITMOS[st.session_state.ritmo]["svg"], "ecg-art"))
    st.markdown('<div class="warning">Continúe el protocolo indicado. El botón de descarga permanece deshabilitado.</div>', unsafe_allow_html=True)
    if st.button("RESUMEN DEL EVENTO", type="primary"): ir("RESUMEN")

elif e == "DESCARGAR":
    screen("DESCARGUE", "Oprima el corazón con el rayo")
    if st.button("⚡", key="shock"):
        st.session_state.descargas += 1
        st.session_state.energia += 200
        choice = st.session_state.desenlace
        success = random.choice([True, False]) if choice == "Selección aleatoria" else choice.startswith("Recupera")
        st.session_state.resultado = "Sí: circulación simulada restablecida (ROSC)" if success else "No: persiste el ritmo simulado"
        st.session_state.fin = datetime.now()
        log(f"Descarga virtual 200 J: {st.session_state.resultado}")
        
        guardar_en_bd({
            "fecha": st.session_state.fin.strftime("%Y-%m-%d %H:%M:%S"),
            "ritmo": st.session_state.ritmo,
            "resultado": st.session_state.resultado,
            "descargas": st.session_state.descargas,
            "energia_J": st.session_state.energia
        })
        ir("POST_DESCARGA")

elif e == "POST_DESCARGA":
    icon = "corazon_confirmacion.svg" if st.session_state.resultado.startswith("Sí") else "corazon_informacion.svg"
    screen("DESCARGA REALIZADA", st.session_state.resultado, svg(icon))
    if st.button("RESUMEN DEL EVENTO", type="primary"): ir("RESUMEN")

elif e == "RESUMEN":
    success = st.session_state.resultado.startswith("Sí")
    final_svg = "senal_ecg.svg" if success else RITMOS[st.session_state.ritmo]["svg"]
    screen("RESUMEN DEL EVENTO", "Señal posterior simulada", svg(final_svg, "ecg-art"))
    
    total = str(st.session_state.fin - st.session_state.inicio).split('.')[0] if st.session_state.fin and st.session_state.inicio else "0:00:00"
    
    rows = [
        ("Modo", st.session_state.modo), ("Caso", st.session_state.caso),
        ("Conciencia", st.session_state.conciencia), ("Respiración", st.session_state.respiracion),
        ("Pulso", st.session_state.pulso), ("Ritmo ECG", st.session_state.ritmo),
        ("Saturación", st.session_state.saturacion), ("Presión arterial", st.session_state.presion),
        ("Descargas", st.session_state.descargas), ("Energía", f"{st.session_state.energia} J virtuales"),
        ("Tiempo total", total),
        ("Fecha", st.session_state.fin.strftime("%d/%m/%Y") if st.session_state.fin else ""),
        ("Hora", st.session_state.fin.strftime("%H:%M:%S") if st.session_state.fin else ""),
        ("Resultado", st.session_state.resultado)
    ]
    st.markdown('<table class="event">' + ''.join(f'<tr><td>{a}</td><td>{b}</td></tr>' for a, b in rows) + '</table>', unsafe_allow_html=True)
    
    report = "SIMULADOR DEA RESUMEN\n" + '\n'.join(f"{a}: {b}" for a, b in rows) + "\n\nREGISTRO\n" + '\n'.join(st.session_state.registro)
    st.download_button("DESCARGAR RESUMEN (.TXT)", report, "resumen_evento.txt")
    
    if BD_PATH.exists():
        st.download_button("DESCARGAR BASE DE DATOS (.JSON)", BD_PATH.read_text(encoding="utf-8"), "historial_simulaciones.json", "application/json")
        
    if st.button("NUEVA SIMULACIÓN"):
        reset()
        st.rerun()

if e not in ("APAGADO", "RESUMEN"):
    if st.button("APAGAR / REINICIAR"):
        reset()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
