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

def insertar_evento_medico(dni, enfermedad, medicacion, sintomas, comentarios=None, conn=None):
    """Inserta un nuevo evento médico"""
    try:
        # Obtener ID del paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            st.error("No se pudo encontrar el ID del paciente")
            return False
        id_paciente = int(id_paciente)
        
        # Crear tabla si no existe
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
        
        # Insertar evento
        query = """
        INSERT INTO eventos_medicos_recientes 
        (id_paciente, fecha_evento, enfermedad, medicacion, sintomas, comentarios)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        params = (
            id_paciente, 
            date.today(), 
            enfermedad.strip() if enfermedad else None,
            medicacion.strip() if medicacion and medicacion.strip() else None,
            sintomas.strip() if sintomas and sintomas.strip() else None,
            comentarios.strip() if comentarios and comentarios.strip() else None
        )
        
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

#-----------------------------------------------------------------------
# FUNCIONES PARA ESTUDIOS MÉDICOS
#-----------------------------------------------------------------------

def get_estudios_medicos_recientes(dni, conn=None):
    """Obtiene los estudios médicos del paciente con sus imágenes"""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return None
        id_paciente = int(id_paciente)
        
        query = """
        SELECT e.id_estudio, e.id_paciente, e.fecha, e.tipo, e.zona, e.descripcion, i.imagen_base64
        FROM Estudios e
        LEFT JOIN imagenes_estudios i ON e.id_estudio = i.id_estudio
        WHERE e.id_paciente = %s 
        ORDER BY e.fecha DESC
        """
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener estudios médicos: {str(e)}")
        return None

def insertar_estudio_medico(dni, tipo_estudio, fecha_estudio, zona, razon, observaciones=None, conn=None):
    """Inserta un nuevo estudio médico y devuelve True si tiene éxito."""
    try:
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            st.error("No se pudo encontrar el ID del paciente para el estudio.")
            return False
        id_paciente = int(id_paciente)

        descripcion_completa = razon.strip()
        if observaciones and observaciones.strip():
            descripcion_completa += f" | Observaciones: {observaciones.strip()}"

        query = """
        INSERT INTO estudios (id_paciente, fecha, tipo, zona, descripcion)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id_estudio
        """
        params = (id_paciente, fecha_estudio, tipo_estudio.strip(), zona.strip(), descripcion_completa)

        # AVISO IMPORTANTE:
        # La siguiente línea asume que tu función `execute_query` realiza un `conn.commit()`
        # para las operaciones que no son de selección.
        # Estás usando `is_select=True` porque esperas un valor de retorno, pero un INSERT
        # es una operación de escritura y NECESITA un commit.
        result = execute_query(query, params=params, conn=conn, is_select=False) # Cambiado a is_select=False

        # La lógica de `execute_query` debe manejar el retorno de datos incluso con is_select=False
        if result:
            print("✅ Inserción confirmada en la base de datos.")
            return True # <--- ¡LA SOLUCIÓN PRINCIPAL!
        else:
            # Este error ahora significa que el commit o la ejecución fallaron.
            st.error("La base de datos no confirmó el guardado del estudio.")
            return False

    except Exception as e:
        st.error(f"Error crítico al insertar estudio médico: {str(e)}")
        print(f"Error detallado al insertar estudio: {str(e)}")
        return False


def guardar_imagen_estudio(id_estudio, id_paciente, imagen_base64, conn=None):
    """Guarda la imagen de un estudio en la tabla imagenes_estudios"""
    try:
        # Insertar imagen
        query = """
        INSERT INTO imagenes_estudios (id_estudio, id_paciente, imagen_base64)
        VALUES (%s, %s, %s)
        """
        result = execute_query(query, params=(id_estudio, id_paciente, imagen_base64), conn=conn, is_select=False)

        if result:
            print(f"✅ Imagen guardada para estudio ID: {id_estudio}, paciente ID: {id_paciente}")
            return True
        else:
            print("❌ Error al guardar la imagen del estudio")
            return False

    except Exception as e:
        print(f"❌ Error al guardar imagen del estudio: {str(e)}")
        return False




def eliminar_estudio_medico(estudio_id, dni, conn=None):
    """Elimina un estudio médico específico"""
    id_paciente = int(id_paciente)
    try:
        # Verificar que el estudio pertenece al paciente
        id_paciente = get_id_paciente_por_dni(dni, conn=conn)
        if not id_paciente:
            return False
        id_paciente = int(id_paciente)
        
        # Primero eliminar las imágenes asociadas
        delete_images_query = """
        DELETE FROM imagenes_estudios 
        WHERE id_estudio = %s
        """
        execute_query(delete_images_query, params=(estudio_id,), conn=conn, is_select=False)
        
        # Luego eliminar el estudio
        query = """
        DELETE FROM Estudios 
        WHERE id_estudio = %s AND id_paciente = %s
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
                            zona=None, descripcion=None, conn=None):
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
            update_fields.append("tipo = %s")
            params.append(tipo_estudio.strip())
        
        if fecha_estudio:
            update_fields.append("fecha = %s")
            params.append(fecha_estudio)
        
        if zona:
            update_fields.append("zona = %s")
            params.append(zona.strip())
        
        if descripcion is not None:
            update_fields.append("descripcion = %s")
            params.append(descripcion.strip() if descripcion.strip() else None)
        
        if not update_fields:
            return False  # No hay nada que actualizar
        
        # Agregar condiciones WHERE
        params.extend([estudio_id, id_paciente])
        
        query = f"""
        UPDATE Estudios 
        SET {', '.join(update_fields)}
        WHERE id_estudio = %s AND id_paciente = %s
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
            COUNT(i.imagen_base64) as estudios_con_imagen,
            COUNT(DISTINCT e.tipo) as tipos_diferentes,
            MIN(e.fecha) as primer_estudio,
            MAX(e.fecha) as ultimo_estudio
        FROM Estudios e
        LEFT JOIN imagenes_estudios i ON e.id_estudio = i.id_estudio
        WHERE e.id_paciente = %s
        """
        
        return execute_query(query, params=(id_paciente,), conn=conn, is_select=True)
    except Exception as e:
        print(f"Error al obtener estadísticas de estudios: {str(e)}")
        return None

