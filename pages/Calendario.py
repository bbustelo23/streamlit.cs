import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date, time

# Se asume que estas funciones existen y funcionan correctamente en fCalendario.py
from fCalendario import (
    obtener_todos_los_medicos, 
    obtener_lugares_por_medico, 
    obtener_dias_con_turnos, 
    obtener_turnos_mes, 
    eliminar_turno, 
    editar_turno, 
    obtener_o_crear_paciente, 
    obtener_o_crear_medico, 
    guardar_turno
)
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

# --- Configuración de la Página ---
st.set_page_config(
    page_title="MedCheck - Calendario",
    page_icon="📅",
    layout="wide"
)

# --- Estilos CSS Mejorados ---
st.markdown("""
    <style>
        /* --- Estilos Generales --- */
        .main-title { color: #800020; font-size: 2.5em; font-weight: bold; }
        .medcheck-text { color: #800020; }
        .stButton>button {
            background-color: #800020 !important;
            color: white !important;
            border: none;
            border-radius: 5px;
        }
        .stButton>button:hover { background-color: #600010 !important; }
        
        /* --- Estilos del Calendario --- */
        .calendar-container {
            font-family: 'Inter', sans-serif;
        }
        .calendar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 5px;
            text-align: center;
        }
        .day-name { font-weight: bold; color: #555; padding-bottom: 10px; }
        .day-cell {
            padding: 10px 5px;
            border-radius: 8px;
            position: relative;
            min-height: 60px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border: 1px solid transparent;
        }
        .day-other-month { color: #ccc; }
        .day-today .day-number {
            background-color: #800020;
            color: white;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            line-height: 30px;
            display: block;
        }
        .dot {
            height: 6px;
            width: 6px;
            background-color: #5cb85c;
            border-radius: 50%;
            display: inline-block;
            margin-top: 4px;
        }

        /* --- Estilos de Tarjetas de Turno --- */
        .card {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-left: 5px solid #800020;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .card-title {
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
        }
        .card-content {
            font-size: 0.95em;
            color: #555;
            margin: 8px 0;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Título Principal ---
st.markdown('<h1 class="main-title">📅 <span class="medcheck-text">MedCheck</span> - Calendario de Turnos</h1>', unsafe_allow_html=True)
st.divider()

# --- Verificación de Sesión y Encuesta ---
conn = connect_to_supabase()
dni = st.session_state.get("dni")
if not dni:
    st.warning("No hay un DNI cargado en sesión.")
    st.stop()
encuesta_completada = get_encuesta_completada(dni, conn=conn)
if not encuesta_completada.empty and not encuesta_completada.iloc[0]["encuesta_completada"]:
    st.warning("Antes de continuar, necesitas completar tu encuesta de salud.")
    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")
    st.stop()

# --- Inicialización de Fecha ---
if "current_date" not in st.session_state:
    st.session_state.current_date = datetime.today()

# --- Layout Principal en Dos Columnas ---
col_main, col_sidebar = st.columns([2, 1])

# --- Columna Principal (Izquierda) ---
with col_main:
    # --- Navegación del Calendario ---
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
    with nav_col1:
        if st.button("← Mes Anterior", use_container_width=True):
            st.session_state.current_date = (st.session_state.current_date.replace(day=1) - timedelta(days=1)).replace(day=1)
    with nav_col3:
        if st.button("Mes bunda →", use_container_width=True):
            st.session_state.current_date = (st.session_state.current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
    
    current_date = st.session_state.current_date
    with nav_col2:
        st.subheader(current_date.strftime("%B %Y").capitalize())

    # --- Renderizado del Calendario Mejorado ---
    st.markdown('<div class="calendar-container">', unsafe_allow_html=True)
    dias_con_turnos = obtener_dias_con_turnos(current_date.year, current_date.month, dni)
    cal = calendar.Calendar(firstweekday=6) # Domingo como primer día
    month_days = cal.monthdatescalendar(current_date.year, current_date.month)
    
    dias_semana_nombres = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
    header_html = "".join([f'<div class="day-name">{day}</div>' for day in dias_semana_nombres])
    st.markdown(f'<div class="calendar-grid">{header_html}</div>', unsafe_allow_html=True)

    calendar_html = '<div class="calendar-grid">'
    for week in month_days:
        for day in week:
            day_class = "day-cell"
            if day.month != current_date.month:
                day_class += " day-other-month"
            if day == date.today():
                day_class += " day-today"
            
            dot_html = '<span class="dot"></span>' if day in dias_con_turnos else ""
            calendar_html += f'<div class="{day_class}"><span class="day-number">{day.day}</span>{dot_html}</div>'
    calendar_html += '</div>'
    st.markdown(calendar_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # --- Listado de Turnos del Mes ---
    st.subheader("📋 Turnos Agendados para este Mes")
    df_turnos = obtener_turnos_mes(current_date.year, current_date.month, dni)

    if not df_turnos.empty:
        for i, row in df_turnos.iterrows():
            with st.container():
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">🩺 {row['Médico']}</div>
                        <div class="card-content">
                            <strong>Fecha:</strong> {row['Fecha'].strftime('%d/%m/%Y')} a las {row['Hora'].strftime('%H:%M')} hs<br>
                            <strong>Lugar:</strong> {row['Lugar']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("✏️ Editar o Eliminar Turno"):
                    with st.form(f"edit_form_{row['ID']}", border=False):
                        nueva_fecha = st.date_input("Nueva fecha", value=row["Fecha"], key=f"fecha_{i}")
                        nueva_hora = st.time_input("Nueva hora", value=row["Hora"], key=f"hora_{i}")
                        nuevo_lugar = st.text_input("Nuevo lugar", value=row["Lugar"], key=f"lugar_{i}")

                        edit_col, del_col = st.columns(2)
                        with edit_col:
                            if st.form_submit_button("✅ Guardar Cambios", use_container_width=True):
                                editar_turno(row["ID"], nueva_fecha, nueva_hora, nuevo_lugar)
                                st.success("Turno actualizado.")
                                st.rerun()
                        with del_col:
                            if st.form_submit_button("🗑️ Eliminar Turno", type="secondary", use_container_width=True):
                                eliminar_turno(row["ID"])
                                st.warning("Turno eliminado.")
                                st.rerun()
    else:
        st.info("No hay turnos agendados para este mes.")

# --- Columna Lateral (Derecha) ---
with col_sidebar:
    st.subheader("➕ Agendar Nuevo Turno")
    
    with st.form("form_turno", border=False):
        # Detalles del Médico
        st.write("**Detalles del Médico**")
        medicos_disponibles = obtener_todos_los_medicos()
        opciones_medicos = ["Seleccionar médico existente"] + [f"{m[1]}" for m in medicos_disponibles]
        opcion_elegida = st.selectbox("Médico", opciones_medicos, key="selector_medico", label_visibility="collapsed")
        
        with st.expander("➕ Ingresar un médico nuevo"):
            nombre_medico_nuevo = st.text_input("Nombre del nuevo médico")
            especialidad_medico_nuevo = st.text_input("Especialidad del nuevo médico")

        # Fecha y Lugar
        st.write("**Fecha y Lugar del Turno**")
        fecha = st.date_input("Fecha", value=date.today())
        hora = st.time_input("Hora", value=time(9, 0))
        
        id_medico_seleccionado = None
        if opcion_elegida != "Seleccionar médico existente":
            for m in medicos_disponibles:
                if f"{m[1]}" == opcion_elegida:
                    id_medico_seleccionado = m[0]
                    break
            if id_medico_seleccionado:
                lugares = obtener_lugares_por_medico(id_medico_seleccionado)
                lugar_seleccionado = st.selectbox("Lugar", lugares)
            else:
                lugar_seleccionado = st.text_input("Lugar")
        else:
            lugar_seleccionado = st.text_input("Lugar")

        if st.form_submit_button("💾 Guardar Turno", type="primary", use_container_width=True):
            id_paciente = obtener_o_crear_paciente(dni)
            
            # Lógica para guardar
            if nombre_medico_nuevo and especialidad_medico_nuevo:
                id_medico = obtener_o_crear_medico(nombre_medico_nuevo, especialidad_medico_nuevo)
                guardar_turno(id_paciente, id_medico, fecha, hora, lugar_seleccionado)
                st.success("Turno guardado con nuevo médico.")
                st.rerun()
            elif id_medico_seleccionado:
                guardar_turno(id_paciente, id_medico_seleccionado, fecha, hora, lugar_seleccionado)
                st.success("Turno guardado.")
                st.rerun()
            else:
                st.warning("Por favor, selecciona un médico existente o ingresa los datos de uno nuevo.")
