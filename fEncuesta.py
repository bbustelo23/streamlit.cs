import pandas as pd
import streamlit as st
from functions import execute_query
from functions import connect_to_supabase
import sqlite3
from datetime import date

def execute_query_debug(query, params=None, conn=None, is_select=False):
    """Versión de execute_query con debugging mejorado"""
    try:
        if conn is None:
            conn = connect_to_supabase()
        
        st.write(f"🔍 Ejecutando query: {query}")
        st.write(f"🔍 Parámetros: {params}")
        st.write(f"🔍 Es SELECT: {is_select}")
        
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if is_select:
            result = cursor.fetchall()
            st.write(f"🔍 Resultado SELECT: {result}")
            return result
        else:
            # Para INSERT, UPDATE, DELETE
            conn.commit()
            affected_rows = cursor.rowcount
            st.write(f"🔍 Filas afectadas: {affected_rows}")
            cursor.close()
            
            if affected_rows > 0:
                st.write("✅ Query ejecutada exitosamente")
                return True
            else:
                st.write("⚠️ Query ejecutada pero no se afectaron filas")
                return False
                
    except Exception as e:
        st.error(f"❌ Error en execute_query: {str(e)}")
        import traceback
        st.write(f"🔍 Traceback: {traceback.format_exc()}")
        
        # Rollback en caso de error
        if conn:
            conn.rollback()
        return False

def get_id_paciente_por_dni(dni, conn=None):
    """Función para obtener el ID del paciente por DNI"""
    try:
        if conn is None:
            conn = connect_to_supabase()
        
        st.write(f"🔍 Buscando paciente con DNI: {dni}")
        query = "SELECT id FROM pacientes WHERE dni = %s"
        st.write(f"🔍 Query: {query}")
        
        result = execute_query(query, params=(dni,), conn=conn, is_select=True)
        st.write(f"🔍 Resultado de búsqueda: {result}")
        
        if result and len(result) > 0:
            patient_id = result[0][0]
            st.write(f"✅ Paciente encontrado con ID: {patient_id}")
            return patient_id
        else:
            st.error(f"❌ No se encontró paciente con DNI: {dni}")
            return None
            
    except Exception as e:
        st.error(f"❌ Error al buscar paciente: {str(e)}")
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
    vacunas=None,
    antecedentes_familiares_enfermedad=None,
    antecedentes_familiares_familiar=None,
    conn=None
):
    try:
        st.write(f"🔍 DEBUG: Iniciando insert_historial con DNI: {dni}")
        
        if fecha_completado is None:
            fecha_completado = date.today()

        if conn is None:
            conn = connect_to_supabase()
            st.write("✅ Conexión a base de datos establecida")

        # Obtener DNI desde session_state si no se pasa como parámetro
        dni = dni or st.session_state.get('dni')
        
        if not dni:
            raise ValueError("DNI no proporcionado")

        st.write(f"🔍 Buscando paciente con DNI: {dni}")
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        
        if id_paciente is None:
            st.error(f"❌ No se encontró paciente con DNI {dni}")
            raise ValueError(f"No se encontró paciente con DNI {dni}")

        id_paciente = int(id_paciente)
        st.write(f"✅ Paciente encontrado con ID: {id_paciente}")

        # Limpiar y validar los datos antes de insertar
        actividad_fisica = actividad_fisica.strip() if actividad_fisica and actividad_fisica.strip() else "No especificado"
        
        # Validar peso - usar None si es 0 o inválido
        if peso is not None and peso <= 0:
            peso = None
            
        # Corregir la lógica de condición y medicación
        condicion_db = condicion if condicion else "No tiene"
        medicacion_db = medicacion_cronica if medicacion_cronica else "No toma"

        # Mostrar todos los valores que se van a insertar
        st.write("🔍 Valores a insertar:")
        valores_debug = {
            'id_paciente': id_paciente,
            'fecha_completado': fecha_completado,
            'peso': peso,
            'fumador': fumador,
            'alcoholico': alcoholico,
            'dieta': dieta,
            'estres_alto': estres_alto,
            'colesterol_alto': colesterol_alto,
            'actividad_fisica': actividad_fisica,
            'condicion': condicion_db,
            'medicacion_cronica': medicacion_db,
            'alergias': alergias,
            'suplementos': suplementos,
            'vacunas': vacunas,
            'antecedentes_familiares_enfermedad': antecedentes_familiares_enfermedad,
            'antecedentes_familiares_familiar': antecedentes_familiares_familiar
        }
        
        for key, value in valores_debug.items():
            st.write(f"  {key}: {value} (tipo: {type(value)})")

        query = """
        INSERT INTO historial_medico
            (id_paciente, fecha_completado, peso, fumador, alcoholico, dieta, estres_alto, colesterol_alto,
             actividad_fisica, condicion, medicacion_cronica, alergias, suplementos, vacunas, antecedentes_familiares_enfermedad, antecedentes_familiares_familiar)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
            alergias,
            suplementos,
            vacunas,
            antecedentes_familiares_enfermedad,
            antecedentes_familiares_familiar
        )

        st.write("🔍 Ejecutando query...")
        st.write(f"Query: {query}")
        
        result = execute_query_debug(query, params=params, conn=conn, is_select=False)
        
        st.write(f"🔍 Resultado de execute_query: {result}")
        
        if result is not False and result is not None:
            st.write("✅ Historial insertado exitosamente")
            return True
        else:
            st.error("❌ Error: execute_query retornó False o None")
            return False
            
    except Exception as e:
        error_msg = f"Error en insert_historial: {str(e)}"
        st.error(f"❌ {error_msg}")
        st.write(f"🔍 Tipo de error: {type(e)}")
        import traceback
        st.write(f"🔍 Traceback completo: {traceback.format_exc()}")
        return False
#nnnnnnnnnnnnnnnnnnnnnnnnnnn
def get_paciente(dni):
    query = "SELECT * FROM pacientes WHERE dni = %s"
    return execute_query(query, (dni,), is_select=True)

def insert_paciente(dni, nombre, apellido, fecha_nacimiento, sexo, email, contraseña, telefono = None, contacto_emergencia = None, tipo_sangre = None, encuesta_completada=False):
    query = """
    INSERT INTO pacientes (dni, nombre, apellido, fecha_nacimiento, sexo, email, contraseña,  telefono, contacto_emergencia, tipo_sangre, encuesta_completada)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
    conn = connect_to_supabase()
    params = (dni, nombre, apellido, fecha_nacimiento, sexo, email, contraseña,  telefono, contacto_emergencia, tipo_sangre, encuesta_completada)
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


