import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date
import psycopg2
from functions import connect_to_supabase 

# archivo: calendario_turnos_app.py

# ------------------------
# 🔍 Obtener días con turnos
# ------------------------
def obtener_dias_con_turnos(año, mes):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT DATE(fecha_turno)
        FROM Turnos
        WHERE EXTRACT(MONTH FROM fecha_turno) = %s AND EXTRACT(YEAR FROM fecha_turno) = %s
    """, (mes, año))
    dias = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return dias

# ------------------------
# 🔍 Obtener, editar y eliminar turnos
# ------------------------
def obtener_turnos_mes(año, mes):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id_turno, t.fecha_turno, p.nombre AS paciente, m.nombre AS medico, t.lugar
        FROM Turnos t
        JOIN Pacientes p ON t.id_paciente = p.id_paciente
        JOIN Medicos m ON t.id_medico = m.id_medico
        WHERE EXTRACT(MONTH FROM t.fecha_turno) = %s AND EXTRACT(YEAR FROM t.fecha_turno) = %s
        ORDER BY t.fecha_turno
    """, (mes, año))
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(datos, columns=["ID", "Fecha", "Paciente", "Médico", "Lugar"])

def eliminar_turno(id_turno):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("DELETE FROM Turnos WHERE id_turno = %s", (id_turno,))
    conn.commit()
    cur.close()
    conn.close()

def editar_turno(id_turno, nueva_fecha, nuevo_lugar):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("UPDATE Turnos SET fecha_turno = %s, lugar = %s WHERE id_turno = %s", (nueva_fecha, nuevo_lugar, id_turno))
    conn.commit()
    cur.close()
    conn.close()

# ------------------------
# 📋 Pacientes y médicos
# ------------------------
def obtener_o_crear_paciente(dni):
    conn = connect_to_supabase()
    cur = conn.cursor()

    # Buscar si el paciente ya existe
    cur.execute("SELECT id_paciente FROM Pacientes WHERE dni = %s", (dni,))
    paciente = cur.fetchone()

    if paciente:
        id_paciente = paciente[0]
    else:
        # Insertar nuevo paciente sin especificar id_paciente
        cur.execute("INSERT INTO Pacientes (dni) VALUES (%s) RETURNING id_paciente", (dni,))
        id_paciente = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()
    return id_paciente


def obtener_o_crear_medico(nombre):
    conn = connect_to_supabase()
    cur = conn.cursor()

    # Buscar si el médico ya existe
    cur.execute("SELECT id_medico FROM Medicos WHERE nombre = %s", (nombre,))
    medico = cur.fetchone()

    if medico:
        id_medico = medico[0]
    else:
        # Insertar nuevo médico sin especificar id_medico
        cur.execute("INSERT INTO Medicos (nombre) VALUES (%s) RETURNING id_medico", (nombre,))
        id_medico = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()
    return id_medico


def guardar_turno(id_paciente, id_medico, fecha, hora, lugar):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute(
    "INSERT INTO Turnos (fecha, hora, id_paciente, id_medico, lugar) VALUES (%s, %s, %s, %s, %s)",
    (fecha, hora, id_paciente, id_medico))

    conn.commit()
    cur.close()
    conn.close()

# ------------------------
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
