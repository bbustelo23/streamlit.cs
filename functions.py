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
    Establishes a direct connection to the Supabase PostgreSQL database
    using credentials from Streamlit's secrets.
    """
    try:
        conn = psycopg2.connect(
            host=st.secrets["database"]["host"],
            port=st.secrets["database"]["port"],
            dbname=st.secrets["database"]["dbname"],
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"]
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Error de conexión: No se pudo conectar a la base de datos. Verifica las credenciales. Detalle: {e}")
        return None
    except Exception as e:
        st.error(f"Ocurrió un error inesperado al conectar a la base de datos: {e}")
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


    """
    Adds a new employee to the Empleado table.
    """

    query = "INSERT INTO empleado (nombre, dni, telefono, fecha_contratacion, salario) VALUES (%s, %s, %s, %s, %s)"
    params = (nombre, dni, telefono, fecha_contratacion, salario)
    
    return execute_query(query, params=params, is_select=False)

