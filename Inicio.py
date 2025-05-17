
import streamlit as st
from functions import get_paciente
from functions import insert_paciente

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False

# --- Page Configuration (Optional but Recommended) ---
st.set_page_config(
    page_title="MedCheck",
    layout="wide" # "wide" or "centered"
)

# --- Main Application ---
if not st.session_state.logged_in:
    st.title("Bienvenido a MedCheck!")
    st.subheader("¿Qué es MedCheck?")
    st.write("MedCheck es una aplicación web que te permite gestionar tu salud de manera fácil y eficiente.")
    st.write("Con MedCheck, puedes registrar y seguir tu progreso en cuanto a salud, mejorar tu estilo de vida y tomar decisiones informadas sobre tu bienestar.")
else:
    st.title("MedCheck - Inicio")
    st.subheader("¡Bienvenido!")
    st.write("Usá la barra lateral para navegar.")


if not st.session_state.logged_in:
    if not st.session_state.show_register:
        st.title("Iniciar sesión")
        with st.form("login_form"):
            dni = st.text_input("DNI")
            password = st.text_input("Contraseña", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                paciente = get_paciente(dni)
                if not paciente.empty and paciente.iloc[0]['contraseña'] == password:
                    st.session_state.logged_in = True
                    st.session_state.dni = dni
                    st.session_state.nombre = paciente.iloc[0]['nombre']
                    st.success("¡Inicio de sesión exitoso!")
                else:
                    st.error("Usuario o contraseña incorrectos.")
            else:
                st.error("Por favor completá todos los campos.")

        if st.button("¿No tenés cuenta? Registrate"):
            st.session_state.show_register = True
    else:
        st.title("Registro")
        with st.form("register_form"):
            new_name = st.text_input("Nombre")
            new_lastname = st.text_input("Apellido")
            new_DNI = st.text_input("DNI")
            main_email = st.text_input("Correo electrónico")
            new_password = st.text_input("Contraseña", type="password")
            confirm_password = st.text_input("Confirmar contraseña", type="password")
            fecha_nacimiento = st.date_input("Fecha de nacimiento")
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
            register = st.form_submit_button("Registrarme")


            if register:
                if new_password == confirm_password and new_DNI:
                    st.session_state.logged_in = True
                    st.session_state.dni = new_DNI
                    st.session_state.nombre = new_name
                    st.success("¡Registro exitoso!")
                    st.session_state.show_register = False
                    insert_paciente(new_name, fecha_nacimiento, sexo, new_password, int(new_DNI))
                else:
                    st.error("Las contraseñas no coinciden o faltan campos.")

        if st.button("¿Ya tenés cuenta? Iniciar sesión"):
            st.session_state.show_register = False
else:
    # --- Botones de navegación ---
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        if st.button("👤 Ir a mi Perfil"):
            st.switch_page("pages/Perfil.py")  # Asegurate de que exista esa página

    with col2:
        if st.button("📅 Ver Calendario"):
            st.switch_page("pages/Calendario.py")  # Asegurate de que exista esa página

    with col3:
        if st.button("🏥 Ver mi historial"):
            st.switch_page("pages/datos.py")  # Asegurate de que exista esa página

    with col4:
        if st.button("💊 Ver mis medicamentos"):
            st.switch_page("pages/medicamentos.py")  # Asegurate de que exista esa página

# --- Opción para cerrar sesión ---
    st.markdown("---")
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.pop("dni", None)
        st.success("Sesión cerrada. Volvé a la página principal.")
        st.switch_page("Inicio.py") # Asegurate que sea la página de inicio/login