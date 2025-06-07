import streamlit as st
from datetime import date, datetime
from fEncuesta import get_id_paciente_por_dni, get_encuesta_completada
from functions import connect_to_supabase
from fHistorial import insertar_evento_medico, get_eventos_medicos_recientes, get_datos_paciente, get_historial_medico

# Configuración de la página
st.set_page_config(
    page_title="Historial Clínico",
    page_icon="🏥",
    layout="wide"
)

# CSS personalizado para diseño moderno
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2C3E50;
        margin-bottom: 30px;
        padding: 25px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .patient-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
    }
    
    .info-section {
        background: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border-left: 5px solid #3498db;
    }
    
    .medical-event {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 4px solid #16a085;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }
    
    .data-item {
        background: #f8f9fa;
        padding: 12px 15px;
        margin: 8px 0;
        border-radius: 8px;
        border-left: 3px solid #3498db;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .data-label {
        font-weight: 600;
        color: #2c3e50;
    }
    
    .data-value {
        color: #34495e;
        font-weight: 500;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #f39c12;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .success-box {
        background: linear-gradient(135deg, #d4fcff 0%, #96e6a1 100%);
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #27ae60;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 15px;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .section-title {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 25px;
        font-size: 1.5em;
        font-weight: 600;
    }
    
    .form-container {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 6px 25px rgba(0,0,0,0.1);
        border-top: 4px solid #e74c3c;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 30px;
        border-radius: 25px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    .antecedentes-item {
        background: #e8f4fd;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 8px;
        border-left: 3px solid #3498db;
    }
    
    .stat-number {
        font-size: 2em;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .tab-content {
        padding: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Conexión a la base de datos
conn = connect_to_supabase()

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🏥 Historial Clínico Completo</h1>
    <p>Información médica integral del paciente</p>
</div>
""", unsafe_allow_html=True)

# Verificar DNI en sesión
dni = st.session_state.get("dni")

if not dni:
    st.markdown("""
    <div class="warning-box">
        <h3>⚠️ Acceso Restringido</h3>
        <p>No hay un DNI válido en la sesión. Por favor, inicia sesión primero.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Obtener datos del paciente
datos_paciente = get_datos_paciente(dni, conn=conn)

if datos_paciente is None or datos_paciente.empty:
    st.markdown("""
    <div class="warning-box">
        <h3>❌ Error de Datos</h3>
        <p>No se encontraron datos del paciente en el sistema.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Información del paciente
paciente = datos_paciente.iloc[0]

# Header del paciente
st.markdown(f"""
<div class="patient-card">
    <h2>👤 {paciente['nombre']}</h2>
    <p><strong>DNI:</strong> {paciente['dni']} | <strong>Fecha de Nacimiento:</strong> {paciente['fecha_nacimiento']} | <strong>Sexo:</strong> {paciente['sexo']}</p>
</div>
""", unsafe_allow_html=True)

# Métricas rápidas
col1, col2, col3, col4 = st.columns(4)

with col1:
    encuesta_status = "✅ Completada" if paciente.get('encuesta_realizada', False) else "❌ Pendiente"
    st.markdown(f"""
    <div class="metric-card">
        <div class="stat-number">📋</div>
        <div><strong>Encuesta Médica</strong></div>
        <div>{encuesta_status}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    # Calcular edad aproximada
    try:
        from datetime import datetime
        birth_date = datetime.strptime(str(paciente['fecha_nacimiento']), '%Y-%m-%d')
        age = datetime.now().year - birth_date.year
    except:
        age = "N/D"
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="stat-number">{age}</div>
        <div><strong>Años</strong></div>
        <div>Edad aproximada</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    # Contar eventos médicos
    eventos = get_eventos_medicos_recientes(dni, conn=conn)
    num_eventos = len(eventos) if eventos is not None and not eventos.empty else 0
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="stat-number">{num_eventos}</div>
        <div><strong>Eventos</strong></div>
        <div>Médicos registrados</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="stat-number">🩺</div>
        <div><strong>Estado</strong></div>
        <div>Activo</div>
    </div>
    """, unsafe_allow_html=True)

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📊 Datos de la Encuesta", "🩺 Eventos Médicos", "➕ Agregar Evento"])

with tab1:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">📊 Información de la Encuesta Médica</h2>', unsafe_allow_html=True)
    
    # Obtener historial médico
    historial = get_historial_medico(dni, conn=conn)
    
    if historial is not None and not historial.empty:
        datos = historial.iloc[0]
        
        # Sección: Información General
        st.markdown('<div class="info-section">', unsafe_allow_html=True)
        st.markdown("### 🏃‍♂️ Información General")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f'<div class="data-item"><span class="data-label">Peso actual:</span><span class="data-value">{datos.get("peso", "No registrado")} kg</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-item"><span class="data-label">¿Fumador?:</span><span class="data-value">{"Sí" if datos.get("fumador") else "No"}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-item"><span class="data-label">Consume alcohol:</span><span class="data-value">{"Sí" if datos.get("alcoholico") else "No"}</span></div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown(f'<div class="data-item"><span class="data-label">Sigue dieta:</span><span class="data-value">{"Sí" if datos.get("dieta") else "No"}</span></div>', unsafe_allow_html=True)
            if datos.get("actividad_fisica"):
                st.markdown(f'<div class="data-item"><span class="data-label">Actividad física:</span><span class="data-value">{datos["actividad_fisica"]}</span></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="data-item"><span class="data-label">Última actualización:</span><span class="data-value">{datos.get("fecha_completado", "N/D")}</span></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección: Condiciones Médicas
        st.markdown('<div class="info-section">', unsafe_allow_html=True)
        st.markdown("### 💊 Condiciones Médicas y Tratamientos")
        
        if datos.get("condicion") and datos["condicion"] != "no tiene":
            st.markdown(f'<div class="data-item"><span class="data-label">Condición crónica:</span><span class="data-value">{datos["condicion"]}</span></div>', unsafe_allow_html=True)
            if datos.get("medicacion_cronica"):
                st.markdown(f'<div class="data-item"><span class="data-label">Medicación crónica:</span><span class="data-value">{datos["medicacion_cronica"]}</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="data-item"><span class="data-label">Condiciones crónicas:</span><span class="data-value">No reporta condiciones médicas crónicas</span></div>', unsafe_allow_html=True)
        
        # Mostrar alergias y suplementos si existen
        if datos.get("alergias"):
            st.markdown(f'<div class="data-item"><span class="data-label">Alergias:</span><span class="data-value">{datos["alergias"]}</span></div>', unsafe_allow_html=True)
        
        if datos.get("suplementos"):
            st.markdown(f'<div class="data-item"><span class="data-label">Suplementos:</span><span class="data-value">{datos["suplementos"]}</span></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Sección: Antecedentes Familiares
        if datos.get("antecedentes_familiares_enfermedad"):
            st.markdown('<div class="info-section">', unsafe_allow_html=True)
            st.markdown("### 👨‍👩‍👧‍👦 Antecedentes Familiares")
            
            # Manejar los antecedentes familiares
            enfermedades = datos["antecedentes_familiares_enfermedad"]
            familiares = datos["antecedentes_familiares_familiar"]
            
            # Convertir a listas si son strings
            if isinstance(enfermedades, str):
                try:
                    import ast
                    enfermedades = ast.literal_eval(enfermedades) if enfermedades.startswith('[') else [enfermedades]
                except:
                    enfermedades = [enfermedades]
            
            if isinstance(familiares, str):
                try:
                    import ast
                    familiares = ast.literal_eval(familiares) if familiares.startswith('[') else [familiares]
                except:
                    familiares = [familiares]
            
            if enfermedades and familiares:
                for i, (familiar, enfermedad) in enumerate(zip(familiares, enfermedades)):
                    st.markdown(f'<div class="antecedentes-item"><strong>{familiar.title()}:</strong> {enfermedad}</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="warning-box">
            <h3>📋 Encuesta Pendiente</h3>
            <p>No se encontraron datos de la encuesta médica. Complete la encuesta médica para ver la información completa aquí.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">🩺 Historial de Eventos Médicos Recientes</h2>', unsafe_allow_html=True)
    
    eventos = get_eventos_medicos_recientes(dni, conn=conn)
    
    if eventos is not None and not eventos.empty:
        for idx, evento in eventos.iterrows():
            st.markdown(f"""
            <div class="medical-event">
                <h4>🏥 {evento['enfermedad']}</h4>
                <p><strong>📅 Fecha:</strong> {evento['fecha_evento']}</p>
                {"<p><strong>💊 Medicación:</strong> " + str(evento['medicacion']) + "</p>" if evento.get('medicacion') else ""}
                {"<p><strong>🤒 Síntomas:</strong> " + str(evento['sintomas']) + "</p>" if evento.get('sintomas') else ""}
                {"<p><strong>📝 Comentarios:</strong> " + str(evento['comentarios']) + "</p>" if evento.get('comentarios') else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="warning-box">
            <h3>📋 Sin Eventos Registrados</h3>
            <p>No hay eventos médicos recientes registrados. Use la pestaña "Agregar Evento" para comenzar a registrar eventos médicos.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Reemplaza la sección del formulario en tu archivo principal (dentro del tab3)

with tab3:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">➕ Registrar Nuevo Evento Médico</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # Botón de debug (opcional - puedes quitarlo después)
    if st.button("🔍 Verificar Conexión (Debug)"):
        from fHistorial import verificar_conexion_y_permisos
        success, message = verificar_conexion_y_permisos(dni, conn=conn)
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
    
    with st.form("nuevo_evento_medico", clear_on_submit=True):
        st.markdown("### 🩺 Información del Evento Médico")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enfermedad = st.text_input(
                "🦠 Enfermedad/Diagnóstico *", 
                placeholder="Ej: Gripe, Dolor de cabeza, Gastroenteritis...",
                help="Campo obligatorio. Describe el diagnóstico o enfermedad."
            )
            
            medicacion = st.text_area(
                "💊 Medicación utilizada", 
                placeholder="Ej: Paracetamol 500mg cada 8hs, Ibuprofeno 400mg...",
                help="Describe los medicamentos utilizados y las dosis."
            )
        
        with col2:
            sintomas = st.text_area(
                "🤒 Síntomas experimentados", 
                placeholder="Ej: Fiebre alta, dolor de garganta, náuseas...",
                help="Describe los síntomas que experimentaste."
            )
            
            comentarios = st.text_area(
                "📝 Comentarios adicionales", 
                placeholder="Cualquier información adicional importante...",
                help="Observaciones, evolución, recomendaciones médicas, etc."
            )
        
        # Botón de envío
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button("💾 Guardar Evento Médico", use_container_width=True)
        
        if submitted:
            # Validaciones más estrictas
            if not enfermedad or not enfermedad.strip():
                st.error("❌ El campo 'Enfermedad/Diagnóstico' es obligatorio y no puede estar vacío.")
            elif len(enfermedad.strip()) < 2:
                st.error("❌ El diagnóstico debe tener al menos 2 caracteres.")
            else:
                # Mostrar lo que se va a guardar (para debug)
                with st.expander("🔍 Datos a guardar (debug)"):
                    st.write(f"**DNI:** {dni}")
                    st.write(f"**Enfermedad:** '{enfermedad.strip()}'")
                    st.write(f"**Medicación:** '{medicacion.strip() if medicacion.strip() else 'Vacío'}'")
                    st.write(f"**Síntomas:** '{sintomas.strip() if sintomas.strip() else 'Vacío'}'")
                    st.write(f"**Comentarios:** '{comentarios.strip() if comentarios.strip() else 'Vacío'}'")
                
                # Intentar guardar
                try:
                    with st.spinner("Guardando evento médico..."):
                        success = insertar_evento_medico(
                            dni=dni,
                            enfermedad=enfermedad.strip(),
                            medicacion=medicacion.strip() if medicacion and medicacion.strip() else None,
                            sintomas=sintomas.strip() if sintomas and sintomas.strip() else None,
                            comentarios=comentarios.strip() if comentarios and comentarios.strip() else None,
                            conn=conn
                        )
                    
                    if success:
                        st.markdown("""
                        <div class="success-box">
                            <h3>✅ ¡Evento Guardado!</h3>
                            <p>El evento médico se ha registrado correctamente en tu historial.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Recargar página después de 2 segundos
                        st.rerun()
                    else:
                        st.error("❌ Error al guardar el evento médico. Revisa los logs para más detalles.")
                        
                except Exception as e:
                    st.error(f"❌ Error inesperado al guardar: {str(e)}")
                    st.write("**Detalles del error:**")
                    st.code(str(e))
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)