"""def insert_historial(
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
    vacunas=None,
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

    
    
    params = (
        id_paciente,
        fecha_completado,
        telefono,
        contacto_emergencia,
        tipo_sangre,
        peso,
        fumador,
        alcoholico,
        dieta,
        estres_alto,
        colesterol_alto,
        actividad_fisica,
        condicion_db,
        medicacion_db,
        alergias,
        suplementos,
        vacunas,
        antecedentes_familiares_enfermedad,
        antecedentes_familiares_familiar
    )

    return execute_query(query, params=params, conn=conn, is_select=False)

"""

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
    
def tiene_alergia_por_dni(dni, alergia, conn=None):
    id_paciente = get_id_paciente_por_dni(dni, conn=conn)
    if id_paciente is None:
        return False
    
    query = """ 
    SELECT alergias FROM historial_medico WHERE id_paciente = %s;
    """
    result = execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    if result is None or result.empty:
        return False
    
    alergias = result.iloc[0]['alergias']
    if not alergias:
        return False
    
    return alergia.lower() in [a.lower() for a in alergias] # Retorna True si la alergia está en la lista de alergias del paciente
    
def tiene_suplemento_por_dni(dni, suplemento, conn=None):
    id_paciente = get_id_paciente_por_dni(dni, conn=conn)
    if id_paciente is None:
        return False
    
    query = """
    SELECT suplementos FROM historial_medico WHERE id_paciente = %s;
    """ 
    result = execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    if result is None or result.empty:
        return False
    
    suplementos = result.iloc[0]['suplementos']
    if not suplementos: 
        return False
    
    return suplemento.lower() in [s.lower() for s in suplementos] # Retorna True si el suplemento está en la lista de suplementos del paciente
    
def tiene_vacuna_por_dni(dni, vacuna, conn=None):
    id_paciente = get_id_paciente_por_dni(dni, conn=conn)
    if id_paciente is None:
        return False
    
    query = """
    SELECT vacunas FROM historial_medico WHERE id_paciente = %s;
    """ 
    result = execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    if result is None or result.empty:
        return False
    
    vacunas = result.iloc[0]['vacunas']
    if not vacunas: 
        return False
    
    return vacuna.lower() in [v.lower() for v in vacunas] # Retorna True si la vacuna está en la lista de vacunas del paciente





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
