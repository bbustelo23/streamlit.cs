
import streamlit as st
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

conn = connect_to_supabase()

# --- Page Config ---
st.set_page_config(page_title="Inicio - MedCheck", page_icon="🏠", layout="wide")
st.title("👤 Perfil")
# --- Verificar si el usuario está logueado ---
dni = st.session_state.get("dni")

if not dni:
    st.warning("No hay un DNI cargado en sesión.")
    st.stop()


# --- Verificar si completó la encuesta ---
encuesta_completada = get_encuesta_completada(dni, conn=conn)

if not encuesta_completada.empty and not encuesta_completada.iloc[0]["encuesta_realizada"]:
    st.warning("Antes de continuar, necesitamos que completes una breve encuesta sobre tu salud y hábitos.")
    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")   # Ajustá el path según la estructura de tu app

    st.stop()


# --- Contenido de la página principal ---
st.title(f"¡Hola, {st.session_state.nombre} 👋!")
st.subheader("Bienvenido a MedCheck")

