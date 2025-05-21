import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date
import psycopg2
from functions import connect_to_supabase 

# ------------------------
# 🔍 Obtener días con turnos
# ------------------------
def obtener_dias_con_turnos(año, mes):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT DATE(fecha)
        FROM Turnos
        WHERE EXTRACT(MONTH FROM fecha) = %s AND EXTRACT(YEAR FROM fecha) = %s
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
        SELECT t.id_turno, t.fecha, p.nombre AS paciente, m.nombre AS medico, t.lugar
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
    cur.execute("UPDATE Turnos SET fecha = %s, lugar = %s WHERE id_turno = %s", (nueva_fecha, nuevo_lugar, id_turno))
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


def obtener_o_crear_medico(nombre, especialidad, lugar):
    conn = connect_to_supabase()
    cursor = conn.cursor()

    # Verificar si ya existe el médico con ese nombre, especialidad y lugar
    cursor.execute(
        "SELECT id_medico FROM Medicos WHERE nombre = %s AND especialidad = %s AND lugar = %s",
        (nombre, especialidad, lugar)
    )
    result = cursor.fetchone()

    if result:
        id_medico = result[0]
    else:
        # Insertar nuevo médico si no existe
        cursor.execute(
            "INSERT INTO Medicos (nombre, especialidad, lugar) VALUES (%s, %s, %s) RETURNING id_medico",
            (nombre, especialidad, lugar)
        )
        id_medico = cursor.fetchone()[0]
        conn.commit()

    cursor.close()
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
# 🔍 Obtener días con turnos
# ------------------------
def obtener_dias_con_turnos(año, mes):
    conn = connect_to_supabase()
    if conn is None:
        raise ConnectionError("No se pudo establecer la conexión a la base de datos.")

    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT DATE(fecha)
        FROM Turnos
        WHERE EXTRACT(MONTH FROM fecha) = %s AND EXTRACT(YEAR FROM fecha) = %s
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
        SELECT t.id_turno, t.fecha, p.nombre AS paciente, m.nombre AS medico, t.lugar
        FROM Turnos t
        JOIN Pacientes p ON t.id_paciente = p.id_paciente
        JOIN Medicos m ON t.id_medico = m.id_medico
        WHERE EXTRACT(MONTH FROM t.fecha) = %s AND EXTRACT(YEAR FROM t.fecha) = %s
        ORDER BY t.fecha
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
    cur.execute("UPDATE Turnos SET fecha = %s, lugar = %s WHERE id_turno = %s", (nueva_fecha, nuevo_lugar, id_turno))
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
    (fecha, hora, id_paciente, id_medico, lugar))

    conn.commit()
    cur.close()
    conn.close()

def obtener_todos_los_medicos():
    conn = connect_to_supabase()
    cursor = conn.cursor()

    cursor.execute("SELECT id_medico, nombre, especialidad, lugar FROM Medicos")
    medicos = cursor.fetchall()

    cursor.close()
    conn.close()

    # Retornar una lista de tuplas (id, "Nombre - Especialidad - Lugar")
    return [(m[0], f"{m[1]} - {m[2]} - {m[3]}") for m in medicos]
