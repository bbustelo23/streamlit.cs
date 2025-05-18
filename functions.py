import psycopg2
import os
from dotenv import load_dotenv
import pandas as pd
import datetime
import streamlit as st

# Load environment variables from .env file
load_dotenv()

def connect_to_supabase():
    """
    Connects to the Supabase PostgreSQL database using transaction pooler details
    and credentials stored in environment variables.
    """
    try:
        # Retrieve connection details from environment variables
        host = os.getenv("SUPABASE_DB_HOST")
        port = int(os.getenv("SUPABASE_DB_PORT"))
        dbname = os.getenv("SUPABASE_DB_NAME")
        user = os.getenv("SUPABASE_DB_USER")
        password = os.getenv("SUPABASE_DB_PASSWORD")

        # Check if all required environment variables are set
        if not all([host, port, dbname, user, password]):
            print("Error: One or more Supabase environment variables are not set.")
            print("Please set SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME, SUPABASE_DB_USER, and SUPABASE_DB_PASSWORD.")
            return None

        # Establish the connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )
        print("Successfully connected to Supabase database.")
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to Supabase database: {e}")
        return None



def execute_query(query, params=None, conn=None, is_select=True):
    """
    Executes a SQL query and returns the results as a pandas DataFrame for SELECT queries,
    or executes DML operations (INSERT, UPDATE, DELETE) and returns success status.
    """
    try:
        close_conn = False
        if conn is None:
            conn = connect_to_supabase()
            close_conn = True

        cursor = conn.cursor()

        # Ejecutar consulta con o sin parámetros
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if is_select:
            results = cursor.fetchall()
            colnames = [desc[0] for desc in cursor.description]
            result = pd.DataFrame(results, columns=colnames)
        else:
            conn.commit()
            result = True

        cursor.close()
        if close_conn:
            conn.close()

        return result
    except Exception as e:
        print(f"Error executing query: {e}")
        if conn and not is_select:
            conn.rollback()
        return pd.DataFrame() if is_select else False

def add_employee(nombre, dni, telefono, fecha_contratacion, salario):
    """
    Adds a new employee to the Empleado table.
    """

    query = "INSERT INTO empleado (nombre, dni, telefono, fecha_contratacion, salario) VALUES (%s, %s, %s, %s, %s)"
    params = (nombre, dni, telefono, fecha_contratacion, salario)
    
    return execute_query(query, params=params, is_select=False)

def get_paciente(dni):
    query = "SELECT * FROM pacientes WHERE dni = %s"
    return execute_query(query, (dni,), is_select=True)


def insert_paciente(nombre, fecha_nacimiento, sexo, contraseña, dni, encuesta_completada, conn=None):
    """
    Inserta un nuevo paciente en la base de datos.
    Devuelve True si se insertó correctamente, False si hubo un error.
    """
    query = """
    INSERT INTO pacientes (nombre, fecha_nacimiento, sexo, contraseña, dni, encuesta_completada)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    params = (nombre, fecha_nacimiento, sexo, contraseña, int(dni), encuesta_completada)
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

def update_encuesta_completada(dni, encuesta_completada):
    query = """
    UPDATE pacientes
    SET encuesta_completada = %s
    WHERE dni = %s;
    """
    params = (encuesta_completada, dni)
    return execute_query(query, params=params, conn=conn, is_select=False)



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

    if peso is not None:
        peso = float(peso) 
    fumador = bool(fumador)
    alcoholico = bool(alcoholico)
   
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