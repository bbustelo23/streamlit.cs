
import pandas as pd
import streamlit as st
from functions import execute_query
from functions import connect_to_supabase
import sqlite3
from datetime import datetime


def get_paciente(dni):
    query = "SELECT * FROM pacientes WHERE dni = %s"
    return execute_query(query, (dni,), is_select=True)

def insert_paciente(dni, nombre, fecha_nacimiento, sexo, password, encuesta_completada=False):
    query = """
    INSERT INTO pacientes (dni, nombre, fecha_nacimiento, sexo, password, encuesta_completada)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    params = (dni, nombre, fecha_nacimiento, sexo, password, encuesta_completada)
    return execute_query(query, params=params, conn=conn, is_select=False)


def insert_historial(dni, fecha_completado, fumador, alcoholico, peso,
                     condicion=None, medicacion_cronica=None, dieta=False,
                     antecedentes_familiares_enfermedad=None, antecedentes_familiares_familiar=None,
                     conn=None):
    query = """
    INSERT INTO historial (
        dni, fecha_completado, fumador, alcoholico, peso, condicion,
        medicacion_cronica, dieta, estres_alto, colesterol_alto, antecedentes_familiares_enfermedad,
        antecedentes_familiares_familiar
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    params = (
        dni, fecha_completado, fumador, alcoholico, peso,
        condicion, medicacion_cronica, dieta,
        antecedentes_familiares_enfermedad, antecedentes_familiares_familiar)
    return execute_query(query, params=params, conn=conn, is_select=False)


def get_id_paciente_por_dni(dni, conn=None):
    query = "SELECT id_paciente FROM pacientes WHERE dni = %s;"
    #st.write("Ejecutando consulta con dni:", dni)
    
    result = execute_query(query, params=(dni,), conn=conn, is_select=True)
    #st.write("Resultado de la consulta:", result)
    
    if result is not None and not result.empty:
        return result.iloc[0]['id_paciente']
    else:
        st.warning(f"No se encontró un paciente con el DNI {dni}")
        return None


def insert_historial(
    dni,
    fecha_completado=None,
    peso=None,
    fumador=False,
    alcoholico=False,
    dieta=None,
    estres_alto=None,
    colesterol_alto=None,
    actividad_fisica=None,
    alergias=None,
    suplementos=None,
    condicion=None,
    medicacion_cronica=None,
    antecedentes_familiares_enfermedad=None,
    antecedentes_familiares_familiar=None,
    conn=None
):
    if fecha_completado is None:
        fecha_completado = date.today()

    id_paciente = int(get_id_paciente_por_dni(dni, conn=conn))
    if id_paciente is None:
        raise ValueError(f"No se encontró paciente con DNI {dni}")

    condicion_db = condicion if condicion else "no tiene"
    medicacion_db = medicacion_cronica if condicion else None

    query = """
    INSERT INTO historial_medico
        (id_paciente, fecha_completado, peso, fumador, alcoholico, dieta, actividad_fisica, estres_alto, colesterol_alto,
         condicion, medicacion_cronica, antecedentes_familiares_enfermedad, antecedentes_familiares_familiar)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    params = (
        id_paciente,
        fecha_completado,
        peso,
        fumador,
        alcoholico,
        dieta,
        estres_alto,
        colesterol_alto,
        actividad_fisica,
        condicion_db,
        medicacion_db,
        antecedentes_familiares_enfermedad,
        antecedentes_familiares_familiar
    )

    return execute_query(query, params=params, conn=conn, is_select=False)



def update_encuesta_completada(dni, conn=None):
    """
    Marca como completada la encuesta para el paciente con el DNI dado.
    """
    query = """
    UPDATE pacientes
    SET encuesta_realizada = TRUE
    WHERE dni = %s;
    """
    params = (dni,)
    return execute_query(query, params=params, conn=conn, is_select=False)

def get_encuesta_completada(dni, conn=None):
    query = """
    SELECT encuesta_realizada FROM pacientes WHERE dni = %s;
    """
    params = (dni,)
    return execute_query(query, params=params, conn=conn, is_select=True)

# fEncuesta.py - Funciones para manejo de responsables, pacientes e historial médico


# ========== CONEXIÓN ==========
def get_connection():
    return sqlite3.connect('medcheck.db')

# ========== FUNCIONES DE RESPONSABLES ==========

def get_responsable_by_id(id_responsable):
    conn = get_connection()
    try:
        query = "SELECT * FROM responsables WHERE id_responsable = ?"
        return pd.read_sql_query(query, conn, params=(id_responsable,))
    finally:
        conn.close()

def insert_responsable(nombre, apellido, telefono=""):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO responsables (nombre, apellido, telefono)
            VALUES (?, ?, ?)
        """, (nombre, apellido, telefono))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