# Función para debug
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
        WHERE table_name IN ('eventos_medicos_recientes', 'estudios', 'imagenes_estudios')
        """
        
        tables_exist = execute_query(check_tables_query, conn=conn, is_select=True)
        
        return True, f"Todo OK - Paciente ID: {id_paciente}, Tablas disponibles: {tables_exist}"
        
    except Exception as e:
        return False, f"Error en verificación: {str(e)}"

# Reemplaza la función existente en tu archivo fHistorial.py con esta versión.
def actualizar_historial_medico(dni, datos_actualizados, conn=None):
    """
    Actualiza los datos de la encuesta de un paciente en la tabla historial_medico.
    
    Args:
        dni (str): DNI del paciente.
        datos_actualizados (dict): Un diccionario con las columnas a actualizar y sus nuevos valores.
        conn: Conexión a la base de datos.
        
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario.
    """
    if not datos_actualizados:
        print("No hay datos para actualizar.")
        return False

    try:
        # Obtener el id_paciente a partir del DNI
        id_paciente = get_id_paciente_por_dni(dni, conn)
        if not id_paciente:
            st.error(f"No se encontró un paciente con el DNI proporcionado.")
            return False
        
        # Asegurarse de que el id_paciente sea un entero
        id_paciente = int(id_paciente)

        # Definir todos los campos válidos de la encuesta médica
        campos_validos = {
            'sangre',
            'telefono', 
            'contacto_emergencia',
            'peso',
            'fumador',
            'alcoholico',
            'dieta',
            'actividad_fisica',
            'estres_alto',
            'colesterol_alto',
            'alergias',
            'suplementos',
            'condicion',
            'medicacion_cronica',
            'vacunas',
            'antecedentes_familiares_enfermedad',
            'antecedentes_familiares_familiar',
            'fecha_completado'
        }
        
        # Filtrar solo los campos válidos
        datos_filtrados = {k: v for k, v in datos_actualizados.items() if k in campos_validos}
        
        if not datos_filtrados:
            st.error("No se encontraron campos válidos para actualizar.")
            return False

        # Construir la parte SET de la consulta SQL dinámicamente
        set_clause = ", ".join([f'"{key}" = %s' for key in datos_filtrados.keys()])
        params = list(datos_filtrados.values())
        params.append(id_paciente)

        query = f"""
            UPDATE historial_medico
            SET {set_clause}
            WHERE id_paciente = %s
        """
        
        # Ejecutar la consulta
        execute_query(query, params=params, conn=conn, is_select=False)
        
        return True

    except Exception as e:
        st.error(f"Error al actualizar el historial médico: {str(e)}")
        print(f"Error detallado al actualizar historial: {str(e)}")
        return False


def crear_formulario_edicion_completo(dni, conn=None):
    """
    Crea un formulario completo para editar todos los campos de la encuesta médica.
    
    Args:
        dni (str): DNI del paciente
        conn: Conexión a la base de datos
    """
    st.title("✏️ Editar Encuesta Médica")
    
    # Obtener datos actuales del paciente
    datos_actuales = get_historial_medico_por_dni(dni, conn)
    
    if datos_actuales.empty:
        st.error("No se encontraron datos del historial médico para este paciente.")
        return
    
    # Extraer los datos actuales
    historial = datos_actuales.iloc[0]
    
    # Crear el formulario con todos los campos
    with st.form("editar_historial_completo"):
        st.subheader("Información básica")
        
        # Tipo de sangre
        sangre_options = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        sangre_index = sangre_options.index(historial.get('sangre', 'A-')) if historial.get('sangre') in sangre_options else 1
        sangre = st.radio("¿Qué tipo de sangre tenés?", sangre_options, index=sangre_index)
        
        # Teléfonos
        telefono = st.text_input("¿Cuál es tu número de teléfono?", value=historial.get('telefono', ''))
        emergencia = st.text_input("¿Cuál es el número de teléfono de tu contacto de emergencia?", value=historial.get('emergencia', ''))
        
        # Peso
        peso = st.number_input("¿Cuál es tu peso actual (kg)?", min_value=0.0, step=0.1, value=float(historial.get('peso', 0)))
        
        st.subheader("Hábitos")
        
        # Fumador
        fumador = st.radio("¿Fumás?", ["Sí", "No"], index=0 if historial.get('fumador') else 1)
        
        # Alcohol
        alcoholico = st.radio("¿Consumís alcohol?", ["Sí", "No"], index=0 if historial.get('alcoholico') else 1)
        
        # Actividad física
        actividad_fisica = st.radio("¿Hacés actividad física?", ["Sí", "No"], index=0 if historial.get('actividad_fisica') == 'Sí' else 1)
        
        # Dieta
        sigue_dieta = st.radio("¿Seguís alguna dieta específica?", ["Sí", "No"], index=0 if historial.get('dieta') else 1)
        
        # Estrés
        estres_options = ["Alto", "Medio", "Bajo"]
        estres_index = 0 if historial.get('estres_alto') else 1
        estres = st.radio("Nivel de Estrés:", estres_options, index=estres_index)
        
        # Colesterol
        colesterol = st.radio("¿Colesterol alto?", ["Sí", "No"], index=0 if historial.get('colesterol_alto') else 1)
        
        st.subheader("Condiciones médicas")
        
        # Condición crónica
        tiene_condicion = st.radio("¿Tenés alguna condición médica crónica diagnosticada?", ["Sí", "No"], 
                                 index=0 if historial.get('condicion') else 1)
        condicion = ""
        medicacion = ""
        if tiene_condicion == "Sí":
            condicion = st.text_input("¿Cuál es la condición?", value=historial.get('condicion', ''))
            toma_medicacion = st.radio("¿Tomás medicación para esta condición?", ["Sí", "No"], 
                                     index=0 if historial.get('medicacion_cronica') else 1)
            if toma_medicacion == "Sí":
                medicacion = st.text_input("¿Qué medicación tomás?", value=historial.get('medicacion_cronica', ''))
        
        # Alergias
        alergias_actuales = historial.get('alergias', []) or []
        tiene_alergias = st.radio("¿Tenés alergias?", ["Sí", "No"], index=0 if alergias_actuales else 1)
        alergias = []
        if tiene_alergias == "Sí":
            alergias_text = st.text_area("Lista de alergias (una por línea):", 
                                       value="\n".join(alergias_actuales) if alergias_actuales else "")
            alergias = [a.strip() for a in alergias_text.split('\n') if a.strip()]
        
        # Suplementos
        suplementos_actuales = historial.get('suplementos', '')
        suplementos = st.radio("¿Tomás suplementos?", ["Sí", "No"], index=0 if suplementos_actuales else 1)
        suplemento = ""
        if suplementos == "Sí":
            suplemento = st.text_input("¿Qué suplemento?", value=suplementos_actuales or '')
        
        # Vacunas
        vacunas_actuales = historial.get('vacunas', []) or []
        tiene_vacuna = st.radio("¿Tenés vacunas puestas?", ["Sí", "No"], index=0 if vacunas_actuales else 1)
        vacunas = []
        if tiene_vacuna == "Sí":
            vacunas_text = st.text_area("Lista de vacunas (una por línea):", 
                                      value="\n".join(vacunas_actuales) if vacunas_actuales else "")
            vacunas = [v.strip() for v in vacunas_text.split('\n') if v.strip()]
        
        # Antecedentes familiares
        enfermedades_actuales = historial.get('antecedentes_familiares_enfermedad', []) or []
        familiares_actuales = historial.get('antecedentes_familiares_familiar', []) or []
        
        antecedentes_familiares = st.radio("¿Tenés antecedentes familiares de alguna enfermedad?", ["Sí", "No"], 
                                         index=0 if enfermedades_actuales else 1)
        enfermedades = []
        familiares = []
        if antecedentes_familiares == "Sí":
            # Combinar datos actuales para mostrar
            antecedentes_text = ""
            if enfermedades_actuales and familiares_actuales:
                for i, (enf, fam) in enumerate(zip(enfermedades_actuales, familiares_actuales)):
                    antecedentes_text += f"{fam}: {enf}\n"
            
            antecedentes_input = st.text_area("Antecedentes familiares (formato: familiar: enfermedad, uno por línea):",
                                            value=antecedentes_text)
            
            # Procesar input
            for linea in antecedentes_input.split('\n'):
                if ':' in linea:
                    familiar, enfermedad = linea.split(':', 1)
                    familiares.append(familiar.strip())
                    enfermedades.append(enfermedad.strip())
        
        # Botón de submit
        submitted = st.form_submit_button("Actualizar Historial Médico")
        
        if submitted:
            # Preparar datos para actualizar
            datos_actualizados = {
                'sangre': sangre,
                'telefono': telefono,
                'emergencia': emergencia,
                'peso': peso,
                'fumador': (fumador == "Sí"),
                'alcoholico': (alcoholico == "Sí"),
                'dieta': (sigue_dieta == "Sí"),
                'actividad_fisica': actividad_fisica,
                'estres_alto': (estres == "Alto"),
                'colesterol_alto': (colesterol == "Sí"),
                'alergias': alergias if tiene_alergias == "Sí" else None,
                'suplementos': suplemento if suplementos == "Sí" else None,
                'condicion': condicion if tiene_condicion == "Sí" else None,
                'medicacion_cronica': medicacion if tiene_condicion == "Sí" and medicacion else None,
                'vacunas': vacunas if tiene_vacuna == "Sí" else None,
                'antecedentes_familiares_enfermedad': enfermedades if antecedentes_familiares == "Sí" else None,
                'antecedentes_familiares_familiar': familiares if antecedentes_familiares == "Sí" else None,
            }
            
            # Actualizar en la base de datos
            if actualizar_historial_medico(dni, datos_actualizados, conn):
                st.success("¡Historial médico actualizado exitosamente!")
                st.rerun()
            else:
                st.error("Error al actualizar el historial médico.")