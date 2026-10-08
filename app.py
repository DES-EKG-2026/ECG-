"""
SIMULADOR DEA MÓVIL - PROYECTO UNIVERSITARIO
Ajustado fielmente al Wireframe oficial sin eliminar funcionalidades previas.
"""
from datetime import datetime
from pathlib import Path
import base64
import json
import random
import time
import streamlit as st

# Compatibilidad con estructura de archivos
ASSETS = Path(__file__).parent / "assets" if (Path(__file__).parent / "assets").exists() else Path(__file__).parent
BD_PATH = Path(__file__).parent / "historial_simulaciones.json"

# Mapeo de ritmos ECG y archivos SVG
RITMOS = {
    "Fibrilación ventricular": {"svg": "ecg_fibrilacion_ventricular.svg", "descarga": True},
    "Taquicardia ventricular sin pulso": {"svg": "ecg_taquicardia_ventricular.svg", "descarga": True},
    "Asistolia": {"svg": "ecg_asistolia.svg", "descarga": False},
    "Actividad eléctrica sin pulso (AESP)": {"svg": "ecg_aesp.svg", "descarga": False},
    "Ritmo sinusal": {"svg": "senal_ecg.svg", "descarga": False},
    "Bradicardia sinusal": {"svg": "ecg_bradicardia.svg", "descarga": False},
    "Taquicardia sinusal con pulso": {"svg": "ecg_taquicardia_sinusal.svg", "descarga": False},
    "Extrasístoles": {"svg": "ecg_etrasistole.svg", "descarga": False},
}

