
import pandas as pd
import streamlit as st
from functions import execute_query
from functions import connect_to_supabase


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
        medicacion_cronica, dieta, antecedentes_familiares_enfermedad,
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


from datetime import date

def insert_historial(
    dni,
    fecha_completado=None,
    peso=None,
    fumador=False,
    alcoholico=False,
    dieta=None,
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
        (id_paciente, fecha_completado, peso, fumador, alcoholico, dieta, actividad_fisica,
         condicion, medicacion_cronica, antecedentes_familiares_enfermedad, antecedentes_familiares_familiar)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    params = (
        id_paciente,
        fecha_completado,
        peso,
        fumador,
        alcoholico,
        dieta,
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
