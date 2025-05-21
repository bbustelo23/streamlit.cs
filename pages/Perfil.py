
import streamlit as st


# --- Page Config ---
st.set_page_config(page_title="Inicio - MedCheck", page_icon="🏠", layout="wide")
st.title("👤 Perfil")
# --- Verificar si el usuario está logueado ---
dni = st.session_state.get("dni")

if not dni:
    st.warning("No hay un DNI cargado en sesión.")
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

