import streamlit as st

st.title("Encuesta de Bienvenida")

# Ejemplo de preguntas
edad = st.number_input("¿Cuál es tu edad?", min_value=0, max_value=120)
fuma = st.radio("¿Fumás?", ["Sí", "No"])
actividad = st.selectbox("¿Con qué frecuencia hacés actividad física?", ["Nunca", "1 vez por semana", "3 o más veces por semana"])

if st.button("Enviar"):
    # Podés guardar esta info en la base de datos si querés
    st.session_state.encuesta_completada = True
    st.success("¡Gracias por completar la encuesta!")
    st.switch_page("Inicio.py")