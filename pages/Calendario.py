import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date
import psycopg2
from functions import connect_to_supabase 
from fCalendario import render_classic_calendar, obtener_dias_con_turnos, obtener_turnos_mes, eliminar_turno, editar_turno, obtener_o_crear_paciente, obtener_o_crear_medico, guardar_turno

# archivo: calendario_turnos_app.py

# 📅 UI - Calendario
# ------------------------
st.set_page_config(layout="centered")
st.title("📅 Calendario de Turnos Médicos")

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
dias_con_turnos = obtener_dias_con_turnos(current_date.year, current_date.month)

# Render calendario visual
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdatescalendar(current_date.year, current_date.month)


render_classic_calendar()

# ------------------------
# ➕ Agendar Turno
# ------------------------
st.markdown("### ➕ Agendar Turno Médico")
with st.form("form_turno"):
    fecha = st.date_input("Fecha del turno", value=date.today())
    hora = st.time_input("Hora del turno", value=datetime.now().time())
    dni_paciente = st.text_input("DNI del paciente")
    nombre_medico = st.text_input("Nombre del médico")
    lugar = st.text_input("Lugar del turno")
    enviar = st.form_submit_button("Guardar Turno")

    if enviar:
        if dni_paciente.strip() and nombre_medico.strip() and lugar.strip():
            id_paciente = obtener_o_crear_paciente(dni_paciente.strip())
            id_medico = obtener_o_crear_medico(nombre_medico.strip())
            guardar_turno(id_paciente, id_medico, fecha, lugar)
            st.success("✅ Turno guardado correctamente")
        else:
            st.warning("Por favor completá todos los campos.")

# ------------------------
# 📋 Listado + Edición y Eliminación
# ------------------------
st.markdown("### 📋 Turnos del Mes")
df = obtener_turnos_mes(current_date.year, current_date.month)

if not df.empty:
    for i, row in df.iterrows():
        with st.expander(f"📅 {row['Fecha'].strftime('%d/%m/%Y')} - {row['Paciente']}"):
            st.text(f"Médico: {row['Médico']}")
            st.text(f"Lugar: {row['Lugar']}")
            nueva_fecha = st.date_input(f"Editar fecha (ID {row['ID']})", value=row["Fecha"], key=f"fecha_{i}")
            nuevo_lugar = st.text_input("Editar lugar", value=row["Lugar"], key=f"lugar_{i}")
            col_ed, col_el = st.columns([1, 1])
            with col_ed:
                if st.button("💾 Guardar cambios", key=f"editar_{i}"):
                    editar_turno(row["ID"], nueva_fecha, nuevo_lugar)
                    st.success("Turno actualizado.")
            with col_el:
                if st.button("🗑️ Eliminar turno", key=f"eliminar_{i}"):
                    eliminar_turno(row["ID"])
                    st.warning("Turno eliminado.")
else:
    st.info("No hay turnos agendados este mes.")

#Tenemos que agregar la opcion de que el paciente pueda cancelar el turno
#Tenemos que agregar un menu desplegable de los medicos que tiene, y si quiere agregar otro, ahi darle la opcion de escribirlo