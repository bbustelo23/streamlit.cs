#-----------------------------------------------------------------aaaaaaaaaaaaaaaaaa--

import streamlit as st
from fEncuesta import get_encuesta_completada, get_id_paciente_por_dni, tiene_antecedente_enfermedad_por_dni
from functions import connect_to_supabase, execute_query 
from datetime import datetime, date

# --- Conexión a la base de datos ---
conn = connect_to_supabase()

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Perfil - MedCheck", 
    page_icon="👤", 
    layout="centered"
)

# --- 1. Verificación de Sesión de Usuario ---
dni = st.session_state.get("dni")
if not dni:
    st.error("⚠️ No has iniciado sesión. Por favor, vuelve a la página de inicio.")
    st.stop()

# --- 2. Verificación de Encuesta Completada ---
encuesta_df = get_encuesta_completada(dni, conn=conn)

if not encuesta_df.empty and not encuesta_df.iloc[0]["encuesta_completada"]:
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
st.write("Crea un informe personalizado según tus necesidades del momento.")

# Menú desplegable para seleccionar el tipo de informe
tipo_informe = st.selectbox(
    "Selecciona el tipo de informe que necesitas",
    options=["", "guardia_agil", "historial_completo", "personalizado"],
    format_func=lambda x: {
        "": "Selecciona una opción...",
        "guardia_agil": "🚑 Guardia Ágil - Para emergencias",
        "historial_completo": "📋 Historial Completo - Para consultas",
        "personalizado": "⚙️ Personalizado - Elige qué incluir"
    }[x],
    label_visibility="collapsed"
)

# --- 5. Configuración para Informe Personalizado ---
incluir_alergias = incluir_medicacion = incluir_antecedentes = True
incluir_vacunas = incluir_estudios = incluir_contacto = True

if tipo_informe == "personalizado":
    with st.container(border=True):
        st.subheader("⚙️ Configuración de Informe Personalizado")
        st.write("Selecciona los datos que quieres incluir:")
        
        col1, col2 = st.columns(2)
        with col1:
            incluir_alergias = st.checkbox("🚨 Incluir Alergias", value=True)
            incluir_medicacion = st.checkbox("💊 Incluir Medicación Actual", value=True)
            incluir_antecedentes = st.checkbox("📜 Incluir Antecedentes")
        with col2:
            incluir_vacunas = st.checkbox("💉 Incluir Vacunas")
            incluir_estudios = st.checkbox("🔬 Incluir Estudios Previos")
            

# --- Helper function ---
def calculate_age(born_date_str):
    """Calcula la edad a partir de una fecha de nacimiento en formato YYYY-MM-DD."""
    if not born_date_str or not isinstance(born_date_str, str):
        return "N/A"
    try:
        born = datetime.strptime(born_date_str, '%Y-%m-%d').date()
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except (ValueError, TypeError):
        return "N/A"


