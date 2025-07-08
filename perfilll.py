import streamlit as st
import pandas as pd
from jinja2 import Environment, FileSystemLoader
import pdfkit
import datetime
import os
import weasyprint

# Se importan las funciones reales, incluyendo la que ejecuta queries SQL
from fEncuesta import get_encuesta_completada, tiene_antecedente_enfermedad_por_dni, get_id_paciente_por_dni
from functions import connect_to_supabase, execute_query

# --- 0. Función UNIFICADA con QUERIES SQL ---

def get_user_data_from_db(dni, conn):
    """
    Obtiene los datos completos del usuario mediante consultas SQL directas,
    uniendo las tablas necesarias para mayor eficiencia.
    
    Args:
        conn: La conexión activa a Supabase. (Aunque no se usa directamente si execute_query ya la gestiona)
        
    Returns:
        dict: Un diccionario completo con todos los datos del usuario.
    """
    try:
        conn=connect_to_supabase()
        # 1. Query principal para unir pacientes e historial_medico
        main_query = """
            SELECT 
                p.id_paciente, p.nombre, p.apellido, p.dni, p.fecha_nacimiento,
                p.tipo_sangre, p.sexo, p.telefono, p.email
                h.colesterol_alto, h.estres_alto,
                h.actividad_fisica, h.alergias, h.condicion, h.alcoholico, h.fumador
            FROM 
                pacientes AS p
            LEFT JOIN 
                historial_medico AS h ON p.id_paciente = h.id_paciente
            WHERE 
                p.dni = %s;
        """
        # execute_query devuelve un DataFrame
        df_paciente = execute_query(main_query, params=(dni,), is_select=True)
        
        if df_paciente.empty:
            st.error("Error: No se encontraron datos para el DNI del usuario.")
            st.stop()
        
        paciente_info = df_paciente.iloc[0].to_dict()
        id_paciente = int(get_id_paciente_por_dni(dni))

        # 2. Query para obtener medicamentos del paciente
        meds_query = """
            SELECT 
                m.nombre, m.dosis_cantidad, m.frecuencia_tipo, m.frecuencia_valor
            FROM 
                medicamentos AS m
            JOIN 
                paciente_medicamentos AS pm ON m.id = pm.id_medicamento
            WHERE 
                pm.id_paciente = %s;
        """
        df_medicamentos = execute_query(meds_query, params=(id_paciente,), is_select=True)
        
        medicamentos_actuales = []
        if not df_medicamentos.empty:
            for _, med in df_medicamentos.iterrows():
                medicamentos_actuales.append({
                    "nombre": med.get('nombre', 'N/A'),
                    "dosis": f"{med.get('dosis_cantidad', '')} {med.get('frecuencia_valor', '')} cada {med.get('frecuencia_tipo', '')}"
                })

        # 3. Query para obtener el estudio más reciente
        estudio_query = """
            SELECT tipo, fecha, descripcion 
            FROM estudios 
            WHERE id_paciente = %s 
            ORDER BY fecha DESC 
            LIMIT 1;
        """
        df_estudio = execute_query(estudio_query, params=(id_paciente,), is_select=True)
        
        estudio_reciente_str = "Ninguno registrado."
        if not df_estudio.empty:
            estudio = df_estudio.iloc[0]
            estudio_reciente_str = f"{estudio.get('tipo', 'Estudio')} ({estudio.get('fecha', '')}): {estudio.get('descripcion', 'Sin descripción.')}"

        # 4. Unificar todos los datos en el diccionario final
        user_data = {
            # --- Datos para el Perfil (PDF) ---
            "nombre": paciente_info.get('nombre', ''),
            "apellido": paciente_info.get('apellido', ''),
            "dni": paciente_info.get('dni', ''),
            "fecha_nacimiento": str(paciente_info.get('fecha_nacimiento', '')),
            "telefono": paciente_info.get('telefono', ''),
            "email": paciente_info.get('email', ''),
            "tipo_sangre": paciente_info.get('tipo_sangre', 'No especificado'),
            "contacto_emergencia_nombre": paciente_info.get('paciente_responsable', 'No especificado'),
            "contacto_emergencia_telefono": "N/A", # Dato no encontrado en el schema
            "alergias": paciente_info.get('alergias', "No se registran alergias."),
            "medicacion_actual": medicamentos_actuales,
            "antecedentes": paciente_info.get('condicion', "No se registran condiciones crónicas."),
            "vacunas": "No especificado en el esquema actual.", # Dato no encontrado en el schema
            "estudios_recientes": estudio_reciente_str,
            
            # --- Datos Adicionales para Estadísticas ---
            "genero": paciente_info.get('sexo'),
            "actividad_fisica": paciente_info.get('actividad_fisica', False),
            "fumador": paciente_info.get('fumador', False),
            "alcohol_frecuente": paciente_info.get('alcoholico', False),
            "presion_arterial_alta": paciente_info.get('presion_arterial_alta', False),
            "colesterol_alto": paciente_info.get('colesterol_alto', False),
            "estres_alto": paciente_info.get('estres_alto', False),
            # Se mantienen las llamadas a la función externa para antecedentes familiares
            'antecedentes_familiares_cancer': tiene_antecedente_enfermedad_por_dni(dni, 'cancer', conn),
            'antecedentes_familiares_diabetes': tiene_antecedente_enfermedad_por_dni(dni, 'diabetes', conn),
            'antecedentes_familiares_hipertension': tiene_antecedente_enfermedad_por_dni(dni, 'hipertension', conn),
        }
        for key, value in user_data.items():
            if value is None:
                if isinstance(user_data.get(key), list):
                     user_data[key] = []
                elif isinstance(user_data.get(key), bool):
                     user_data[key] = False
                else:
                     user_data[key] = "No especificado"
        return user_data

    except Exception as e:
        st.error(f"Ocurrió un error al consultar la base de datos con SQL: {e}")
        st.stop()
        return {}


