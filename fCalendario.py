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