
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
    INSERT INTO pacientes (dni, nombre, fecha_nacimiento, sexo, contraseña, encuesta_completada)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    conn = connect_to_supabase()
    params = (dni, nombre, fecha_nacimiento, sexo, password, encuesta_completada)
    return execute_query(query, params=params, conn=conn, is_select=False)


def get_id_paciente_por_dni(dni, conn=None):
    conn = connect_to_supabase()
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

    dni = st.session_state.get('dni')
    conn = connect_to_supabase() 
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
    SET encuesta_completada = TRUE
    WHERE dni = %s;
    """
    params = (dni,)
    return execute_query(query, params=params, conn=conn, is_select=False)

#def get_encuesta_completada(dni, conn=None):
    query = """
    SELECT encuesta_completada FROM pacientes WHERE dni = %s;
    """
    params = (dni,)
    return execute_query(query, params=params, conn=conn, is_select=True)


def get_encuesta_completada(dni, conn=None):
    """
    Verifica si un paciente ha completado la encuesta buscando una entrada
    en la tabla historial_medico.
    Devuelve un DataFrame con una columna 'encuesta_completada' (True/False).
    """
    # Primero, obtenemos el id_paciente a partir del DNI
    id_paciente_query = "SELECT id_paciente FROM pacientes WHERE dni = %s"
    df_id = execute_query(id_paciente_query, params=(dni,), conn=conn, is_select=True)

    if df_id.empty:
        # Si no se encuentra el paciente, se asume que la encuesta no está completada.
        return pd.DataFrame([{'encuesta_completada': False}])

    id_paciente = df_id.iloc[0]['id_paciente']

    # Ahora, verificamos si existe una entrada para ese paciente en historial_medico
    historial_query = "SELECT EXISTS (SELECT 1 FROM historial_medico WHERE id_paciente = %s)"
    params = (int(id_paciente),)
    df_exists = execute_query(historial_query, params=params, conn=conn, is_select=True)

    # El resultado de la consulta EXISTS es un booleano en la columna 'exists'
    encuesta_completada = df_exists.iloc[0]['exists'] if not df_exists.empty else False

    # Devolvemos el resultado en el formato que el resto del código espera
    return pd.DataFrame([{'encuesta_completada': encuesta_completada}])

# fEncuesta.py - Funciones para manejo de responsables, pacientes e historial médico



# ========== FUNCIONES DE HISTORIAL MÉDICO ==========


def get_historial_by_paciente(id_paciente):
    conn = connect_to_supabase()
    try:
        query = "SELECT * FROM historial_medico WHERE id_paciente = ? ORDER BY fecha_encuesta DESC"
        return pd.read_sql_query(query, conn, params=(id_paciente,))
    finally:
        conn.close()

def obtener_edad(id_paciente):
    """
    Calcula la edad de un paciente usando su ID directamente.
    """
    if not id_paciente:
        return None
    
    try:
        query = "SELECT fecha_nacimiento FROM pacientes WHERE id_paciente = %s"
        
        # execute_query debería devolver un DataFrame
        df = execute_query(query, params=(int(id_paciente),), is_select=True)
        
        if not df.empty:
            fecha_nacimiento = df.iloc[0]['fecha_nacimiento']
            if fecha_nacimiento:
                hoy = date.today()
                edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                return edad
        return None # Retorna None si no se encuentra paciente o fecha
        
    except Exception as e:
        print(f"Error en obtener_edad: {e}")
        return None

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
