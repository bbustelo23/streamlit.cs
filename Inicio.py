import streamlit as st
from datetime import date, datetime
# Se asume que estas funciones existen y funcionan correctamente en fEncuesta.py
from fEncuesta import get_paciente, insert_paciente
from functions import connect_to_supabase

# --- Page Configuration MUST BE THE FIRST STREAMLIT COMMAND ---
st.set_page_config(
    page_title="Inicio - MedCheck",
    page_icon="⚕️",
    layout="wide"
)

# --- Custom CSS for a new elegant look ---
st.markdown("""
    <style>
        /* --- Estilos Generales --- */
        .main-title {
            color: #800020;
            font-size: 2.8em;
            font-weight: bold;
            text-align: center;
            padding-top: 2rem;
        }
        .subtitle {
            text-align: center;
            color: #555;
            margin-bottom: 2rem;
        }
        .medcheck-text {
            color: #800020;
            font-weight: bold;
        }

        /* --- Layout de Inicio de Sesión / Registro (Centrado) --- */
        .form-container {
            max-width: 480px;
            margin: 2rem auto;
            padding: 2.5rem;
            background: #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.1);
            border: 1px solid #E0E0E0;
        }
        
        .form-container .stButton>button {
            background-color: #800020 !important;
            color: white !important;
            width: 100%;
            border-radius: 8px;
            padding: 12px 0;
            font-weight: bold;
            border: none;
        }
        .form-container .stButton>button:hover {
            background-color: #600010 !important;
        }
        .toggle-link {
            text-align: center;
            margin-top: 1.5rem;
        }

        /* --- Layout del Panel de Control (Logueado) --- */
        .dashboard-header {
            background: #800020; /* CAMBIO: Fondo bordó */
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            margin-bottom: 2rem;
        }
        .dashboard-header .header-title .medcheck-text {
            color: #FFFFFF; /* CAMBIO: Letra de MedCheck a blanco */
        }
        .dashboard-header .header-title {
            font-size: 3.5em;
            font-weight: bold;
            margin: 0;
        }
        .dashboard-header .welcome-subtitle {
            font-size: 1.2em;
            color: #FBE9E7; /* CAMBIO: Letra del subtítulo a blanco suave */
            margin-top: 0.5rem;
        }

        .dashboard-grid {
            padding: 1rem 0;
        }
        .nav-card {
            background-color: #FFFFFF;
            border: 1px solid #E9ECEF;
            border-top: 4px solid #800020; /* Acento de color bordó */
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            transition: all 0.3s ease;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .nav-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.12);
            border-top-color: #600010;
        }
        .nav-card .icon {
            font-size: 4rem;
            color: #800020; /* Icono en color bordó */
            line-height: 1;
        }
        .nav-card h3 {
            color: #343A40; /* Texto oscuro para el título */
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            font-size: 1.5em;
        }
        .nav-card p {
            color: #6C757D; /* Gris suave para la descripción */
            font-size: 1em;
            flex-grow: 1;
            padding-bottom: 1rem;
        }
        
        .nav-card .stButton>button {
            background-color: #800020 !important;
            color: white !important;
            border: none !important;
        }
        .nav-card .stButton>button:hover {
            background-color: #600010 !important;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Conexión a la Base de Datos ---
conn = connect_to_supabase()

# --- Inicialización del Estado de Sesión ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False
if "nombre" not in st.session_state:
    st.session_state.nombre = "Usuario"
if "dni" not in st.session_state:
    st.session_state.dni = None

# --- Lógica Principal de la Aplicación ---

# --- VISTA DE USUARIO LOGUEADO ---
if st.session_state.logged_in:
    # --- NUEVO ENCABEZADO DE BIENVENIDA ---
    st.markdown(f"""
        <div class="dashboard-header">
            <h1 class="header-title"><span class="medcheck-text">MedCheck</span></h1>
            <p class="welcome-subtitle">¡Hola, {st.session_state.nombre}! Bienvenido a tu panel de control.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="dashboard-grid">', unsafe_allow_html=True)
    
    card_info = [
        {"icon": "👤", "title": "Mi Perfil", "desc": "Genera informes médicos para consultas o emergencias.", "page": "pages/Perfil.py", "key": "perfil"},
        {"icon": "📅", "title": "Calendario", "desc": "Administra y visualiza tus próximos turnos médicos.", "page": "pages/Calendario.py", "key": "calendario"},
        {"icon": "🏥", "title": "Historial Clínico", "desc": "Consulta tus eventos y estudios médicos pasados.", "page": "pages/Historial.py", "key": "historial"},
        {"icon": "💊", "title": "Medicamentos", "desc": "Lleva un control de tus tratamientos y dosis actuales.", "page": "pages/Medicamentos.py", "key": "medicamentos"}
    ]

    # Crear una cuadrícula 2x2
    row1_cols = st.columns(2)
    row2_cols = st.columns(2)
    
    all_cols = row1_cols + row2_cols

    for i, card in enumerate(card_info):
        with all_cols[i]:
            st.markdown('<div class="nav-card">', unsafe_allow_html=True)
            st.markdown(f'<div><div class="icon">{card["icon"]}</div><h3>{card["title"]}</h3><p>{card["desc"]}</p></div>', unsafe_allow_html=True)
            if st.button(f"Acceder", key=card["key"]):
                st.switch_page(card["page"])
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("Cerrar Sesión"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# --- VISTA DE USUARIO NO LOGUEADO ---
else:
    st.markdown('<h1 class="main-title">⚕️ Bienvenido a <span class="medcheck-text">MedCheck</span></h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tu asistente de salud personal. Inicia sesión o regístrate para continuar.</p>', unsafe_allow_html=True)

    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    # --- Formulario de Registro ---
    if st.session_state.show_register:
        st.subheader("Crear una cuenta nueva")
        with st.form("register_form", border=False):
            new_name = st.text_input("Nombre", key="reg_name")
            new_lastname = st.text_input("Apellido", key="reg_lastname")
            new_DNI = st.text_input("DNI", key="reg_dni")
            main_email = st.text_input("Correo electrónico", key="reg_email")
            new_password = st.text_input("Contraseña", type="password", key="reg_pass")
            confirm_password = st.text_input("Confirmar contraseña", type="password", key="reg_confirmpass")
            fecha_nacimiento = st.date_input("Fecha de nacimiento", min_value=date(1920, 1, 1), max_value=datetime.today().date(), key="reg_birth")
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino", "Prefiero no decirlo"], key="reg_sex")
            
            if st.form_submit_button("Registrarme"):
                if new_password == confirm_password and all([new_name, new_lastname, new_DNI, main_email]):
                    insert_paciente(
                        dni=int(new_DNI), nombre=new_name, apellido=new_lastname, email=main_email, 
                        fecha_nacimiento=fecha_nacimiento, sexo=sexo, contraseña=new_password, 
                        encuesta_completada=False
                    )
                    st.session_state.logged_in = True
                    st.session_state.dni = new_DNI
                    st.session_state.nombre = new_name
                    st.session_state.apellido = new_lastname
                    st.success("¡Registro exitoso! Bienvenido.")
                    st.rerun()
                else:
                    st.error("Las contraseñas no coinciden o faltan campos obligatorios.")
        
        st.markdown('<div class="toggle-link">', unsafe_allow_html=True)
        if st.button("¿Ya tienes cuenta? Iniciar sesión", key="toggle_to_login"):
            st.session_state.show_register = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Formulario de Login ---
    else:
        st.subheader("Iniciar Sesión")
        with st.form("login_form", border=False):
            dni = st.text_input("DNI", key="login_dni")
            password = st.text_input("Contraseña", type="password", key="login_pass")
            
            if st.form_submit_button("Ingresar"):
                if dni and password:
                    paciente = get_paciente(dni)
                    if not paciente.empty and paciente.iloc[0]['contraseña'] == password:
                        st.session_state.logged_in = True
                        st.session_state.dni = dni
                        st.session_state.nombre = paciente.iloc[0]['nombre']
                        st.success("¡Inicio de sesión exitoso!")
                        st.rerun()
                    else:
                        st.error("DNI o contraseña incorrectos.")
                else:
                    st.warning("Por favor, completa todos los campos.")
        
        st.markdown('<div class="toggle-link">', unsafe_allow_html=True)
        if st.button("¿No tienes cuenta? Regístrate", key="toggle_to_register"):
            st.session_state.show_register = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True) # Cierre de form-container