# --- Conexión a la base de datos ---
# La conexión ahora es gestionada principalmente por la función execute_query
conn = connect_to_supabase()

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Perfil - MedCheck",
    page_icon="👤",
    layout="centered"
)

# --- 1. Verificación y Carga de Datos de Sesión ---
dni = st.session_state.get("dni")
if not dni:
    st.error("⚠️ No has iniciado sesión. Por favor, vuelve a la página de inicio.")
    st.stop()

user_data = get_user_data_from_db(dni, conn)
if not user_data:
    st.warning("No se pudieron cargar los datos del usuario. Inténtalo de nuevo.")
    st.stop()

if "nombre" not in st.session_state:
    st.session_state.nombre = user_data.get("nombre", "Usuario")

# El resto del código no necesita cambios, ya que ahora depende de `user_data` que ya está cargado.
# --- 2. Verificación de Encuesta Completada ---
encuesta_df = get_encuesta_completada(dni, conn=conn)

if not encuesta_df.empty and not encuesta_df.iloc[0]["encuesta_realizada"]:
    st.warning("**Antes de continuar, necesitamos más información.**")
    st.write(
        "Para poder generar informes precisos y ofrecerte la mejor experiencia, "
        "es fundamental que completes una breve encuesta sobre tu salud y hábitos."
    )
    if st.button("📝 Completar Encuesta Médica", type="primary"):
        st.switch_page("pages/_Encuesta.py")
    st.stop()

# --- 3. Header de Bienvenida ---
st.title(f"👋 ¡Hola, {st.session_state.get('nombre', 'Usuario')}!")
st.write("Bienvenido a tu perfil médico. Desde aquí puedes generar informes para tus consultas o emergencias.")
st.divider()

# --- 4. Sección de Generación de Informes ---
st.header("📄 Generar Informe Médico")
st.write("Crea un informe PDF personalizado según tus necesidades del momento.")

tipo_informe = st.selectbox(
    "Selecciona el tipo de informe que necesitas",
    options=["guardia_agil", "historial_completo", "personalizado"],
    format_func=lambda x: {
        "guardia_agil": "🚑 Guardia Ágil - Para emergencias",
        "historial_completo": "📋 Historial Completo - Para consultas",
        "personalizado": "⚙️ Personalizado - Elige qué incluir"
    }[x],
    label_visibility="collapsed"
)

