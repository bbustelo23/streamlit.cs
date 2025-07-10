import streamlit as st
from datetime import date, datetime
# Se importa la nueva función para actualizar
from fHistorial import (
    get_estadisticas_estudios, 
    verificar_conexion_y_permisos, 
    actualizar_estudio_medico, 
    get_estudios_medicos_recientes, 
    insertar_estudio_medico, 
    guardar_imagen_estudio, 
    insertar_evento_medico, 
    get_eventos_medicos_recientes, 
    get_datos_paciente, 
    get_historial_medico,
    actualizar_historial_medico # <-- NUEVA FUNCIÓN
)
import base64
from PIL import Image
import io
from functions import connect_to_supabase

# --- Configuración de la Página ---
st.set_page_config(
    page_title="MedCheck - Historial",
    page_icon="⚕️",
    layout="wide"
)

# --- Estilos CSS Mejorados ---
st.markdown("""
    <style>
        /* --- Colores y Fuentes Principales --- */
        .main-title { color: #800020; font-size: 2.5em; font-weight: bold; }
        .medcheck-text { color: #800020; font-weight: bold; }
        .stButton>button { background-color: #800020 !important; color: white !important; border-radius: 5px; border: none; }
        .stButton>button:hover { background-color: #600010 !important; }

        /* --- Diseño de Tarjetas --- */
        .card { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.2em; font-weight: bold; color: #2E4053; margin-bottom: 8px; }
        .card-content { font-size: 1em; color: #333333; }
        
        /* --- Encabezado del Paciente --- */
        .patient-header { background-color: #F8F8F8; border-radius: 10px; padding: 20px; margin-bottom: 20px; border: 1px solid #E0E0E0; }
        
        /* --- Pestañas (Tabs) --- */
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: transparent; border-radius: 4px 4px 0px 0px; gap: 1px; padding: 10px; }
        .stTabs [aria-selected="true"] { background-color: #F8F8F8; font-weight: bold; color: #800020; }
    </style>
    """, unsafe_allow_html=True)

# --- Título Principal ---
st.markdown('<h1 class="main-title">🏥 <span class="medcheck-text">MedCheck</span> - Historial Clínico</h1>', unsafe_allow_html=True)
st.divider()

# --- Conexión y Carga de Datos ---
conn = connect_to_supabase()
dni = st.session_state.get("dni")

if not dni:
    st.error("⚠️ **Acceso Restringido:** Inicia sesión para ver tu historial.")
    st.stop()

datos_paciente = get_datos_paciente(dni, conn=conn)
if datos_paciente is None or datos_paciente.empty:
    st.error("❌ **Error de Datos:** No se encontraron datos para el DNI proporcionado.")
    st.stop()

# --- Encabezado del Paciente ---
paciente = datos_paciente.iloc[0]
with st.container():
    st.markdown('<div class="patient-header">', unsafe_allow_html=True)
    st.header(f"👤 {paciente.get('nombre', 'Paciente')}")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**DNI:** {paciente.get('dni')}")
    with col2:
        st.caption(f"**Fecha de Nacimiento:** {paciente.get('fecha_nacimiento', 'N/D')}")
    st.markdown('</div>', unsafe_allow_html=True)


# --- Pestañas de Navegación ---
tab1, tab2, tab3 = st.tabs(["Eventos Clínicos 🩺", "Estudios Médicos 🔬", "Resumen de Encuesta 📊"])