# Casos clínicos
CASOS = {
    "Fibrilación ventricular": dict(ritmo="Fibrilación ventricular", conciencia="Inconsciente", respiracion="Agónica", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "TV sin pulso": dict(ritmo="Taquicardia ventricular sin pulso", conciencia="Inconsciente", respiracion="Ausente", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "Asistolia": dict(ritmo="Asistolia", conciencia="Inconsciente", respiracion="Ausente", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "AESP": dict(ritmo="Actividad eléctrica sin pulso (AESP)", conciencia="Inconsciente", respiracion="Agónica", pulso="Ausente", saturacion="No detectable", presion="No detectable"),
    "Recuperación posterior": dict(ritmo="Ritmo sinusal", conciencia="Somnoliento", respiracion="Normal", pulso="Presente", saturacion="96%", presion="110/70 mmHg"),
}

# Epicrisis docentes
EPICRISIS = {
    "FV con recuperación": "Usuario simulado inconsciente, con respiración agónica y sin pulso. El DEA identifica fibrilación ventricular, recomienda 200 J virtuales y, tras la descarga, el caso evoluciona a ritmo sinusal con circulación simulada restablecida.",
    "FV persistente": "Usuario simulado inconsciente y sin pulso. Tras una primera descarga virtual de 200 J persiste la fibrilación ventricular. El ejercicio indica continuar el protocolo docente y reevaluar el ritmo.",
    "TV sin pulso": "Usuario simulado inconsciente, sin pulso y con complejos rápidos y anchos. Se aplica una descarga virtual y se registra recuperación o persistencia según el desenlace configurado.",
    "Asistolia": "Usuario simulado inconsciente, sin respiración normal y sin pulso. El ECG muestra una línea casi plana; la aplicación bloquea la descarga y orienta continuar el protocolo del curso.",
    "AESP": "El monitor muestra actividad eléctrica organizada, pero el usuario simulado no tiene pulso ni presión detectable. Se clasifica como actividad eléctrica sin pulso y no se habilita la descarga.",
}

SATURACIONES = ["No detectable", "70%", "75%", "80%", "85%", "90%", "94%", "96%", "98%"]
PRESIONES = ["No detectable", "70/40 mmHg", "80/50 mmHg", "90/60 mmHg", "100/60 mmHg", "110/70 mmHg", "120/80 mmHg", "140/90 mmHg"]

# --- BASE DE DATOS Y IA ---

def guardar_en_bd(registro_datos):
    datos = []
    if BD_PATH.exists():
        try:
            datos = json.loads(BD_PATH.read_text(encoding="utf-8"))
        except Exception:
            datos = []
    datos.append(registro_datos)
    BD_PATH.write_text(json.dumps(datos, indent=4, ensure_ascii=False), encoding="utf-8")

def responder_ia(pregunta):
    p = pregunta.lower()
    if any(k in p for k in ["desfibrilable", "descarga", "choque"]):
        return "🤖 **Asistente IA:** Los ritmos desfibrilables son la **Fibrilación Ventricular (FV)** y la **Taquicardia Ventricular sin pulso (TVsp)**. La Asistolia y la AESP NO reciben descarga."
    elif any(k in p for k in ["parche", "electrodo", "donde", "colocar"]):
        return "🤖 **Asistente IA:** Coloque un parche debajo de la clavícula derecha y el otro en la línea axilar media izquierda del tórax."
    elif any(k in p for k in ["rcp", "reanimacion", "compresion"]):
        return "🤖 **Asistente IA:** Inicie RCP (30 compresiones por 2 ventilaciones) a una frecuencia de 100-120 cpm si la descarga no es recomendada o tras administrarla."
    elif any(k in p for k in ["asistolia", "aesp"]):
        return "🤖 **Asistente IA:** Son ritmos de paro no desfibrilables. Mantenga la RCP continua y revalúe el ritmo cada 2 minutos."
    else:
        return "🤖 **Asistente IA:** Hola. Puedo responder dudas sobre ritmos desfibrilables, posición de parches, RCP y protocolos de DEA."

# --- MÁQUINA DE ESTADOS Y AUXILIARES ---

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

def screen(title="", subtitle="", art_top="", art_bottom=""):
    st.markdown(f'''
    <div class="screen">
        <div class="brand">DESFIBRILAD<span>⚡</span>R</div>
        {f'<div class="art-top">{art_top}</div>' if art_top else ''}
        {f'<h1>{title}</h1>' if title else ''}
        {f'<h2>{subtitle}</h2>' if subtitle else ''}
        {f'<div class="art-bottom">{art_bottom}</div>' if art_bottom else ''}
    </div>
    ''', unsafe_allow_html=True)

def ir(estado):
    st.session_state.estado = estado
    st.rerun()

st.set_page_config(page_title="Simulador DEA", page_icon="⚡", layout="centered")
init()

# CSS - Estilos para replicar el Wireframe con marcos negros y esquinas cuadradas/redondeadas según diseño
st.markdown('''<style>
[data-testid="stHeader"], [data-testid="stToolbar"] {display:none}
.stApp{background:#f5f5f5;color:#000}
.block-container{max-width: 420px; padding: 10px}
.phone{background:#fff; border:3px solid #000; border-radius: 24px; padding: 16px; min-height: 680px; box-shadow:0 10px 25px rgba(0,0,0,0.1)}
.speaker{width: 80px; height: 4px; border-radius: 4px; background: #000; margin: 0 auto 12px}

.screen{
    position:relative; 
    min-height: 380px; 
    border:2px solid #000; 
    border-radius: 16px; 
    display: flex; 
    flex-direction:column; 
    align-items:center; 
    justify-content: center; 
    text-align:center;
    padding: 16px 12px; 
    margin-bottom: 12px;
    background: #fff;
}
.brand{position:absolute; top: 12px; font:900 22px Arial, sans-serif; color:#000; letter-spacing:1px}
.brand span{color:#000; font-size:24px}
.screen h1{font:900 22px Arial, sans-serif; margin:8px 0; text-transform:uppercase; color:#000; letter-spacing: 0.5px}
.screen h2{font:700 16px Arial, sans-serif; margin:4px 0; color:#000}

/* ESTILO DE BOTONES TIPO WIREFRAME (MARCO NEGRO Y TEXTO NEGRO) */
.stButton>button, .stDownloadButton>button {
    width: 100% !important;
    min-height: 48px !important;
    border: 2px solid #000000 !important;
    border-radius: 2px !important;
    background-color: #ffffff !important;
    color: #000000 !important;
    font: 800 16px Arial, sans-serif !important;
    text-transform: UPPERCASE !important;
    margin-bottom: 6px !important;
}
.stButton>button p, .stDownloadButton>button p { color: #000000 !important; font-weight: 900 !important; }

/* BOTÓN DE POWER Y CHOQUE CIRCULARES */
.st-key-power button {
    width: 110px !important; height: 110px !important; min-height: 110px !important;
    border-radius: 50% !important; border: 3px solid #000 !important; margin: 30px auto !important; font-size: 0px !important;
}
.st-key-shock button {
    width: 120px !important; height: 120px !important; min-height: 120px !important;
    border-radius: 50% !important; border: 3px solid #000 !important; margin: 10px auto !important; font-size: 0px !important;
}

/* ARTES E IMÁGENES SVG */
.art-top svg, .art-bottom svg, .art svg { width: 140px; height: 140px; margin: 5px 0; }
.ecg-art svg { width: 100%; height: 110px; margin: 5px 0; }

/* TABLA DE RESUMEN TIPO WIREFRAME */
.wireframe-table { width: 100%; border-collapse: collapse; margin-top: 5px; }
.wireframe-table td { border: 1.5px solid #000; padding: 6px 8px; font: bold 11px Arial, sans-serif; color: #000; text-transform: uppercase; text-align: left; }
.wireframe-table td:first-child { width: 50%; background: #fafafa; }

/* CONTENEDORES E INFORMACIÓN */
.info-box { border: 1.5px solid #000; padding: 8px; border-radius: 4px; margin-bottom: 6px; font: 12px Arial, sans-serif; text-align: left; }
.info-box b { text-transform: uppercase; display: block; }

@media (max-width: 480px) {
    .block-container{padding:0}
    .phone{border:0; border-radius:0; box-shadow: none; min-height:100vh}
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
    background-size: 75px 75px !important;
}}
.st-key-shock button {{
    background-color: #fff !important;
    background-image: url("{img_descarga}") !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-size: 85px 85px !important;
}}
</style>''', unsafe_allow_html=True)

st.markdown('<div class="phone"><div class="speaker"></div>', unsafe_allow_html=True)

e = st.session_state.estado

# --- PANTALLAS SEGÚN ESTRUCTURA DEL WIREFRAME ---

if e == "APAGADO":
    screen("DESFIBRILADOR")
    if st.button("🔴", key="power"):
        st.session_state.inicio = datetime.now()
        log("Simulador encendido")
        ir("MENU")

elif e == "MENU":
    screen("DESFIBRILADOR")
    if st.button("INFORMACION"): ir("INFORMACION")
    if st.button("OPERE"): ir("OPERAR")

elif e == "INFORMACION":
    screen("", "", art_top=svg("corazon_informacion.svg"))
    if st.button("RESENA HISTORICA"): ir("HISTORIA")
    if st.button("USOS"): ir("USO")
    if st.button("EPICRISIS MEDICA"): ir("EPICRISIS")
    if st.button("ASISTENTE IA"): ir("CHAT_IA")
    if st.button("MINI EVALUACIÓN"): ir("EVALUACION")
    if st.button("VOLVER"): ir("MENU")

elif e == "OPERAR":
    screen("SIMULE PARAMETROS", art_bottom=svg("usuario_con_parches.svg"))
    if st.button("CONFIGURAR PARAMETROS"): ir("PARAMETROS")

elif e == "PARAMETROS":
    screen("SIMULE PARAMETROS", art_bottom=svg("usuario_con_parches.svg"))
    with st.form("parametros"):
        modo = st.radio("Modo", ["Caso predeterminado", "Configuración manual"], horizontal=True)
        if modo == "Caso predeterminado":
            caso = st.selectbox("Seleccione Caso", list(CASOS.keys()))
            data = CASOS[caso]
            ritmo, conciencia, respiracion, pulso, saturacion, presion = data.values()
        else:
            ritmo = st.selectbox("Ritmo ECG", list(RITMOS.keys()))
            conciencia = st.selectbox("Estado de conciencia", ["Consciente", "Somnoliento", "Inconsciente"])
            respiracion = st.selectbox("Respiración", ["Normal", "Agónica", "Ausente"])
            pulso = st.selectbox("Pulso", ["Presente", "Ausente"])
            saturacion = st.selectbox("SATURACION", SATURACIONES)
            presion = st.selectbox("PRESION ARTERIAL", PRESIONES)
            caso = "Configuración manual"
        
        desenlace = st.selectbox("Desenlace si hay descarga", ["Selección aleatoria", "Recupera circulación (ROSC)", "Persiste el ritmo"])
        submit = st.form_submit_button("SIGUIENTE")
        
        if submit:
            requiere_sin_pulso = ritmo in ["Fibrilación ventricular", "Taquicardia ventricular sin pulso", "Asistolia", "Actividad eléctrica sin pulso (AESP)"]
            if requiere_sin_pulso and pulso != "Ausente":
                st.error("Para este escenario el pulso debe figurar como ausente.")
            else:
                for k, v in dict(modo=modo, caso=caso, ritmo=ritmo, conciencia=conciencia, respiracion=respiracion, pulso=pulso, saturacion=saturacion, presion=presion, desenlace=desenlace).items():
                    st.session_state[k] = v
                ir("ANALIZANDO")

elif e == "ANALIZANDO":
    log(f"Caso: {st.session_state.caso}; ritmo: {st.session_state.ritmo}")
    info = RITMOS[st.session_state.ritmo]
    screen("ANALIZANDO", art_bottom=svg("usuario_con_parches.svg"))
    with st.spinner("Analizando ritmo..."):
        time.sleep(1.5)
    log("Análisis completado")
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
    screen("DESCARGA RECOMEDADA", "200J", art_bottom=svg("usuario_con_parches.svg"))
    if st.button("CONTINUAR"): ir("DESCARGAR")

elif e == "NO_DESCARGA":
    screen("DESCARGA NO RECOMENDADA", st.session_state.ritmo, art_bottom=svg(RITMOS[st.session_state.ritmo]["svg"], "ecg-art"))
    if st.button("RESUMEN DEL EVENTO"): ir("RESUMEN")

elif e == "DESCARGAR":
    screen("DESCARGA RECOMEDADA\n200J", "DESCARGUE")
    if st.button("⚡", key="shock"):
        st.session_state.descargas += 1
        st.session_state.energia += 200
        choice = st.session_state.desenlace
        success = random.choice([True, False]) if choice == "Selección aleatoria" else choice.startswith("Recupera")
        st.session_state.resultado = "Sí: circulación restablecida (ROSC)" if success else "No: persiste el ritmo"
        st.session_state.fin = datetime.now()
        log(f"Descarga 200 J: {st.session_state.resultado}")
        
        guardar_en_bd({
            "fecha": st.session_state.fin.strftime("%Y-%m-%d %H:%M:%S"),
            "ritmo": st.session_state.ritmo,
            "resultado": st.session_state.resultado,
            "descargas": st.session_state.descargas,
            "energia_J": st.session_state.energia
        })
        ir("POST_DESCARGA")

elif e == "POST_DESCARGA":
    screen("", art_top=svg("corazon_confirmacion.svg"))
    if st.button("RESUMEN DEL EVENTO"): ir("RESUMEN")

elif e == "RESUMEN":
    success = st.session_state.resultado.startswith("Sí")
    final_svg = "senal_ecg.svg" if success else RITMOS[st.session_state.ritmo]["svg"]
    
    screen("", art_top=svg(final_svg, "ecg-art"))
    
    total_time = str(st.session_state.fin - st.session_state.inicio).split('.')[0] if st.session_state.fin and st.session_state.inicio else "0:00:00"
    fecha_str = st.session_state.fin.strftime("%d/%m/%Y") if st.session_state.fin else ""
    hora_str = st.session_state.fin.strftime("%H:%M:%S") if st.session_state.fin else ""

    tabla_html = f'''
    <table class="wireframe-table">
        <tr><td>SATURACION</td><td>{st.session_state.saturacion}</td></tr>
        <tr><td>PRESION ARTERIAL</td><td>{st.session_state.presion}</td></tr>
        <tr><td>DESCARGAS REALIZADAS</td><td>{st.session_state.descargas}</td></tr>
        <tr><td>ENERGIA ENTREGADA</td><td>{st.session_state.energia} J</td></tr>
        <tr><td>TIEMPO TOTAL</td><td>{total_time}</td></tr>
        <tr><td>FECHA</td><td>{fecha_str}</td></tr>
        <tr><td>HORA</td><td>{hora_str}</td></tr>
    </table>
    '''
    st.markdown(tabla_html, unsafe_allow_html=True)
    
    report = "SIMULADOR DEA - RESUMEN\n" + f"Saturacion: {st.session_state.saturacion}\nPresion: {st.session_state.presion}\nDescargas: {st.session_state.descargas}\nEnergia: {st.session_state.energia} J\nTiempo: {total_time}\nFecha: {fecha_str}\nHora: {hora_str}\nResultado: {st.session_state.resultado}"
    
    st.download_button("DESCARGAR REPORTES (.TXT)", report, "resumen_wireframe.txt")
    if st.button("INICIO / NUEVA SIMULACIÓN"):
        reset()
        st.rerun()

# CONTENIDOS SECUNDARIOS DE INFORMACIÓN
elif e == "CHAT_IA":
    screen("ASISTENTE IA")
    preg = st.text_input("Pregunta clínica:")
    if preg:
        st.info(responder_ia(preg))
    if st.button("VOLVER A INFORMACION"): ir("INFORMACION")

elif e == "HISTORIA":
    screen("RESENA HISTORICA")
    st.markdown('<div class="info-box"><b>Inicios</b>Estudios sobre desfibrilación en el siglo XX.</div><div class="info-box"><b>Evolución</b>Uso de corrientes controladas y creación de los primeros equipos portátiles.</div>', unsafe_allow_html=True)
    if st.button("VOLVER A INFORMACION"): ir("INFORMACION")

elif e == "USO":
    screen("USOS")
    st.markdown('<div class="info-box"><b>Pasos principales</b>1. Encender el equipo.<br>2. Colocar electrodos.<br>3. Analizar ritmo.<br>4. Aplicar descarga si se indica.</div>', unsafe_allow_html=True)
    if st.button("VOLVER A INFORMACION"): ir("INFORMACION")

elif e == "EPICRISIS":
    screen("EPICRISIS MEDICA")
    caso_edu = st.selectbox("Caso Clínico", list(EPICRISIS.keys()))
    st.markdown(f'<div class="info-box"><b>{caso_edu}</b>{EPICRISIS[caso_edu]}</div>', unsafe_allow_html=True)
    if st.button("VOLVER A INFORMACION"): ir("INFORMACION")

elif e == "EVALUACION":
    screen("MINI EVALUACIÓN")
    q1 = st.radio("1. Ritmos desfibrilables:", ["FV y TV sin pulso", "Asistolia y AESP"])
    if st.button("EVALUAR"):
        if q1 == "FV y TV sin pulso":
            st.success("Correcto")
        else:
            st.error("Incorrecto")
    if st.button("VOLVER A INFORMACION"): ir("INFORMACION")

if e not in ("APAGADO", "RESUMEN"):
    if st.button("REINICIAR / APAGAR"):
        reset()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