# --- 5. Opciones de Informe Personalizado ---
opciones_informe = {
    "incluir_alergias": True,
    "incluir_medicacion": True,
    "incluir_antecedentes": True,
    "incluir_vacunas": True,
    "incluir_estudios": True,
    "incluir_contacto": True,
}

if tipo_informe == "guardia_agil":
    with st.container(border=True):
        st.subheader("🚑 Informe de Guardia Ágil")
        st.write("**Contenido:** Datos esenciales, alergias, medicación actual y contacto de emergencia.")
        opciones_informe["incluir_antecedentes"] = False
        opciones_informe["incluir_vacunas"] = False
        opciones_informe["incluir_estudios"] = False

elif tipo_informe == "historial_completo":
    with st.container(border=True):
        st.subheader("📋 Informe de Historial Completo")
        st.write("**Contenido:** Todo tu historial médico.")

elif tipo_informe == "personalizado":
    with st.container(border=True):
        st.subheader("⚙️ Informe Personalizado")
        st.write("Selecciona los datos que quieres incluir:")
        col1, col2 = st.columns(2)
        with col1:
            opciones_informe["incluir_alergias"] = st.checkbox("🚨 Incluir Alergias", value=True)
            opciones_informe["incluir_medicacion"] = st.checkbox("💊 Incluir Medicación Actual", value=True)
            opciones_informe["incluir_antecedentes"] = st.checkbox("📜 Incluir Antecedentes")
        with col2:
            opciones_informe["incluir_vacunas"] = st.checkbox("💉 Incluir Vacunas")
            opciones_informe["incluir_estudios"] = st.checkbox("🔬 Incluir Estudios Previos")
            opciones_informe["incluir_contacto"] = st.checkbox("📞 Incluir Contacto de Emergencia", value=True)

st.divider()

# --- 6. Lógica de Generación de PDF y Botón de Descarga ---
# --- 6. Lógica de Generación de Archivos (Refactorizada) ---
def crear_html_string(datos_paciente, opciones):
    """Genera el contenido HTML del informe como un string."""
    if not datos_paciente:
        return ""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    search_paths = [project_root, script_dir]
    env = Environment(loader=FileSystemLoader(search_paths))
    template = env.get_template('Patient Profile Report from Claude.html')
    return template.render(paciente=datos_paciente, opciones=opciones, fecha_generacion=datetime.datetime.now().strftime("%d de %B de %Y a las %H:%M"))

# --- 7. Botones de Acción (Lógica Corregida y Simplificada) ---
col1, col2 = st.columns(2)
with col1:
    if st.button("👁️ Previsualizar HTML", use_container_width=True):
        html_content = crear_html_string(user_data, opciones_informe)
        if html_content:
            with st.expander("Vista Previa del HTML", expanded=True):
                st.components.v1.html(html_content, height=600, scrolling=True)
        else:
            st.warning("No se pudo generar la vista previa del HTML.")

with col2:
    is_disabled = not user_data
    
    # Se genera el HTML primero
    html_para_pdf = crear_html_string(user_data, opciones_informe)
    pdf_bytes = None
    if html_para_pdf:
        try:
            # Luego se convierte a PDF
            pdf_bytes = weasyprint.HTML(string=html_para_pdf).write_pdf()
        except Exception as e:
            st.error(f"Ocurrió un error al convertir a PDF: {e}")

    st.download_button(
        label="📥 Descargar PDF",
        data=pdf_bytes if pdf_bytes else b"",
        file_name=f"InformeMedico_{user_data.get('apellido', 'Usuario')}_{dni}.pdf",
        mime="application/pdf",
        use_container_width=True,
        disabled=is_disabled or not pdf_bytes, # Se deshabilita si no hay datos o si falló la creación del PDF
        type="primary"
    )
            
# --- 8. SECCIÓN DE DEPURACIÓN MANTENIDA ---
st.divider()
with st.expander("🕵️‍♂️ Información de Depuración (Revisa si los datos están aquí)"):
    st.write("Estos son los datos que se están usando para generar el informe:")
    st.json(user_data)

