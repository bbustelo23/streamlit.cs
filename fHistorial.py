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
    
#-----------------------------------------------------------------------
def get_estudios_medicos_recientes(dni, conn=None):
    """Obtiene los estudios médicos del paciente con sus imágenes"""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return None
        id_paciente = int(id_paciente)
        
        query = """
        SELECT e.*, i.imagen_base64
        FROM Estudios e
        LEFT JOIN imagenes_estudios i ON e.id_estudio = i.id_estudio
        WHERE e.id_paciente = %s 
        ORDER BY e.fecha DESC
        """
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener estudios médicos: {str(e)}")
        return None

def insertar_estudio_medico(dni, tipo_estudio, fecha_estudio, zona, razon, observaciones=None, imagen_base64=None, conn=None):
    """Inserta un nuevo estudio médico usando la tabla Estudios existente"""
    try:
        # Obtener ID del paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            st.error("No se pudo encontrar el ID del paciente")
            return False
        id_paciente = int(id_paciente)
        
        # Obtener el próximo ID para el estudio
        get_max_id_query = "SELECT COALESCE(MAX(id_estudio), 0) + 1 as next_id FROM Estudios"
        result_id = execute_query(get_max_id_query, conn=conn, is_select=True)
        
        if result_id is not None and not result_id.empty:
            next_id = result_id.iloc[0]['next_id']
        else:
            next_id = 1
        
        # Insertar estudio médico en la tabla Estudios
        # Mapeo de campos según tu estructura:
        # - tipo_estudio -> tipo
        # - fecha_estudio -> fecha  
        # - zona -> zona
        # - razon + observaciones -> descripcion
        
        query = """
        INSERT INTO Estudios 
        (id_estudio, id_paciente, fecha, tipo, zona, descripcion)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        # Combinamos razón y observaciones en descripción
        descripcion_completa = razon.strip()
        if observaciones and observaciones.strip():
            descripcion_completa += f" | Observaciones: {observaciones.strip()}"
        
        params = (
            next_id,
            id_paciente,
            fecha_estudio,
            tipo_estudio.strip(),
            zona.strip(),
            descripcion_completa
        )
        
        result = execute_query(query, params=params, conn=conn, is_select=False)
        
        if result:
            print(f"Estudio médico insertado exitosamente para paciente ID: {id_paciente}")
            
            # Si hay imagen, guardarla en una tabla separada para imágenes
            if imagen_base64:
                guardar_imagen_estudio(next_id, imagen_base64, conn)
            
            return True
        else:
            st.error("Error: No se pudo insertar el estudio médico")
            return False
            
    except Exception as e:
        st.error(f"Error al insertar estudio médico: {str(e)}")
        print(f"Error detallado al insertar estudio: {str(e)}")
        return False

# === FUNCIONES AUXILIARES PARA IMÁGENES ===

def guardar_imagen_estudio(id_estudio, imagen_base64, conn=None):
    """Guarda la imagen de un estudio en una tabla separada"""
    try:
        # Crear tabla para imágenes si no existe
        create_images_table = """
        CREATE TABLE IF NOT EXISTS imagenes_estudios (
            id_imagen INTEGER PRIMARY KEY,
            id_estudio INTEGER,
            imagen_base64 TEXT,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_estudio) REFERENCES Estudios(id_estudio)
        );
        """
        
        try:
            execute_query(create_images_table, conn=conn, is_select=False)
        except Exception as table_error:
            print(f"Error al crear tabla de imágenes: {str(table_error)}")
        
        # Obtener próximo ID para la imagen
        get_max_img_id = "SELECT COALESCE(MAX(id_imagen), 0) + 1 as next_id FROM imagenes_estudios"
        result_img_id = execute_query(get_max_img_id, conn=conn, is_select=True)
        
        if result_img_id is not None and not result_img_id.empty:
            next_img_id = result_img_id.iloc[0]['next_id']
        else:
            next_img_id = 1
        
        # Insertar imagen
        query = """
        INSERT INTO imagenes_estudios (id_imagen, id_estudio, imagen_base64)
        VALUES (%s, %s, %s)
        """
        
        result = execute_query(query, params=(next_img_id, id_estudio, imagen_base64), conn=conn, is_select=False)
        
        if result:
            print(f"Imagen guardada exitosamente para estudio ID: {id_estudio}")
            return True
        else:
            print("Error al guardar imagen del estudio")
            return False
            
    except Exception as e:
        print(f"Error al guardar imagen del estudio: {str(e)}")
        return False

def get_imagen_estudio(id_estudio, conn=None):
    """Obtiene la imagen de un estudio específico"""
    try:
        query = """
        SELECT imagen_base64 FROM imagenes_estudios 
        WHERE id_estudio = %s
        ORDER BY fecha_subida DESC
        LIMIT 1
        """
        return execute_query(query, params=(id_estudio,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener imagen del estudio: {str(e)}")
        return None
    """Elimina un estudio médico específico"""
    try:
        # Verificar que el estudio pertenece al paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return False
        id_paciente = int(id_paciente)
        
        query = """
        DELETE FROM estudios_medicos 
        WHERE id = %s AND id_paciente = %s
        """
        
        result = execute_query(query, params=(estudio_id, id_paciente), conn=conn, is_select=False)
        
        if result:
            print(f"Estudio médico {estudio_id} eliminado exitosamente")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error al eliminar estudio médico: {str(e)}")
        return False

def actualizar_estudio_medico(estudio_id, dni, tipo_estudio=None, fecha_estudio=None, 
                            razon=None, observaciones=None, imagen_base64=None, conn=None):
    """Actualiza un estudio médico existente"""
    try:
        # Verificar que el estudio pertenece al paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return False
        id_paciente = int(id_paciente)
        
        # Construir query dinámicamente según los campos a actualizar
        update_fields = []
        params = []
        
        if tipo_estudio:
            update_fields.append("tipo_estudio = %s")
            params.append(tipo_estudio.strip())
        
        if fecha_estudio:
            update_fields.append("fecha_estudio = %s")
            params.append(fecha_estudio)
        
        if razon:
            update_fields.append("razon = %s")
            params.append(razon.strip())
        
        if observaciones is not None:  # Permitir cadena vacía
            update_fields.append("observaciones = %s")
            params.append(observaciones.strip() if observaciones.strip() else None)
        
        if imagen_base64 is not None:  # Permitir None para eliminar imagen
            update_fields.append("imagen_base64 = %s")
            params.append(imagen_base64)
        
        if not update_fields:
            return False  # No hay nada que actualizar
        
        # Agregar timestamp de actualización
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        # Agregar condiciones WHERE
        params.extend([estudio_id, id_paciente])
        
        query = f"""
        UPDATE estudios_medicos 
        SET {', '.join(update_fields)}
        WHERE id = %s AND id_paciente = %s
        """
        
        result = execute_query(query, params=params, conn=conn, is_select=False)
        
        if result:
            print(f"Estudio médico {estudio_id} actualizado exitosamente")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error al actualizar estudio médico: {str(e)}")
        return False

def get_estadisticas_estudios(dni, conn=None):
    """Obtiene estadísticas de los estudios médicos del paciente"""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return None
        id_paciente = int(id_paciente)
        
        query = """
        SELECT 
            COUNT(*) as total_estudios,
            COUNT(CASE WHEN imagen_base64 IS NOT NULL THEN 1 END) as estudios_con_imagen,
            COUNT(DISTINCT tipo_estudio) as tipos_diferentes,
            MIN(fecha_estudio) as primer_estudio,
            MAX(fecha_estudio) as ultimo_estudio
        FROM estudios_medicos 
        WHERE id_paciente = %s
        """
        
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener estadísticas de estudios: {str(e)}")
        return None

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
        
        # Verificar que existen las tablas
        check_tables_query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_name IN ('eventos_medicos_recientes', 'estudios_medicos')
        """
        
        tables_exist = execute_query(check_tables_query, conn=conn, is_select=True)
        
        return True, f"Todo OK - Paciente ID: {id_paciente}, Tablas disponibles: {tables_exist}"
        
    except Exception as e:
        return False, f"Error en verificación: {str(e)}"