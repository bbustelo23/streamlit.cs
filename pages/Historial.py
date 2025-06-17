import streamlit as st
from datetime import date, datetime
from fEncuesta import get_id_paciente_por_dni, get_encuesta_completada
from functions import connect_to_supabase
from fHistorial import get_estadisticas_estudios, verificar_conexion_y_permisos, actualizar_estudio_medico, get_estudios_medicos_recientes, insertar_estudio_medico, guardar_imagen_estudio, get_imagen_estudio, insertar_evento_medico, get_eventos_medicos_recientes, get_datos_paciente, get_historial_medico
import base64
from PIL import Image
import io

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Historial Clínico - MedCheck",
    page_icon="🏥",
    layout="centered"
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
        st.markdown("---")
else:
    st.info("📋 **Sin Eventos Registrados:** Usa el formulario a continuación para agregar tu primer evento.")

st.divider()

# --- 5. Formulario para Agregar Nuevo Evento Médico ---
st.header("➕ Registrar Nuevo Evento Médico")

with st.form("nuevo_evento_medico", clear_on_submit=True, border=False):
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
                    comentarios="",
                    conn=conn
                )
            if success:
                st.success("✅ ¡Evento guardado!")
                st.rerun()
            else:
                st.error("❌ Hubo un error al guardar el evento.")

st.divider()

# --- 6. Historial de Estudios Médicos ---
st.header("🔬 Estudios Médicos")
estudios = get_estudios_medicos_recientes(dni, conn=conn)

if estudios is not None and not estudios.empty:
    for idx, estudio in estudios.iterrows():
        with st.expander(f"📋 {estudio.get('tipo', 'Estudio')} - {estudio.get('fecha', 'N/D')}"):
            st.write(f"**Tipo de Estudio:** {estudio.get('tipo', 'N/D')}")
            st.write(f"**Zona:** {estudio.get('zona', 'N/D')}")
            st.write(f"**Fecha:** {estudio.get('fecha', 'N/D')}")
            st.write(f"**Descripción:** {estudio.get('descripcion', 'N/D')}")
            
            # Mostrar imagen si existe
            if estudio.get('imagen_base64'):
                try:
                    image_data = base64.b64decode(estudio['imagen_base64'])
                    image = Image.open(io.BytesIO(image_data))
                    st.image(image, caption=f"Imagen del estudio: {estudio.get('tipo')}", use_column_width=True)
                    
                    # Botón para descargar la imagen
                    st.download_button(
                        label="⬇️ Descargar Imagen",
                        data=image_data,
                        file_name=f"estudio_{estudio.get('tipo', 'imagen')}_{estudio.get('fecha', 'fecha')}.jpg",
                        mime="image/jpeg"
                    )
                except Exception as e:
                    st.error(f"Error al cargar la imagen: {str(e)}")
else:
    st.info("🔬 **Sin Estudios Registrados:** Usa el formulario a continuación para agregar tu primer estudio médico.")

st.divider()

# --- 7. Formulario para Agregar Nuevo Estudio Médico ---
st.header("🔬 Agregar Estudio Médico")
st.caption("Sube radiografías, tomografías, análisis de sangre, etc.")

with st.form("nuevo_estudio_medico", clear_on_submit=True, border=False):
    col1, col2 = st.columns(2)
    
    with col1:
        tipo_estudio = st.selectbox(
            "Tipo de Estudio (*)",
            ["", "Radiografía", "Tomografía", "Resonancia Magnética", "Ecografía", 
             "Análisis de Sangre", "Análisis de Orina", "Electrocardiograma", 
             "Mamografía", "Colonoscopía", "Endoscopía", "Otro"]
        )
        
        if tipo_estudio == "Otro":
            tipo_estudio_personalizado = st.text_input("Especificar tipo de estudio:")
            if tipo_estudio_personalizado:
                tipo_estudio = tipo_estudio_personalizado
    
    with col2:
        fecha_estudio = st.date_input(
            "Fecha del Estudio (*)",
            value=date.today(),
            max_value=date.today()
        )
    
    zona = st.text_input(
        "Zona del Cuerpo (*)",
        placeholder="Ej: Rodilla derecha, Tórax, Abdomen, Brazo izquierdo..."
    )
    
    razon = st.text_area(
        "Razón del Estudio (*)",
        placeholder="Ej: Control de rutina, dolor persistente, seguimiento post-operatorio..."
    )
    
    observaciones = st.text_area(
        "Observaciones o Resultados",
        placeholder="Ej: Valores normales, se observa fractura, inflamación detectada..."
    )
    
    # Carga de imagen
    st.subheader("📷 Cargar Imagen del Estudio")
    uploaded_file = st.file_uploader(
        "Selecciona una imagen (JPG, PNG, PDF)",
        type=['jpg', 'jpeg', 'png', 'pdf'],
        help="Puedes subir una foto de la radiografía, análisis o estudio médico"
    )
    
    # Preview de la imagen
    if uploaded_file is not None:
        if uploaded_file.type.startswith('image/'):
            image = Image.open(uploaded_file)
            st.image(image, caption="Vista previa de la imagen", use_column_width=True)
        else:
            st.info("📄 Archivo PDF cargado correctamente")
    
    submitted_estudio = st.form_submit_button("🔬 Guardar Estudio Médico")
    
    if submitted_estudio:
        if not tipo_estudio or not zona or not zona.strip() or not razon or not razon.strip():
            st.error("❌ Los campos 'Tipo de Estudio', 'Zona del Cuerpo' y 'Razón del Estudio' son obligatorios.")
        else:
            with st.spinner("Guardando estudio médico..."):
                # Convertir imagen a base64 si existe
                imagen_base64 = None
                if uploaded_file is not None:
                    try:
                        if uploaded_file.type.startswith('image/'):
                            # Para imágenes
                            image = Image.open(uploaded_file)
                            # Redimensionar si es muy grande
                            if image.width > 1024 or image.height > 1024:
                                image.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                            
                            # Convertir a RGB si es necesario
                            if image.mode in ("RGBA", "P"):
                                image = image.convert("RGB")
                            
                            # Convertir a bytes
                            img_byte_arr = io.BytesIO()
                            image.save(img_byte_arr, format='JPEG', quality=85)
                            img_byte_arr = img_byte_arr.getvalue()
                            
                            # Convertir a base64
                            imagen_base64 = base64.b64encode(img_byte_arr).decode()
                        else:
                            # Para PDFs u otros archivos
                            file_bytes = uploaded_file.read()
                            imagen_base64 = base64.b64encode(file_bytes).decode()
                            
                    except Exception as e:
                        st.error(f"Error al procesar la imagen: {str(e)}")
                        imagen_base64 = None
                
                success = insertar_estudio_medico(
                    dni=dni,
                    tipo_estudio=tipo_estudio,
                    fecha_estudio=fecha_estudio,
                    zona=zona,
                    razon=razon,
                    observaciones=observaciones,
                    imagen_base64=imagen_base64,
                    conn=conn
                )
                
                if success:
                    st.success("✅ ¡Estudio médico guardado exitosamente!")
                    st.rerun()
                else:
                    st.error("❌ Hubo un error al guardar el estudio médico.")

# --- 8. Información adicional ---
st.divider()
st.info("💡 **Tip:** Mantén siempre actualizado tu historial médico para un mejor seguimiento de tu salud.")