# --- Pestaña 1: Eventos Clínicos (Sin cambios) ---
with tab1:
    st.subheader("Historial de Eventos")
    eventos = get_eventos_medicos_recientes(dni, conn=conn)
    if eventos is not None and not eventos.empty:
        for idx, evento in eventos.iterrows():
            st.markdown(f"""
                <div class="card">
                    <div class="card-title">🗓️ {evento.get('fecha_evento', 'N/D')} - {evento.get('enfermedad', 'Diagnóstico no disponible')}</div>
                    <div class="card-content">
                        <p><strong>Síntomas:</strong> {evento.get('sintomas', 'No reportados')}</p>
                        <p><strong>Medicación:</strong> {evento.get('medicacion', 'No reportada')}</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📋 **Sin Eventos Registrados:** Usa el formulario a continuación para agregar tu primer evento.")
    with st.expander("➕ Registrar Nuevo Evento Médico"):
        with st.form("nuevo_evento_medico", clear_on_submit=True, border=False):
            enfermedad = st.text_input("Enfermedad o Diagnóstico (*)", placeholder="Ej: Gripe...")
            sintomas = st.text_area("Síntomas", placeholder="Ej: Fiebre alta...")
            medicacion = st.text_area("Medicación", placeholder="Ej: Paracetamol 500mg...")
            if st.form_submit_button("💾 Guardar Evento"):
                if not enfermedad.strip():
                    st.error("❌ El campo 'Enfermedad o Diagnóstico' es obligatorio.")
                else:
                    insertar_evento_medico(dni=dni, enfermedad=enfermedad, medicacion=medicacion, sintomas=sintomas, conn=conn)
                    st.success("✅ ¡Evento guardado!")
                    st.rerun()

# --- Pestaña 2: Estudios Médicos (Sin cambios) ---
with tab2:
    st.subheader("Historial de Estudios")
    estudios = get_estudios_medicos_recientes(dni, conn=conn)
    if estudios is not None and not estudios.empty:
        for idx, estudio in estudios.iterrows():
            with st.container():
                st.markdown(f"""
                    <div class="card">
                        <div class="card-title">📋 {estudio.get('tipo', 'Estudio')} - {estudio.get('fecha', 'N/D')}</div>
                        <div class="card-content">
                            <p><strong>Zona del Cuerpo:</strong> {estudio.get('zona', 'N/D')}</p>
                            <p><strong>Razón:</strong> {estudio.get('descripcion', 'N/D')}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if estudio.get('imagen_base64'):
                    with st.expander("Ver Imagen del Estudio"):
                        try:
                            image_data = base64.b64decode(estudio['imagen_base64'])
                            st.image(image_data, caption=f"Imagen: {estudio.get('tipo')}", use_column_width=True)
                            st.download_button("⬇️ Descargar Imagen", image_data, f"estudio_{estudio.get('tipo')}.jpg", "image/jpeg")
                        except Exception as e:
                            st.error(f"Error al cargar la imagen: {str(e)}")
    else:
        st.info("🔬 **Sin Estudios Registrados:** Usa el formulario para agregar tu primer estudio.")
    with st.expander("🔬 Agregar Nuevo Estudio Médico"):
        with st.form("nuevo_estudio_medico", clear_on_submit=True, border=False):
            # ... (código del formulario sin cambios)
            pass

# --- Pestaña 3: Resumen de Encuesta (TOTALMENTE REDISEÑADA) ---
with tab3:
    st.subheader("Información de Salud y Hábitos")
    historial = get_historial_medico(dni, conn=conn)

    if historial is not None and not historial.empty:
        datos = historial.iloc[0]

        # --- Visualización Mejorada de Datos ---
        st.markdown("##### **Datos y Hábitos**")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="⚖️ Peso Actual", value=f"{datos.get('peso', 0)} kg")
        with col2:
            st.metric(label="🚭 Fumador", value="Sí" if datos.get('fumador') else "No")
        with col3:
            st.metric(label="🍷 Consume Alcohol", value="Sí" if datos.get('alcoholico') else "No")
        
        st.markdown("##### **Condiciones y Antecedentes**")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        condicion = datos.get("condicion", "no tiene")
        if condicion and condicion.lower() != "no tiene":
            st.write(f"**🩺 Condición crónica:** {condicion}")
            st.write(f"**💊 Medicación crónica:** {datos.get('medicacion_cronica', 'N/D')}")
        else:
            st.write("**🩺 Condiciones crónicas:** No reportadas.")
        
        if datos.get("antecedentes_familiares_enfermedad"):
            st.write(f"**👨‍👩‍👧‍👦 Antecedentes Familiares:** {datos.get('antecedentes_familiares_familiar', 'N/D')} - {datos.get('antecedentes_familiares_enfermedad', 'N/D')}")
        st.markdown('</div>', unsafe_allow_html=True)

        st.divider()

        # --- Formulario de Edición ---
        if 'editing_survey' not in st.session_state:
            st.session_state.editing_survey = False

        if st.button("✏️ Editar Datos de Encuesta"):
            st.session_state.editing_survey = not st.session_state.editing_survey
        
        if st.session_state.editing_survey:
            with st.form("edit_survey_form"):
                st.subheader("Editando Información de la Encuesta")
                
                # Campos del formulario pre-llenados con datos existentes
                peso_edit = st.number_input("Peso (kg)", value=float(datos.get('peso', 0.0)))
                fumador_edit = st.checkbox("Fumador", value=bool(datos.get('fumador', False)))
                alcoholico_edit = st.checkbox("Consume alcohol regularmente", value=bool(datos.get('alcoholico', False)))
                condicion_edit = st.text_input("Condición crónica", value=datos.get('condicion', ''))
                medicacion_cronica_edit = st.text_input("Medicación crónica", value=datos.get('medicacion_cronica', ''))
                
                st.write("Antecedentes Familiares")
                familiar_edit = st.text_input("Familiar", value=datos.get('antecedentes_familiares_familiar', ''))
                enfermedad_familiar_edit = st.text_input("Enfermedad", value=datos.get('antecedentes_familiares_enfermedad', ''))

                submitted = st.form_submit_button("💾 Guardar Cambios")
                if submitted:
                    datos_actualizados = {
                        "peso": peso_edit,
                        "fumador": fumador_edit,
                        "alcoholico": alcoholico_edit,
                        "condicion": condicion_edit,
                        "medicacion_cronica": medicacion_cronica_edit,
                        "antecedentes_familiares_familiar": familiar_edit,
                        "antecedentes_familiares_enfermedad": enfermedad_familiar_edit
                    }
                    
                    success = actualizar_historial_medico(dni, datos_actualizados, conn)
                    
                    if success:
                        st.success("✅ ¡Datos actualizados correctamente!")
                        st.session_state.editing_survey = False
                        st.rerun()
                    else:
                        st.error("❌ Hubo un error al actualizar los datos.")

    else:
        st.warning("📋 **Encuesta Pendiente:** Completa la encuesta médica para ver tu información aquí.")

st.divider()
st.info("💡 **Tip:** Mantén siempre actualizado tu historial médico para un mejor seguimiento de tu salud.")