
import streamlit as st


st.session_state.setdefault("nombre", None)
st.session_state.setdefault("dni", None)
st.session_state.setdefault("encuesta_completada", False)

# --- Page Config ---
st.set_page_config(page_title="Inicio - MedCheck", page_icon="🏠", layout="wide")

# --- Verificar si el usuario está logueado ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Tenés que iniciar sesión primero.")
    st.stop()

# --- Verificar si completó la encuesta ---
if "encuesta_completada" not in st.session_state or not st.session_state.encuesta_completada:
    st.title("👋 ¡Hola!")
    st.subheader("Antes de continuar...")

    st.info("Para comenzar a usar MedCheck, necesitamos que completes una breve encuesta sobre tu salud y hábitos.")

    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")   # Ajustá el path según la estructura de tu app

    st.stop()

# --- Contenido de la página principal ---
st.title(f"¡Hola, {st.session_state.nombre} 👋!")
st.subheader("Bienvenido a MedCheck")

