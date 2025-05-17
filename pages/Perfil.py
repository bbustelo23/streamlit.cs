import streamlit as st

# --- Page Config ---
st.set_page_config(page_title="Inicio - MedCheck", page_icon="🏠", layout="wide")

# --- Verificar si el usuario está logueado ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Tenés que iniciar sesión primero.")
    st.stop()

# --- Contenido de la página principal ---
st.title(f"¡Hola, {st.session_state.dni} 👋!")
st.subheader("Bienvenido a MedCheck")

# --- Sección de perfil ---
st.markdown("---")
st.subheader("Perfil")