# --- 6. Función para generar datos de paciente (CORREGIDA) ---
def get_datos_paciente(dni):
    """
    Obtiene los datos completos del usuario mediante consultas SQL directas,
    uniendo las tablas necesarias para mayor eficiencia.
    """
    try:
        # 1. Query principal para unir pacientes e historial_medico
        main_query = """
            SELECT 
                p.id_paciente, p.nombre, p.apellido, p.dni, p.fecha_nacimiento,
                p.tipo_sangre, p.sexo, p.telefono, p.email, h.colesterol_alto, h.estres_alto,
                h.actividad_fisica, h.alergias, h.condicion, h.alcoholico, h.fumador
            FROM 
                pacientes AS p
            LEFT JOIN 
                historial_medico AS h ON p.id_paciente = h.id_paciente
            WHERE 
                p.dni = %s;
        """
        df_paciente = execute_query(main_query, params=(dni,), is_select=True)
        
        if df_paciente.empty:
            st.error("Error: No se encontraron datos para el DNI del usuario.")
            st.stop()
        
        paciente_info = df_paciente.iloc[0].to_dict()
        id_paciente = int(paciente_info['id_paciente'])

        # 2. Query para obtener medicamentos del paciente
        meds_query = """
            SELECT 
                m.nombre, m.dosis_cantidad, m.frecuencia_tipo, m.frecuencia_valor
            FROM 
                medicamentos AS m
            JOIN 
                paciente_medicamentos AS pm ON m.id_medicamento = pm.id_medicamento
            WHERE 
                pm.id_paciente = %s;
        """
        df_medicamentos = execute_query(meds_query, params=(id_paciente,), is_select=True)
        
        medicamentos_formateados = []
        if not df_medicamentos.empty:
            for _, med in df_medicamentos.iterrows():
                nombre = med.get('nombre', 'N/A')
                dosis = med.get('dosis_cantidad', '')
                frec_tipo = med.get('frecuencia_tipo', '')
                frec_valor = med.get('frecuencia_valor', '')
                medicamentos_formateados.append(f"{nombre} - {dosis} {frec_valor} cada {frec_tipo}")

        # 3. Query para obtener TODOS los estudios
        estudio_query = """
            SELECT tipo, fecha, descripcion 
            FROM estudios 
            WHERE id_paciente = %s 
            ORDER BY fecha DESC;
        """
        df_estudios = execute_query(estudio_query, params=(id_paciente,), is_select=True)
        
        estudios_formateados = []
        if not df_estudios.empty:
            for _, estudio in df_estudios.iterrows():
                fecha_estudio = estudio.get('fecha', '').strftime('%d/%m/%Y') if estudio.get('fecha') else 'Sin fecha'
                estudios_formateados.append(f"({fecha_estudio}) {estudio.get('tipo', 'Estudio')}: {estudio.get('descripcion', 'Sin descripción.')}")

        # 4. Procesar strings que deben ser listas (alergias, antecedentes)
        alergias_str = paciente_info.get('alergias')
        alergias_list = [a.strip() for a in alergias_str.split(',')] if alergias_str and alergias_str.strip() else []
        
        antecedentes_str = paciente_info.get('condicion')
        antecedentes_list = [a.strip() for a in antecedentes_str.split(',')] if antecedentes_str and antecedentes_str.strip() else []

        # 5. Unificar todos los datos en el diccionario final
        user_data = {
            # --- Datos para el Perfil (PDF) ---
            "nombre": f"{paciente_info.get('nombre', '')} {paciente_info.get('apellido', '')}",
            "dni": paciente_info.get('dni', ''),
            "edad": calculate_age(str(paciente_info.get('fecha_nacimiento', ''))),
            "telefono": paciente_info.get('telefono', 'No especificado'),
            "email": paciente_info.get('email', 'No especificado'),
            "tipo_sangre": paciente_info.get('tipo_sangre', 'No especificado'),
            
            "alergias": alergias_list,
            "medicacion": medicamentos_formateados,
            "antecedentes": antecedentes_list,
            "vacunas": [], # Dato no encontrado en el schema, se devuelve lista vacía
            "estudios": estudios_formateados,
            
            # --- Datos Adicionales para Estadísticas (si se necesitan) ---
            "genero": paciente_info.get('sexo'),
            "actividad_fisica": paciente_info.get('actividad_fisica', False),
            # ... otros datos ...
        }
        return user_data

    except Exception as e:
        st.error(f"Ocurrió un error al consultar la base de datos: {e}")
        return None

