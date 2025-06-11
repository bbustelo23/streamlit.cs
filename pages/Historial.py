import streamlit as st
from datetime import date, datetime
from fEncuesta import get_id_paciente_por_dni, get_encuesta_completada
from functions import connect_to_supabase
from fHistorial import insertar_evento_medico, get_eventos_medicos_recientes, get_datos_paciente, get_historial_medico

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Historial Clínico - MedCheck",
    page_icon="🏥",
    layout="centered"  # Un layout centrado es más simple para leer
)

# --- Conexión a la base de datos ---
conn = connect_to_supabase()

# --- 1. Verificación y Carga de Datos ---
dni = st.session_state.get("dni")
if not dni:
    st.error("⚠️ **Acceso Restringido:** Inicia sesión para ver tu historial.")
    st.stop()

datos_paciente = get_datos_paciente(dni, conn=conn)
if datos_paciente is None or datos_paciente.empty:
    st.error("❌ **Error de Datos:** No se encontraron datos para el DNI proporcionado.")
    st.stop()

# --- 2. Encabezado del Paciente ---
paciente = datos_paciente.iloc[0]
st.title(f"👤 {paciente.get('nombre', 'Paciente')}")
st.caption(f"DNI: {paciente.get('dni')} | Fecha de Nacimiento: {paciente.get('fecha_nacimiento', 'N/D')}")
st.divider()

# --- 3. Resumen de la Encuesta Médica ---
st.header("📊 Resumen de la Encuesta")
historial = get_historial_medico(dni, conn=conn)

if historial is not None and not historial.empty:
    datos = historial.iloc[0]
    
    st.subheader("Hábitos y Datos Generales")
    st.write(f"**Peso actual:** {datos.get('peso', 'N/D')} kg")
    st.write(f"**Fumador:** {'Sí' if datos.get('fumador') else 'No'}")
    st.write(f"**Consume alcohol:** {'Sí' if datos.get('alcoholico') else 'No'}")
    
    st.subheader("Condiciones y Antecedentes")
    condicion = datos.get("condicion", "no tiene")
    if condicion and condicion != "no tiene":
        st.write(f"**Condición crónica:** {condicion}")
        st.write(f"**Medicación crónica:** {datos.get('medicacion_cronica', 'N/D')}")
    else:
        st.write("**Condiciones crónicas:** No reportadas.")
        
    if datos.get("antecedentes_familiares_enfermedad"):
        # Lógica para procesar antecedentes (simplificada)
        familiares = datos.get("antecedentes_familiares_familiar", "N/D")
        enfermedades = datos.get("antecedentes_familiares_enfermedad", "N/D")
        st.write(f"**Antecedentes Familiares:** {familiares} - {enfermedades}")
        
else:
    st.warning("📋 **Encuesta Pendiente:** Completa la encuesta médica para ver tu información aquí.")

st.divider()

# --- 4. Historial de Eventos Médicos ---
st.header("🩺 Historial de Eventos Médicos")
eventos = get_eventos_medicos_recientes(dni, conn=conn)

if eventos is not None and not eventos.empty:
    for idx, evento in eventos.iterrows():
        st.subheader(f"🏥 {evento.get('enfermedad', 'Diagnóstico no disponible')}")
        st.caption(f"Fecha: {evento.get('fecha_evento', 'N/D')}")
        if evento.get('sintomas'):
            st.write(f"**Síntomas:** {evento['sintomas']}")
        if evento.get('medicacion'):
            st.write(f"**Medicación:** {evento['medicacion']}")
        if evento.get('comentarios'):
            st.write(f"**Comentarios:** {evento['comentarios']}")
        st.markdown("---") # Pequeño separador entre eventos
else:
    st.info("📋 **Sin Eventos Registrados:** Usa el formulario a continuación para agregar tu primer evento.")

st.divider()

# --- 5. Formulario para Agregar Nuevo Evento ---
st.header("➕ Registrar Nuevo Evento Médico")

with st.form("nuevo_evento_medico", clear_on_submit=True, border=False): # Borde quitado
    enfermedad = st.text_input(
        "Enfermedad o Diagnóstico (*)",
        placeholder="Ej: Gripe, Dolor de cabeza..."
    )
    sintomas = st.text_area(
        "Síntomas",
        placeholder="Ej: Fiebre alta, dolor de garganta..."
    )
    medicacion = st.text_area(
        "Medicación",
        placeholder="Ej: Paracetamol 500mg cada 8hs..."
    )
    
    submitted = st.form_submit_button("💾 Guardar Evento")
    
    if submitted:
        if not enfermedad or not enfermedad.strip():
            st.error("❌ El campo 'Enfermedad o Diagnóstico' es obligatorio.")
        else:
            with st.spinner("Guardando..."):
                success = insertar_evento_medico(
                    dni=dni,
                    enfermedad=enfermedad,
                    medicacion=medicacion,
                    sintomas=sintomas,
                    comentarios="", # Campo de comentarios eliminado del form para simplicidad
                    conn=conn
                )
            if success:
                st.success("✅ ¡Evento guardado!")
                st.rerun() # Recarga la página para mostrar el nuevo evento arriba
            else:
                st.error("❌ Hubo un error al guardar el evento.")