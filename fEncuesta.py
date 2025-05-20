
import pandas as pd
import streamlit as st
from functions import execute_query
from functions import connect_to_supabase


def get_paciente(dni):
    query = "SELECT * FROM pacientes WHERE dni = %s"
    return execute_query(query, (dni,), is_select=True)

def insert_historial(dni, fecha_completado, fumador, alcoholico, peso,
                     condicion=None, medicacion_cronica=None, dieta=False,
                     antecedentes_enfermedad=None, antecedentes_familiar=None,
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
        antecedentes_enfermedad, antecedentes_familiar
    )
    return execute_query(query, params=params, conn=conn, is_select=False)




def get_id_paciente_por_dni(dni, conn=None):
    query = "SELECT id_paciente FROM pacientes WHERE dni = %s;"
    st.write("Ejecutando consulta con dni:", dni)
    
    result = execute_query(query, params=(dni,), conn=conn, is_select=True)
    st.write("Resultado de la consulta:", result)
    
    if result is not None and not result.empty:
        return result.iloc[0]['id_paciente']
    else:
        st.warning(f"No se encontró un paciente con el DNI {dni}")
        return None


def insert_historial(
    dni,
    fecha_completado,
    peso=None,
    fumador=False,
    alcoholico=False,
    dieta=None,
    actividad_fisica=None,
    alergias=None,
    suplementos=None,
    condicion=None,
    medicacion_cronica=None,
    conn=None
):
    id_paciente = get_id_paciente_por_dni(dni, conn=conn)
    if id_paciente is None:
        raise ValueError(f"No se encontró paciente con DNI {dni}")

    #alergias_db = alergias if alergias else "no tiene"
    condicion_db = condicion if condicion else "no tiene"
    medicacion_db = medicacion if condicion else None
    #suplementos_db = suplementos if suplementos else "no toma"

   
    query = """
    INSERT INTO historial 
        (id_paciente, fecha, peso, fumador, alcoholico, dieta, actividad_fisica, condicion, medicacion_cronica)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
        medicacion_db
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
