import streamlit as st
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

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
# Se asume que get_encuesta_completada devuelve un DataFrame de pandas.
encuesta_df = get_encuesta_completada(dni, conn=conn)

# Si el DataFrame no está vacío y el valor de 'encuesta_realizada' es False:
if not encuesta_df.empty and not encuesta_df.iloc[0]["encuesta_realizada"]:
    st.warning("**Antes de continuar, necesitamos más información.**")
    st.write(
        "Para poder generar informes precisos y ofrecerte la mejor experiencia, "
        "es fundamental que completes una breve encuesta sobre tu salud y hábitos."
    )
    
    if st.button("📝 Completar Encuesta Médica", type="primary"):
        # Asegúrate de que la ruta a tu página de encuesta sea correcta
        st.switch_page("pages/_Encuesta.py")
    
    st.stop() # Detiene la ejecución para no mostrar el resto de la página

# --- 3. Header de Bienvenida ---
st.title(f"👋 ¡Hola, {st.session_state.get('nombre', 'Usuario')}!")
st.write("Bienvenido a tu perfil médico. Desde aquí puedes generar informes para tus consultas o emergencias.")
st.divider()

# --- 4. Sección de Generación de Informes ---
st.header("📄 Generar Informe Médico")
st.write("Crea un informe PDF personalizado según tus necesidades del momento.")

# Menú desplegable para seleccionar el tipo de informe
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

# --- 5. Contenedores de Información y Opciones ---
if tipo_informe == "guardia_agil":
    with st.container(border=True):
        st.subheader("🚑 Informe de Guardia Ágil")
        st.write("**Ideal para:** Emergencias y visitas rápidas al hospital.")
        st.write("**Contenido:** Datos esenciales, alergias críticas, medicación actual y contacto de emergencia.")

elif tipo_informe == "historial_completo":
    with st.container(border=True):
        st.subheader("📋 Informe de Historial Completo")
        st.write("**Ideal para:** Consultas con especialistas, segundas opiniones o estudios complejos.")
        st.write("**Contenido:** Historial médico detallado, antecedentes familiares y todos los estudios previos.")

elif tipo_informe == "personalizado":
    with st.container(border=True):
        st.subheader("⚙️ Informe Personalizado")
        st.write("Selecciona a continuación los datos que quieres incluir en tu informe:")
        
        col1, col2 = st.columns(2)
        with col1:
            incluir_alergias = st.checkbox("🚨 Incluir Alergias", value=True)
            incluir_medicacion = st.checkbox("💊 Incluir Medicación Actual", value=True)
            incluir_antecedentes = st.checkbox("📜 Incluir Antecedentes")
        with col2:
            incluir_vacunas = st.checkbox("💉 Incluir Vacunas")
            incluir_estudios = st.checkbox("🔬 Incluir Estudios Previos")
            incluir_contacto = st.checkbox("📞 Incluir Contacto de Emergencia", value=True)

st.divider()

# --- 6. Botones de Acción ---
col1, col2 = st.columns(2)

with col1:
    if st.button("✨ Generar Informe", type="primary", use_container_width=True):
        # Aquí iría la lógica para recopilar los datos y generar el informe
        st.success("¡Informe generado con éxito!")
        st.info("La descarga comenzará en breve...")
        # Lógica de generación y descarga del PDF

with col2:
    if st.button("📥 Descargar PDF", use_container_width=True):
        # Este botón puede ser el que realmente inicie la descarga del archivo generado
        st.info("Funcionalidad de descarga en desarrollo...")
        # Lógica para servir el archivo PDF al usuario

