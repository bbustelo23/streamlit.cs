import streamlit as st
import datetime
from functions import update_encuesta_completada, insert_historial

st.title("📝 Encuesta médica")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Tenés que iniciar sesión primero.")
    st.stop()

    
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

sigue_dieta = st.radio("¿Seguís alguna dieta específica?", ["Sí", "No"], index=1)
if sigue_dieta == "Sí":
    tipo_dieta = st.text_input("¿Qué tipo de dieta?")

    
#antecedentes_familiares = st.radio("¿Tenés antecedentes familiares de alguna enfermedad?", ["Sí", "No"], index=1)
#if antecedentes_familiares == "Sí":
#    st.markdown("### Detalles de antecedentes")
#    cantidad = st.number_input("¿Cuántos antecedentes querés declarar?", min_value=1, step=1)
#    antecedentes = []
#    for i in range(cantidad):
#        familiar = st.text_input(f"Familiar #{i+1} (Ej: madre, padre, abuelo)")
#        diagnostico = st.text_input(f"Diagnóstico del familiar #{i+1}")
#        antecedentes.append((familiar, diagnostico))

submit = st.button("Enviar encuesta") 
from datetime import date

if submit:
    insert_historial(
        dni=st.session_state.dni,
        fecha_completado=date.today(),
        fumador=(fumador == "Sí"),
        alcoholico=(alcoholico == "Sí"),
        peso=peso,
        condicion=condicion if tiene_condicion == "Sí" else None,
        medicacion_cronica = medicacion if tiene_condicion == "Sí" and toma_medicacion == "Sí" else None,
        dieta=(sigue_dieta == "Sí"),
    )

    update_encuesta_completada(dni=st.session_state.dni)

    st.success("¡Encuesta completada y guardada con éxito!")
    st.switch_page("Inicio.py")


