import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date
import psycopg2
from fCalendario import obtener_todos_los_medicos, obtener_lugares_por_medico, obtener_dias_con_turnos, obtener_turnos_mes, eliminar_turno, editar_turno, obtener_o_crear_paciente, obtener_o_crear_medico, guardar_turno
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

conn = connect_to_supabase()

# archivo: calendario_turnos_app.py

# 🗕️ UI - Calendario
# ------------------------

st.set_page_config(
    page_title="MedCheck - Calendario",
    page_icon="⚕️",
    layout="wide"
)

# Custom CSS styling
st.markdown("""
    <style>
    .main-title {
        color: #800020;  /* Burgundy color */
        font-size: 3em;
        font-weight: bold;
        margin-bottom: 1em;
    }
    .subtitle {
        color: #2E4053;  /* Dark blue-gray */
        font-size: 1.5em;
        margin-bottom: 1em;
    }
    .stButton>button {
        background-color: #800020 !important;
        color: white !important;
    }
    .stButton>button:hover {
        background-color: #600010 !important;
        color: white !important;
    }
    .medcheck-text {
        color: #800020;  /* Burgundy color */
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">📅 <span class="medcheck-text">MedCheck</span> - Calendario</h1>', unsafe_allow_html=True)
dni = st.session_state.get("dni")

if not dni:
    st.warning("No hay un DNI cargado en sesión.")
    st.stop()

encuesta_completada = get_encuesta_completada(dni, conn=conn)

if not encuesta_completada.empty and not encuesta_completada.iloc[0]["encuesta_realizada"]:
    st.warning("Antes de continuar, necesitamos que completes una breve encuesta sobre tu salud y hábitos.")
    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")   # Ajustá el path según la estructura de tu app

    st.stop()

if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today().replace(day=1)

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("← Mes anterior"):
        st.session_state.current_date -= timedelta(days=1)
        st.session_state.current_date = st.session_state.current_date.replace(day=1)
with col3:
    if st.button("Mes siguiente →"):
        year = st.session_state.current_date.year
        month = st.session_state.current_date.month + 1
        if month > 12:
            month = 1
            year += 1
        st.session_state.current_date = datetime(year, month, 1)

current_date = st.session_state.current_date
st.subheader(current_date.strftime("%B %Y").upper())

# Colorear días con turnos
dias_con_turnos = obtener_dias_con_turnos(current_date.year, current_date.month, dni)

# Render calendario visual
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdatescalendar(current_date.year, current_date.month)

def render_classic_calendar():
    dias = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    st.markdown("<style>table, th, td {border:1px solid #000; text-align: center; font-size: 18px;} th {background-color: #f0f0f0;}</style>", unsafe_allow_html=True)
    tabla = "<table style='width:100%; table-layout: fixed;'>"
    tabla += "<tr>" + "".join([f"<th>{dia}</th>" for dia in dias]) + "</tr>"
    for semana in month_days:
        tabla += "<tr>"
        for dia in semana:
            color = "#eee" if dia.month != current_date.month else "#fff"
            if dia in dias_con_turnos:
                color = "#b3e6b3"
            hoy = date.today()
            estilo = f"background-color:{color}; padding:15px;"
            if dia == hoy:
                estilo += "border: 2px solid #000; font-weight: bold;"
            tabla += f"<td style='{estilo}'>{dia.day}</td>"
        tabla += "</tr>"
    tabla += "</table>"
    st.markdown(tabla, unsafe_allow_html=True)

render_classic_calendar()

# ------------------------
# ➕ Agendar Turno

if "agregando_nuevo_medico" not in st.session_state:
    st.session_state.agregando_nuevo_medico = False

# ------------------------
st.markdown("### ➕ Agendar Turno Médico")

medicos_disponibles = obtener_todos_los_medicos()
opciones_medicos = [f"{m[1]}" for m in medicos_disponibles] + ["➕ Ingresar un médico nuevo"]
opcion_elegida = st.selectbox("Médico", opciones_medicos, key="selector_medico")

if opcion_elegida == "➕ Ingresar un médico nuevo":
    st.session_state.agregando_nuevo_medico = True
else:
    st.session_state.agregando_nuevo_medico = False

with st.form("form_turno"):
    fecha = st.date_input("Fecha del turno", value=date.today())
    hora = st.time_input("Hora del turno", value=datetime.now().time())
    dni_paciente = st.text_input("DNI del paciente", value=dni)
    
    if st.session_state.agregando_nuevo_medico:
        col_m1, col_m2, col_m3= st.columns(3)
        with col_m1:
            nombre_medico = st.text_input("Nombre del médico")
        with col_m2:
            especialidad_medico = st.text_input("Especialidad del médico")
        with col_m3:
            lugar_seleccionado = st.text_input("Lugar del turno")
        usar_medico_existente = False  
    else:
        usar_medico_existente = True
        # Buscar el ID del médico seleccionado
        id_medico = None
        for m in medicos_disponibles:
            if f"{m[1]}" == opcion_elegida:
                id_medico = m[0]
                break
        
        if id_medico:
            lugares = obtener_lugares_por_medico(id_medico)
            lugar_seleccionado = st.selectbox("Seleccionar lugar del turno", lugares)
        else:
            lugar_seleccionado = st.text_input("Lugar del turno")

    enviar = st.form_submit_button("Guardar Turno")

    if enviar:
        try:
            if dni_paciente.strip() and lugar_seleccionado.strip():
                id_paciente = obtener_o_crear_paciente(dni_paciente.strip())

                if usar_medico_existente and id_medico:
                    guardar_turno(id_paciente, id_medico, fecha, hora, lugar_seleccionado)
                    st.success("✅ Turno guardado correctamente")
                    st.rerun()  # Recargar la página para mostrar los cambios
                elif not usar_medico_existente:
                    if nombre_medico.strip() and especialidad_medico.strip():
                        id_medico_nuevo = obtener_o_crear_medico(nombre_medico.strip(), especialidad_medico.strip(), lugar_seleccionado.strip())
                        guardar_turno(id_paciente, id_medico_nuevo, fecha, hora, lugar_seleccionado)
                        st.success("✅ Turno guardado correctamente con nuevo médico")
                        st.rerun()  # Recargar la página para mostrar los cambios
                    else:
                        st.warning("Por favor completá nombre y especialidad del nuevo médico.")
                else:
                    st.error("Error: No se pudo obtener el ID del médico seleccionado.")
            else:
                st.warning("Por favor completá DNI del paciente y lugar del turno.")
        except Exception as e:
            st.error(f"Error al guardar el turno: {str(e)}")

# ------------------------
# 📋 Listado + Edición y Eliminación
# ------------------------
st.markdown("### 📋 Turnos del Mes")
df = obtener_turnos_mes(current_date.year, current_date.month, dni)

if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"🗕️ {row['Fecha'].strftime('%d/%m/%Y')} - {row['Paciente']}"):
            st.text(f"Médico: {row['Médico']}")
            st.text(f"Lugar: {row['Lugar']}")
            nueva_fecha = st.date_input(f"Editar fecha (ID {row['ID']})", value=row["Fecha"], key=f"fecha_{i}")
            nuevo_lugar = st.text_input("Editar lugar", value=row["Lugar"], key=f"lugar_{i}")
            col_ed, col_el = st.columns([1, 1])
            with col_ed:
                if st.button("✅ Guardar cambios", key=f"editar_{i}"):
                    try:
                        editar_turno(row["ID"], nueva_fecha, nuevo_lugar)
                        st.success("Turno actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar turno: {str(e)}")
            with col_el:
                if st.button("🗑️ Eliminar turno", key=f"eliminar_{i}"):
                    try:
                        eliminar_turno(row["ID"])
                        st.warning("Turno eliminado.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al eliminar turno: {str(e)}")
else:
    st.info("No hay turnos agendados este mes.")

#------------------------------------------------------------------------
