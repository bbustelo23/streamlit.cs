import streamlit as st
from fEncuesta import insert_historial, update_encuesta_completada, get_encuesta_completada
from functions import connect_to_supabase

conn = connect_to_supabase()

st.title("📝 Encuesta médica")

dni = st.session_state.get("dni")

if not dni:
    st.warning("No hay un DNI cargado en sesión.")
    st.stop()

encuesta_completada = get_encuesta_completada(dni, conn=conn)

if not encuesta_completada.empty and encuesta_completada.iloc[0]["encuesta_completada"]:
    st.warning("Ya completaste la encuesta.")
    st.stop()

sangre = st.radio("¿Qué tipo de sangre tenés?", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], index=1)
telefono = st.text_input("¿Cuál es tu número de teléfono?") 
emergencia = st.text_input("¿Cuál es el número de teléfono de tu contacto de emergencia?")

fumador = st.radio("¿Fumás?", ["Sí", "No"], index=1)
alcoholico = st.radio("¿Consumís alcohol?", ["Sí", "No"], index=1)
peso = st.number_input("¿Cuál es tu peso actual (kg)?", min_value=0.0, step=0.1) 

    # Condición crónica
tiene_condicion = st.radio("¿Tenés alguna condición médica crónica diagnosticada?", ["Sí", "No"], index=1)
if tiene_condicion == "Sí":
    condicion = st.text_input("¿Cuál es la condición?")
    toma_medicacion = st.radio("¿Tomás medicación para esta condición?", ["Sí", "No"], index=1)
    if toma_medicacion == "Sí":
        medicacion = st.text_input("¿Qué medicación tomás?")

actividad_fisica = st.radio("¿Hacés actividad física?", ["Sí", "No"], index=1)
sigue_dieta = st.radio("¿Seguís alguna dieta específica?", ["Sí", "No"], index=1)
if sigue_dieta == "Sí":
    tipo_dieta = st.text_input("¿Qué tipo de dieta?")


estres = st.radio("Nivel de Estres:", ["Alto", "Medio", "Bajo"], index = 1)
colesterol = st.radio("¿Colesterol alto?", ["Si", "No"], index=1)

tiene_alergias = st.radio("¿Tenés alergias?", ["Sí", "No"], index=1)
alergias = []  # lista vacía donde guardamos las alergias

if tiene_alergias == "Sí": 
    st.markdown("### Detalles de alergias")

    cantidad_ale = st.number_input("¿Cuántas alergias querés declarar?", min_value=1, step=1)

    for i in range(cantidad_ale):
        alergia_input = st.text_input(f"Alergia #{i+1}", key=f"alergia_{i}")
        
        if alergia_input.strip():
            alergias.append(alergia_input.strip())


suplementos = st.radio("¿Tomás suplementos?", ["Sí", "No"], index=1)
if suplementos == "Sí":
    suplemento = st.text_input("¿Qué suplemento?")


tiene_vacuna = st.radio("¿Tenés vacunas puestas?", ["Sí", "No"], index=1)
vacunas = []

if tiene_vacuna == "Sí": 
    st.markdown("### Detalles de vacunas")

    with st.form("form_vacunas", clear_on_submit=False):
        cantidad_vacunas = st.number_input("¿Cuántas vacunas querés declarar?", min_value=1, step=1, key="num_vacunas")

        vacuna_inputs = []
        for i in range(cantidad_vacunas):
            vacuna_nombre = st.text_input(f"Nombre de la vacuna #{i+1}", key=f"vacuna_{i}")
            vacuna_inputs.append(vacuna_nombre)

        submitted_vacunas = st.form_submit_button("Guardar vacunas")

        if submitted_vacunas:
            vacunas = [v.strip() for v in vacuna_inputs if v.strip()]
            st.success("Vacunas registradas correctamente.")


antecedentes_familiares = st.radio("¿Tenés antecedentes familiares de alguna enfermedad?", ["Sí", "No"], index=1)
if antecedentes_familiares == "Sí":
    st.markdown("### Detalles de antecedentes")
    
    cantidad = st.number_input("¿Cuántos antecedentes querés declarar?", min_value=1, step=1)
    
    enfermedades = []
    familiares = []
    
    for i in range(cantidad):
        col1, col2 = st.columns(2)
        with col1:
            familiar = st.text_input(f"Familiar #{i+1} (Ej: madre, padre, abuelo)", key=f"familiar_{i}")
        with col2:
            diagnostico = st.text_input(f"Diagnóstico del familiar #{i+1}", key=f"diagnostico_{i}")
        
        if familiar.strip() and diagnostico.strip():
            familiares.append(familiar.strip())
            enfermedades.append(diagnostico.strip())


submit = st.button("Enviar encuesta") 
from datetime import date

if submit:
    try:
        # Validar que los campos requeridos estén presentes
        if not st.session_state.get('dni'):
            st.error("Error: DNI no encontrado en la sesión")
            st.stop()
        
        # Llamar a la función insert_historial con manejo de errores
        success = insert_historial(
            dni=st.session_state.dni,
            fecha_completado=date.today(),
            peso=peso,
            fumador=(fumador == "Sí"),
            alcoholico=(alcoholico == "Sí"),
            dieta=(sigue_dieta == "Sí"),
            estres_alto=(estres == "Alto"),
            colesterol_alto=(colesterol == "Si"),
            actividad_fisica=actividad_fisica,  # Asegúrate de que esta variable esté definida
            alergias=alergias if tiene_alergias == "Sí" else None,
            suplementos=suplemento if suplementos == "Sí" else None,
            condicion=condicion if tiene_condicion == "Sí" else None,
            medicacion_cronica=medicacion if tiene_condicion == "Sí" and toma_medicacion == "Sí" else None,
            vacunas=vacunas if tiene_vacuna == "Sí" else None,
            antecedentes_familiares_enfermedad=enfermedades if antecedentes_familiares == "Sí" else None,
            antecedentes_familiares_familiar=familiares if antecedentes_familiares == "Sí" else None,
            conn=conn
        )
        
        if success:
            # Solo actualizar encuesta_completada si insert_historial fue exitoso
            update_result = update_encuesta_completada(dni=st.session_state.get("dni"), conn=conn)
            
            if update_result:
                st.success("¡Encuesta completada y guardada con éxito!")
                st.switch_page("Inicio.py")
            else:
                st.error("Error al actualizar el estado de la encuesta")
        else:
            st.error("Error al guardar el historial médicoo")
            
    except Exception as e:
        st.error(f"Error al procesar la encuesta: {str(e)}")
        print(f"Error detallado: {str(e)}")  # Para debugging



