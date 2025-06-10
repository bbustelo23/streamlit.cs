import streamlit as st
import pandas as pd
from datetime import date
from functions import execute_query
from fEncuesta import get_id_paciente_por_dni, get_encuesta_completada

# Funciones auxiliares
def get_historial_medico(dni, conn=None):
    """Obtiene el historial médico del paciente"""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return None
        
        id_paciente = int(id_paciente)
        query = """
        SELECT * FROM historial_medico 
        WHERE id_paciente = %s 
        ORDER BY fecha_completado DESC
        LIMIT 1
        """
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        st.error(f"Error al obtener historial médico: {str(e)}")
        return None

def get_datos_paciente(dni, conn=None):
    """Obtiene los datos básicos del paciente"""
    try:
        query = "SELECT * FROM pacientes WHERE dni = %s"
        return execute_query(query, params=(dni,), conn=conn, is_select=True)
    except Exception as e:
        st.error(f"Error al obtener datos del paciente: {str(e)}")
        return None

def get_eventos_medicos_recientes(dni, conn=None):
    """Obtiene los eventos médicos del paciente"""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return None
        id_paciente = int(id_paciente)
        query = """
        SELECT * FROM eventos_medicos_recientes 
        WHERE id_paciente = %s 
        ORDER BY fecha_evento DESC
        """
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener eventos médicos: {str(e)}")
        return None

def insertar_evento_medico(dni, enfermedad, medicacion, sintomas, comentarios, conn=None):
    """Inserta un nuevo evento médico"""
    try:
        # Obtener ID del paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            st.error("No se pudo encontrar el ID del paciente")
            return False
        id_paciente = int(id_paciente)
        # Crear tabla si no existe (con manejo de errores mejorado)
        create_table_query = """
        CREATE TABLE IF NOT EXISTS eventos_medicos_recientes (
            id SERIAL PRIMARY KEY,
            id_paciente INTEGER,
            fecha_evento DATE NOT NULL DEFAULT CURRENT_DATE,
            enfermedad TEXT NOT NULL,
            medicacion TEXT,
            sintomas TEXT,
            comentarios TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Ejecutar creación de tabla
        try:
            execute_query(create_table_query, conn=conn, is_select=False)
        except Exception as table_error:
            print(f"Error al crear tabla (puede que ya exista): {str(table_error)}")
            # Continuar aunque falle la creación de tabla
        
        # Insertar evento
        query = """
        INSERT INTO eventos_medicos_recientes 
        (id_paciente, fecha_evento, enfermedad, medicacion, sintomas, comentarios)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Preparar parámetros (convertir None a NULL para campos opcionales)
        params = (
            id_paciente, 
            date.today(), 
            enfermedad.strip() if enfermedad else None,
            medicacion.strip() if medicacion and medicacion.strip() else None,
            sintomas.strip() if sintomas and sintomas.strip() else None,
            comentarios.strip() if comentarios and comentarios.strip() else None
        )
        
        # Ejecutar inserción
        result = execute_query(query, params=params, conn=conn, is_select=False)
        
        if result:
            print(f"Evento médico insertado exitosamente para paciente ID: {id_paciente}")
            return True
        else:
            st.error("Error: No se pudo insertar el evento médico")
            return False
            
    except Exception as e:
        st.error(f"Error al insertar evento médico: {str(e)}")
        print(f"Error detallado: {str(e)}")
        return False

# Función adicional para debug
def verificar_conexion_y_permisos(dni, conn=None):
    """Función para verificar que todo funcione correctamente"""
    try:
        # Verificar conexión
        test_query = "SELECT 1 as test"
        test_result = execute_query(test_query, conn=conn, is_select=True)
        
        if test_result is None:
            return False, "No se pudo conectar a la base de datos"
        
        # Verificar que existe el paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return False, "No se encontró el paciente en la base de datos"
        id_paciente = int(id_paciente)
        # Verificar que existe la tabla
        check_table_query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'eventos_medicos_recientes'
        );
        """
        
        table_exists = execute_query(check_table_query, conn=conn, is_select=True)
        
        return True, f"Todo OK - Paciente ID: {id_paciente}, Tabla existe: {table_exists}"
        
    except Exception as e:
        return False, f"Error en verificación: {str(e)}"