import streamlit as st
from datetime import datetime, date
import base64 # Necesario para la imagen del logo

# --- Se asume que estas funciones existen y funcionan correctamente ---
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase, execute_query

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Perfil - MedCheck", 
    page_icon="👤", 
    layout="centered"
)

# --- Estilos CSS para la página principal ---
st.markdown("""
    <style>
        .stButton>button {
            background-color: #800020 !important;
            color: white !important;
        }
        .stButton>button:hover {
            background-color: #600010 !important;
        }
        /* Estilo para el botón de descarga para que parezca el principal */
        .stDownloadButton>button {
            background-color: #800020 !important;
            color: white !important;
            width: 100%;
        }
        .stDownloadButton>button:hover {
            background-color: #600010 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)


# --- Logo de MedCheck (Opcional, pero mejora el diseño) ---
try:
    with open("assets/logo.png", "rb") as f:
        logo_base64 = base64.b64encode(f.read()).decode()
except FileNotFoundError:
    logo_base64 = ""


# --- Funciones de Ayuda y Obtención de Datos ---

def calculate_age(born_date_str):
    if not born_date_str or not isinstance(born_date_str, str): return "N/A"
    try:
        born = datetime.strptime(born_date_str, '%Y-%m-%d').date()
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    except (ValueError, TypeError):
        return "N/A"

def get_datos_paciente(dni, conn):
    try:
        main_query = """
            SELECT p.id_paciente, p.nombre, p.apellido, p.dni, p.fecha_nacimiento,
                   p.tipo_sangre, p.sexo, p.telefono, p.email, h.alergias, h.condicion
            FROM pacientes AS p
            LEFT JOIN historial_medico AS h ON p.id_paciente = h.id_paciente
            WHERE p.dni = %s;
        """
        df_paciente = execute_query(main_query, params=(dni,), conn=conn, is_select=True)
        
        if df_paciente.empty: return None
        paciente_info = df_paciente.iloc[0].to_dict()
        id_paciente = int(paciente_info['id_paciente'])

        meds_query = "SELECT nombre, dosis_cantidad, dosis_unidad FROM medicamentos WHERE id_paciente = %s AND (fecha_fin IS NULL OR fecha_fin > CURRENT_DATE);"
        df_medicamentos = execute_query(meds_query, params=(id_paciente,), conn=conn, is_select=True)
        
        medicamentos_formateados = []
        if not df_medicamentos.empty:
            for _, med in df_medicamentos.iterrows():
                medicamentos_formateados.append(f"{med.get('nombre', 'N/A')} ({med.get('dosis_cantidad', '')} {med.get('dosis_unidad', '')})")

        estudio_query = "SELECT tipo, fecha, descripcion FROM estudios WHERE id_paciente = %s ORDER BY fecha DESC;"
        df_estudios = execute_query(estudio_query, params=(id_paciente,), conn=conn, is_select=True)
        
        estudios_formateados = []
        if not df_estudios.empty:
            for _, estudio in df_estudios.iterrows():
                fecha_estudio = estudio.get('fecha').strftime('%d/%m/%Y') if estudio.get('fecha') else 'Sin fecha'
                estudios_formateados.append(f"({fecha_estudio}) {estudio.get('tipo', 'Estudio')}: {estudio.get('descripcion', 'Sin descripción.')}")

        alergias_str = paciente_info.get('alergias', '')
        alergias_list = [a.strip() for a in alergias_str.split(',')] if alergias_str and alergias_str.strip() else []
        
        antecedentes_str = paciente_info.get('condicion', '')
        antecedentes_list = [a.strip() for a in antecedentes_str.split(',')] if antecedentes_str and antecedentes_str.strip() else []

        return {
            "nombre": f"{paciente_info.get('nombre', '')} {paciente_info.get('apellido', '')}",
            "dni": paciente_info.get('dni', ''),
            "edad": calculate_age(str(paciente_info.get('fecha_nacimiento', ''))),
            "telefono": paciente_info.get('telefono', 'No especificado'),
            "email": paciente_info.get('email', 'No especificado'),
            "tipo_sangre": paciente_info.get('tipo_sangre', 'No especificado'),
            "alergias": alergias_list,
            "medicacion": medicamentos_formateados,
            "antecedentes": antecedentes_list,
            "vacunas": [],
            "estudios": estudios_formateados,
        }
    except Exception as e:
        st.error(f"Ocurrió un error al consultar la base de datos: {e}")
        return None

# --- CSS COMPARTIDO PARA TODOS LOS INFORMES ---
CSS_INFORME = """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    body {
        font-family: 'Inter', sans-serif; margin: 0; padding: 0;
        background-color: #f8f9fa; color: #343a40;
        -webkit-print-color-adjust: exact;
    }
    .container { max-width: 850px; margin: 20px auto; background: #ffffff; border-radius: 12px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); overflow: hidden; }
    .header { background: #800020; color: white; padding: 25px 30px; display: flex; align-items: center; justify-content: space-between; }
    .header.guardia { background: #D9534F; } /* Color especial para guardia */
    .header img { height: 50px; filter: brightness(0) invert(1); }
    .header-text h1 { margin: 0; font-size: 28px; font-weight: 700; }
    .header-text p { margin: 5px 0 0; font-size: 14px; opacity: 0.9; }
    .content { padding: 30px; }
    .patient-info h2 { font-size: 22px; color: #800020; border-bottom: 2px solid #f1f3f5; padding-bottom: 10px; margin-bottom: 20px; }
    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
    .info-item { background: #f8f9fa; padding: 12px 15px; border-radius: 8px; font-size: 15px; }
    .info-item strong { color: #495057; margin-right: 8px; }
    .section-card { background: #ffffff; border: 1px solid #e9ecef; border-radius: 10px; padding: 20px; margin-top: 20px; }
    .section-card.alergia { border-left: 5px solid #D9534F; } /* Borde especial para alergias */
    .section-card h3 { font-size: 18px; color: #800020; margin-top: 0; margin-bottom: 15px; display: flex; align-items: center; }
    .section-card .icon { margin-right: 10px; font-size: 22px; }
    .list-container { display: flex; flex-direction: column; gap: 8px; }
    .list-item { padding: 10px; background: #f8f9fa; border-radius: 6px; }
    .list-item-empty { padding: 10px; background: #f8f9fa; border-radius: 6px; color: #6c757d; font-style: italic; }
    .footer { text-align: center; margin-top: 30px; padding: 20px 30px; background: #f8f9fa; font-size: 12px; color: #6c757d; }
"""

# --- FUNCIÓN DE HTML PARA INFORME DE GUARDIA (DISEÑO ACTUALIZADO) ---
def generar_html_guardia_agil(datos):
    def render_section_guardia(title, data_list, icon, card_class=""):
        items_html = "".join(f'<div class="list-item">{item}</div>' for item in data_list) if data_list else '<div class="list-item-empty">No se registran datos.</div>'
        return f"""
            <div class="section-card {card_class}">
                <h3><span class="icon">{icon}</span> {title}</h3>
                <div class="list-container">{items_html}</div>
            </div>
        """
    
    html_body = f"""
        <div class="container">
            <div class="header guardia">
                <div class="header-text"><h1>🚑 Informe de Guardia Ágil</h1><p>Información crítica para emergencias</p></div>
                {'<img src="data:image/png;base64,{logo_base64}" alt="Logo">' if logo_base64 else ''}
            </div>
            <div class="content">
                <div class="patient-info">
                    <h2>👤 Información del Paciente</h2>
                    <div class="info-grid">
                        <div class="info-item"><strong>Nombre:</strong> {datos['nombre']}</div>
                        <div class="info-item"><strong>Edad:</strong> {datos['edad']} años</div>
                        <div class="info-item"><strong>DNI:</strong> {datos['dni']}</div>
                        <div class="info-item"><strong>Tipo Sanguíneo:</strong> {datos['tipo_sangre']}</div>
                    </div>
                </div>
                {render_section_guardia("Alergias Críticas", datos['alergias'], "🚨", "alergia")}
                {render_section_guardia("Medicación Actual", datos['medicacion'], "💊")}
            </div>
            <div class="footer">Generado por MedCheck el {date.today().strftime('%d/%m/%Y')}.</div>
        </div>
    """
    return f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Informe de Guardia - {datos["nombre"]}</title><style>{CSS_INFORME}</style></head><body>{html_body}</body></html>'


# --- FUNCIÓN DE HTML PARA INFORME COMPLETO Y PERSONALIZADO ---
def generar_html_completo(datos, config):
    def render_section(title, data_list, icon, show=True):
        if not show: return ""
        items_html = "".join(f'<div class="list-item">{item}</div>' for item in data_list) if data_list else '<div class="list-item-empty">Ningún dato registrado para esta sección.</div>'
        return f"""
            <div class="section-card">
                <h3><span class="icon">{icon}</span> {title}</h3>
                <div class="list-container">{items_html}</div>
            </div>
        """

    html_body = f"""
        <div class="container">
            <div class="header">
                <div class="header-text"><h1>Informe Médico</h1><p>Generado por MedCheck el {date.today().strftime('%d/%m/%Y')}</p></div>
                {'<img src="data:image/png;base64,{logo_base64}" alt="Logo">' if logo_base64 else ''}
            </div>
            <div class="content">
                <div class="patient-info">
                    <h2>👤 Información del Paciente</h2>
                    <div class="info-grid">
                        <div class="info-item"><strong>Nombre:</strong> {datos['nombre']}</div>
                        <div class="info-item"><strong>Edad:</strong> {datos['edad']} años</div>
                        <div class="info-item"><strong>DNI:</strong> {datos['dni']}</div>
                        <div class="info-item"><strong>Tipo Sanguíneo:</strong> {datos['tipo_sangre']}</div>
                        <div class="info-item"><strong>Teléfono:</strong> {datos['telefono']}</div>
                        <div class="info-item"><strong>Email:</strong> {datos['email']}</div>
                    </div>
                </div>
                {render_section("Alergias", datos['alergias'], "🚨", config.get('alergias', True))}
                {render_section("Medicación Actual", datos['medicacion'], "💊", config.get('medicacion', True))}
                {render_section("Antecedentes Médicos", datos['antecedentes'], "📜", config.get('antecedentes', True))}
                {render_section("Vacunas", datos['vacunas'], "💉", config.get('vacunas', True))}
                {render_section("Estudios Previos", datos['estudios'], "🔬", config.get('estudios', True))}
            </div>
            <div class="footer">Este es un informe confidencial. Verifique siempre la información con un profesional de la salud.</div>
        </div>
    """
    return f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Informe Médico - {datos["nombre"]}</title><style>{CSS_INFORME}</style></head><body>{html_body}</body></html>'


# --- INICIO DE LA APLICACIÓN STREAMLIT ---

conn = connect_to_supabase()
dni = st.session_state.get("dni")

if not dni:
    st.error("⚠️ No has iniciado sesión. Por favor, vuelve a la página de inicio.")
    st.stop()

encuesta_df = get_encuesta_completada(dni, conn=conn)
if not encuesta_df.empty and not encuesta_df.iloc[0]["encuesta_completada"]:
    st.warning("**Antes de continuar, necesitamos más información.**")
    if st.button("📝 Completar Encuesta Médica", type="primary"):
        st.switch_page("pages/_Encuesta.py")
    st.stop()

st.title(f"👋 ¡Hola, {st.session_state.get('nombre', 'Usuario')}!")
st.write("Bienvenido a tu perfil médico. Desde aquí puedes generar informes para tus consultas o emergencias.")
st.divider()

st.header("📄 Generar Informe Médico")
st.write("Crea un informe personalizado según tus necesidades del momento.")

tipo_informe = st.selectbox(
    "Selecciona el tipo de informe que necesitas",
    options=["", "guardia_agil", "historial_completo", "personalizado"],
    format_func=lambda x: {
        "": "Selecciona una opción...",
        "guardia_agil": "🚑 Guardia Ágil - Para emergencias",
        "historial_completo": "📋 Historial Completo - Para consultas",
        "personalizado": "⚙️ Personalizado - Elige qué incluir"
    }[x],
    label_visibility="collapsed"
)

incluir_alergias = incluir_medicacion = incluir_antecedentes = True
incluir_vacunas = incluir_estudios = True

if tipo_informe == "personalizado":
    with st.container(border=True):
        st.subheader("⚙️ Configuración de Informe Personalizado")
        col1, col2 = st.columns(2)
        with col1:
            incluir_alergias = st.checkbox("🚨 Incluir Alergias", value=True)
            incluir_medicacion = st.checkbox("💊 Incluir Medicación Actual", value=True)
            incluir_antecedentes = st.checkbox("📜 Incluir Antecedentes")
        with col2:
            incluir_vacunas = st.checkbox("💉 Incluir Vacunas")
            incluir_estudios = st.checkbox("🔬 Incluir Estudios Previos")

# --- LÓGICA DE DESCARGA DIRECTA (MODIFICADA) ---
if tipo_informe:
    # Preparamos los datos para el botón de descarga
    with st.spinner("Preparando datos para la descarga..."):
        datos_paciente = get_datos_paciente(dni, conn)
    
    if datos_paciente:
        html_informe = ""
        if tipo_informe == "guardia_agil":
            html_informe = generar_html_guardia_agil(datos_paciente)
        
        elif tipo_informe == "historial_completo":
            config_completo = {k: True for k in ['alergias', 'medicacion', 'antecedentes', 'vacunas', 'estudios']}
            html_informe = generar_html_completo(datos_paciente, config_completo)
        
        elif tipo_informe == "personalizado":
            config_personalizado = {
                'alergias': incluir_alergias,
                'medicacion': incluir_medicacion,
                'antecedentes': incluir_antecedentes,
                'vacunas': incluir_vacunas,
                'estudios': incluir_estudios,
            }
            html_informe = generar_html_completo(datos_paciente, config_personalizado)
        
        # El botón de descarga ahora es la acción principal
        st.download_button(
            label="⬇️ Descargar Informe",
            data=html_informe,
            file_name=f"informe_{tipo_informe}_{dni}.html",
            mime="text/html",
            use_container_width=True,
            type="primary" # Hace que el botón se vea como el principal
        )
    else:
        st.error("No se pudieron obtener los datos para generar el informe.")