# ========== FUNCIONES DE PACIENTES ==========

def get_pacientes_by_responsable(id_responsable):
    conn = get_connection()
    try:
        query = """
            SELECT p.*, 
                   CASE 
                       WHEN p.fecha_nacimiento IS NOT NULL 
                       THEN CAST((julianday('now') - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER)
                       ELSE NULL 
                   END as edad
            FROM pacientes p 
            WHERE p.id_responsable = ? AND p.activo = 1
            ORDER BY p.nombre, p.apellido
        """
        return pd.read_sql_query(query, conn, params=(id_responsable,))
    finally:
        conn.close()

def insert_paciente(nombre, apellido, fecha_nacimiento, sexo, dni, id_responsable, 
                    medicos="", tipo_relacion="Otro familiar", tiene_cuenta_propia=False):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO pacientes (nombre, apellido, fecha_nacimiento, sexo, dni, 
                                   id_responsable, medicos, tipo_relacion, tiene_cuenta_propia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (nombre, apellido, fecha_nacimiento, sexo, dni, id_responsable, 
              medicos, tipo_relacion, tiene_cuenta_propia))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_paciente_by_id(id_paciente):
    conn = get_connection()
    try:
        query = """
            SELECT p.*, 
                   r.nombre as responsable_nombre, 
                   r.apellido as responsable_apellido,
                   CASE 
                       WHEN p.fecha_nacimiento IS NOT NULL 
                       THEN CAST((julianday('now') - julianday(p.fecha_nacimiento)) / 365.25 AS INTEGER)
                       ELSE NULL 
                   END as edad
            FROM pacientes p 
            LEFT JOIN responsables r ON p.id_responsable = r.id_responsable
            WHERE p.id_paciente = ?
        """
        return pd.read_sql_query(query, conn, params=(id_paciente,))
    finally:
        conn.close()

def get_paciente_by_dni(dni):
    conn = get_connection()
    try:
        query = "SELECT * FROM pacientes WHERE dni = ?"
        return pd.read_sql_query(query, conn, params=(dni,))
    finally:
        conn.close()

# ========== FUNCIONES DE HISTORIAL MÉDICO ==========

def insert_historial_medico(id_paciente, fecha_encuesta=None, peso=None, fumador=None, alcohol=None,
                            dieta=None, actividad_fisica=None, alergias=None, suplementos=None,
                            antecedentes_familiares=None, condiciones_medicas=None, medicacion_actual=None,
                            observaciones=None):
    if fecha_encuesta is None:
        fecha_encuesta = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historial_medico (
                id_paciente, fecha_encuesta, peso, fumador, alcohol, dieta,
                actividad_fisica, alergias, suplementos, antecedentes_familiares,
                condiciones_medicas, medicacion_actual, observaciones
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (id_paciente, fecha_encuesta, peso, fumador, alcohol, dieta,
              actividad_fisica, alergias, suplementos, antecedentes_familiares,
              condiciones_medicas, medicacion_actual, observaciones))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_historial_by_paciente(id_paciente):
    conn = connect_to_supabase()
    try:
        query = "SELECT * FROM historial_medico WHERE id_paciente = ? ORDER BY fecha_encuesta DESC"
        return pd.read_sql_query(query, conn, params=(id_paciente,))
    finally:
        conn.close()

def obtener_edad(dni,conn=None):
    id_paciente = get_id_paciente_por_dni(dni)
    df = execute_query("SELECT fecha_nacimiento FROM pacientes WHERE id_paciente = %s", (id_paciente,), conn)
    if df.empty or not isinstance(df.at[0, "fecha_nacimiento"], datetime.date):
        return None
    fn = df.at[0, "fecha_nacimiento"]
    hoy = datetime.date.today()
    return hoy.year - fn.year - ((hoy.month, hoy.day) < (fn.month, fn.day))

def tiene_antecedente_enfermedad_por_dni(dni, enfermedad, conn=None):
    # Primero obtenemos el id_paciente a partir del dni
    id_paciente = get_id_paciente_por_dni(dni, conn=conn)
    if id_paciente is None:
        return False  # No se encontró paciente
    
    # Ahora consultamos la lista de antecedentes familiares de enfermedades
    query = """
        SELECT antecedentes_familiares_enfermedad
        FROM historial_medico
        WHERE id_paciente = %s;
    """
    
    result = execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    if result is None or result.empty:
        return False  # No hay datos de antecedentes
    
    antecedentes = result.iloc[0]['antecedentes_familiares_enfermedades']
    
    # Si el campo es NULL o vacío
    if not antecedentes:
        return False
    
    # Suponiendo que antecedentes es una lista de strings
    return enfermedad.lower() in [e.lower() for e in antecedentes]