# --- 7. Función para mostrar Informe de Guardia Ágil (AJUSTADA) ---
def mostrar_informe_guardia_agil(datos):
    st.markdown("""
    <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); padding: 20px; border-radius: 15px; margin: 20px 0;">
        <h2 style="color: white; text-align: center; margin: 0;">🚑 INFORME DE GUARDIA ÁGIL</h2>
        <p style="color: white; text-align: center; margin: 5px 0;">Para emergencias médicas</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1: # Mantener tu HTML
        st.write(f"**Nombre:** {datos['nombre']}")
        st.write(f"**DNI:** {datos['dni']}")
    
    with col2:
        st.write(f"**Edad:** {datos['edad']} años")
        st.write(f"**Teléfono:** {datos['telefono']}")
        
    
    st.markdown("""<h4 style="color: #ff4757; margin-top: 0;">🚨 Alergias Críticas</h4>""", unsafe_allow_html=True)
    if datos['alergias']:
        for alergia in datos['alergias']:
            st.error(f"⚠️ {alergia}")
    else:
        st.write("No se registran alergias.")
    
    st.markdown("""<h4 style="color: #3742fa; margin-top: 0;">💊 Medicación Actual</h4>""", unsafe_allow_html=True)
    if datos['medicacion']:
        for medicamento in datos['medicacion']:
            st.info(f"💊 {medicamento}")
    else:
        st.write("No se registra medicación.")


# --- 8. Función para mostrar Informe Completo (AJUSTADA) ---
def mostrar_informe_completo(datos):
    st.markdown("""<h2 style="color: white; text-align: center; margin: 0;">📋 HISTORIAL MÉDICO COMPLETO</h2>""", unsafe_allow_html=True)
    
    # Datos personales
    st.markdown("""<h4 style="color: #4834d4; margin-top: 0;">👤 Información Personal</h4>""", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Nombre Completo:** {datos['nombre']}")
        st.write(f"**DNI:** {datos['dni']}")
        st.write(f"**Edad:** {datos['edad']} años")
    with col2:
        st.write(f"**Teléfono:** {datos['telefono']}")
        st.write(f"**Email:** {datos['email']}")
        st.write(f"**Fecha del informe:** {datetime.now().strftime('%d/%m/%Y')}")
    
    # Alergias
    st.markdown("""<h4 style="color: #ff4757; margin-top: 0;">🚨 Alergias</h4>""", unsafe_allow_html=True)
    if datos['alergias']:
        for alergia in datos['alergias']:
            st.write(f"• {alergia}")
    else:
        st.write("• No se registran alergias.")
        
    # Antecedentes, Medicación, Vacunas, Estudios... (aplicar el mismo patrón if/else)
    st.markdown("""<h4 style="color: #ffa726; margin-top: 0;">📜 Antecedentes Médicos</h4>""", unsafe_allow_html=True)
    if datos['antecedentes']:
        for antecedente in datos['antecedentes']:
            st.write(f"• {antecedente}")
    else:
        st.write("• No se registran antecedentes.")
        
    st.markdown("""<h4 style="color: #3742fa; margin-top: 0;">💊 Medicación Actual</h4>""", unsafe_allow_html=True)
    if datos['medicacion']:
        for medicamento in datos['medicacion']:
            st.write(f"• {medicamento}")
    else:
        st.write("• No se registra medicación.")

    st.markdown("""<h4 style="color: #2ed573; margin-top: 0;">💉 Vacunas</h4>""", unsafe_allow_html=True)
    if datos['vacunas']:
        for vacuna in datos['vacunas']:
            st.write(f"• {vacuna}")
    else:
        st.write("• No se registran vacunas.")

    st.markdown("""<h4 style="color: #8e44ad; margin-top: 0;">🔬 Estudios Previos</h4>""", unsafe_allow_html=True)
    if datos['estudios']:
        for estudio in datos['estudios']:
            st.write(f"• {estudio}")
    else:
        st.write("• No se registran estudios.")


# --- 9. Función para mostrar Informe Personalizado (AJUSTADA) ---
def mostrar_informe_personalizado(datos, config):
    st.markdown("""<h2 style="color: white; text-align: center; margin: 0;">⚙️ INFORME PERSONALIZADO</h2>""", unsafe_allow_html=True)
    
    # Datos básicos siempre incluidos
    st.markdown("""<h4 style="color: #00d2d3; margin-top: 0;">👤 Datos del Paciente</h4>""", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    # ... (código igual al tuyo) ...
    
    # Secciones condicionales
    if config['alergias']:
        st.markdown("""<h4 style="color: #ff4757; margin-top: 0;">🚨 Alergias</h4>""", unsafe_allow_html=True)
        if datos['alergias']:
            for alergia in datos['alergias']:
                st.write(f"• {alergia}")
        else:
            st.write("• No se registran alergias.")
    
    # ... aplica el mismo patrón if/else para las otras secciones (medicacion, antecedentes, etc.) ...
    if config['medicacion']:
        st.markdown("""<h4 style="color: #3742fa; margin-top: 0;">💊 Medicación Actual</h4>""", unsafe_allow_html=True)
        if datos['medicacion']:
            for medicamento in datos['medicacion']:
                st.write(f"• {medicamento}")
        else:
            st.write("• No se registra medicación.")

    if config['antecedentes']:
        st.markdown("""<h4 style="color: #ffa726; margin-top: 0;">📜 Antecedentes Médicos</h4>""", unsafe_allow_html=True)
        if datos['antecedentes']:
            for antecedente in datos['antecedentes']:
                st.write(f"• {antecedente}")
        else:
            st.write("• No se registran antecedentes.")

    if config['vacunas']:
        st.markdown("""<h4 style="color: #2ed573; margin-top: 0;">💉 Vacunas</h4>""", unsafe_allow_html=True)
        if datos['vacunas']:
            for vacuna in datos['vacunas']:
                st.write(f"• {vacuna}")
        else:
            st.write("• No se registran vacunas.")

    if config['estudios']:
        st.markdown("""<h4 style="color: #8e44ad; margin-top: 0;">🔬 Estudios Previos</h4>""", unsafe_allow_html=True)
        if datos['estudios']:
            for estudio in datos['estudios']:
                st.write(f"• {estudio}")
        else:
            st.write("• No se registran estudios.")

    
    
    # ... (etc. para el resto de las secciones) ...


# --- 10. Botón para Generar Informe (CORREGIDO) ---
if tipo_informe and st.button("✨ Generar Informe", type="primary", use_container_width=True):
    # Solución principal: pasar el 'dni' a la función
    datos_paciente = get_datos_paciente(dni)
    
    if datos_paciente: # Verificar que los datos se obtuvieron correctamente
        st.success("¡Informe generado con éxito!")
        st.divider()
        
        if tipo_informe == "guardia_agil":
            mostrar_informe_guardia_agil(datos_paciente)
        
        elif tipo_informe == "historial_completo":
            mostrar_informe_completo(datos_paciente)
        
        elif tipo_informe == "personalizado":
            config_personalizado = {
                'alergias': incluir_alergias,
                'medicacion': incluir_medicacion,
                'antecedentes': incluir_antecedentes,
                'vacunas': incluir_vacunas,
                'estudios': incluir_estudios,
                
            }
            mostrar_informe_personalizado(datos_paciente, config_personalizado)
