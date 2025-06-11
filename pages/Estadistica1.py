# -----------------------------------------------------------------------------
# CÓDIGO COMPLETO Y UNIFICADO PARA LA PESTAÑA DE ESTADÍSTICAS (statistics_tab.py)
# -----------------------------------------------------------------------------
# Este archivo contiene toda la lógica para:
# 1. Leer los datos del usuario que ha iniciado sesión (usando st.session_state).
# 2. Ofrecer un selector de perfiles si el usuario es cuidador de familiares.
# 3. Comparar el perfil seleccionado con datos de referencia de enfermedades.
# 4. Mostrar los resultados en gráficos interactivos y tablas.
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date

# --- IMPORTANTE ---
# Asegúrate de que estas funciones de tus otros archivos estén disponibles y correctamente importadas.
from functions import execute_query, connect_to_supabase
from fEncuesta import get_id_paciente_por_dni, tiene_antecedente_enfermedad_por_dni, obtener_edad

# Se asume que tienes una función similar para obtener la edad a partir del ID.





# Si no, tendrás que ajustar esta parte.
def obtener_edad_por_dni():
    """
    Obtiene la edad de un paciente a partir de su ID.
    Esta es una función de ejemplo, adáptala a tu implementación real.
    """
    dni = st.session_state.get("dni")
    try:
        query = "SELECT fecha_nacimiento FROM pacientes WHERE dni = %s"
        df = execute_query(query, params=(dni,), is_select=True)
        if not df.empty:
            fecha_nacimiento = df.iloc[0]['fecha_nacimiento']
            if isinstance(fecha_nacimiento, date):
                hoy = date.today()
                return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
    except Exception as e:
        st.error(f"No se pudo calcular la edad: {e}")
    return None

# -----------------------------------------------------------------------------
# SECCIÓN 1: FUNCIONES DE CARGA Y PROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------

def load_medical_profiles():
    """Cargar perfiles médicos de referencia desde la base de datos."""
    try:
        query = "SELECT * FROM perfiles_medicos"
        df = execute_query(query, is_select=True)
        return df
    except Exception as e:
        st.error(f"Error cargando perfiles médicos de referencia: {e}")
        return pd.DataFrame()

def load_user_medical_data(id_paciente):
    """
    Carga el historial y los datos del paciente en una sola consulta
    uniendo las tablas 'pacientes' e 'historial_medico'.
    """
    try:
        query = """
        SELECT 
            p.*, 
            hm.*
        FROM pacientes p
        LEFT JOIN historial_medico hm ON p.id_paciente = hm.id_paciente
        WHERE p.id_paciente = %s
        ORDER BY hm.fecha_completado DESC
        LIMIT 1;
        """
        df = execute_query(query, params=(id_paciente,), is_select=True)
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error cargando el historial médico del usuario: {e}")
        return None

def calculate_imc(peso, altura):
    """
    Calcula el IMC.
    ADVERTENCIA: La columna 'altura' no existe en tu esquema de BD actual.
    Para que esto funcione, debes añadir una columna 'altura' a tu tabla 'pacientes'.
    """
    if peso and altura and altura > 0:
        altura_m = altura / 100 if altura > 3 else altura
        if altura_m > 0:
            return peso / (altura_m ** 2)
    return None

def map_user_profile_to_comparison():
    """
    Mapear datos del historial médico del usuario al formato de comparación
    
    IMPORTANTE: Ajusta los nombres de campos según tu tabla historial_medico real
    Este es un mapeo de ejemplo - necesitas cambiarlo según tus campos
    """
    dni = st.session_state.get("dni")
    id_paciente = get_id_paciente_por_dni(dni)
    conn = connect_to_supabase
    user_data= load_user_medical_data(id_paciente)
    # Ejemplo de mapeo - CAMBIA estos nombres por los de tu tabla real
    mapped_profile = {
        'edad': obtener_edad_por_dni(),
        
        # Hábitos de vida - ajusta según tus campos
        'actividad_fisica': user_data.get('actividad_fisica'),
        'fumador': user_data.get('fumador'),
        'alcohol_frecuente': user_data.get('consume_alcohol') or user_data.get('alcohol_frecuente') or user_data.get('bebe_alcohol'),
        
        # Antecedentes familiares - ajusta según tus campos
        'antecedentes_familiares_cancer': tiene_antecedente_enfermedad_por_dni(dni, 'cancer', conn=conn),
        'antecedentes_familiares_diabetes': tiene_antecedente_enfermedad_por_dni(dni, 'diabetes', conn=conn),
        'antecedentes_familiares_hipertension': tiene_antecedente_enfermedad_por_dni(dni, 'hipertension', conn=conn),
        # Métricas físicas
        #'imc': user_data.get('imc') or calculate_imc(user_data.get('peso'), user_data.get('altura')),
        
        # Condiciones actuales - ajusta según tus campos
        'presion_arterial_alta': user_data.get('presion_alta') or user_data.get('presion_arterial_alta') or user_data.get('hipertension'),
        'colesterol_alto': user_data.get('colesterol_alto') or user_data.get('colesterol_elevado'),
        'estres_alto': user_data.get('nivel_estres') == 'Alto' if user_data.get('nivel_estres') else user_data.get('estres_alto')
    }
    
    return mapped_profile

def calculate_similarity(user_profile, disease_profiles):
    """Calcula la similitud entre el perfil del usuario y un grupo de perfiles de enfermedad."""
    similarities = []
    characteristics = [
        'actividad_fisica', 'fumador', 'alcohol_frecuente',
        'antecedentes_familiares_cancer', 'antecedentes_familiares_diabetes',
        'antecedentes_familiares_hipertension',
        'colesterol_alto', 'estres_alto', 'presion_arterial_alta'
    ]
    
    for _, profile in disease_profiles.iterrows():
        matches = 0
        total_characteristics = 0
        
        for char in characteristics:
            if user_profile.get(char) is not None:
                total_characteristics += 1
                if user_profile.get(char) == profile[char]:
                    matches += 1
        
        if user_profile.get('edad') and not pd.isna(profile['edad']):
            total_characteristics += 1
            if abs(user_profile['edad'] - profile['edad']) <= 10:
                matches += 1
        
        #if user_profile.get('imc') and not pd.isna(profile['imc']):
            #total_characteristics += 1
            #if abs(user_profile['imc'] - profile['imc']) <= 3:
                #matches += 1
        
        if total_characteristics > 0:
            similarity_percentage = (matches / total_characteristics) * 100
            similarities.append(similarity_percentage)
    
    return np.mean(similarities) if similarities else 0

# -----------------------------------------------------------------------------
# SECCIÓN 2: FUNCIONES DE VISUALIZACIÓN
# -----------------------------------------------------------------------------

def create_risk_gauge(percentage, disease_name):
    """Crea un gráfico de medidor (gauge) para mostrar un porcentaje de similitud."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Similitud con {disease_name}", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E3B4E"},
            'steps': [
                {'range': [0, 40], 'color': "lightgreen"},
                {'range': [40, 70], 'color': "yellow"},
                {'range': [70, 100], 'color': "red"}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# -----------------------------------------------------------------------------
# SECCIÓN 3: FUNCIÓN PRINCIPAL DE LA PÁGINA DE STREAMLIT
# -----------------------------------------------------------------------------

def show_statistics_tab():
    """
    Muestra la pestaña de estadísticas completa. Funciona para el usuario logueado
    y permite cambiar a perfiles familiares si es un cuidador.
    """
    conn = connect_to_supabase() 

    # 1. Verificar que el usuario haya iniciado sesión
    if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
        st.warning("🔒 Por favor, inicia sesión para ver tu análisis de riesgo personalizado.")
        st.info("Puedes iniciar sesión desde la página principal.")
        return

    # 2. Obtener el DNI y verificar que exista en la sesión
    dni = st.session_state.get("dni")
    if not dni:
        st.error("🚨 No se pudo obtener la información del usuario. Por favor, intenta iniciar sesión de nuevo.")
        return

    # 3. Consultar la base de datos de forma segura
    try:
        query = "SELECT nombre FROM pacientes WHERE dni = %s"
        # Usamos [dni] para pasar los parámetros como una lista
        paciente_info = execute_query(query, [dni], conn=conn, is_select=True)
        
        # Valor por defecto en caso de no encontrar al paciente
        nombre_paciente_actual = "Usuario" 

        if not paciente_info.empty:
            # Si se encuentra, se actualiza el nombre
            nombre_paciente_actual = paciente_info.iloc[0]['nombre']
        else:
            # Manejamos el caso en que el DNI no está en la tabla de pacientes
            st.warning(f"No se encontró un perfil de paciente para el DNI {dni}.")
            return
    except Exception as e:
        st.error(f"Ocurrió un error al cargar tus datos: {e}")
        return

    st.header(f"📊 Análisis de Riesgo para {nombre_paciente_actual}")
    st.write("Compara tu perfil médico con perfiles de referencia para identificar posibles factores de riesgo.")

    df_ref = load_medical_profiles()
    if df_ref.empty:
        st.error("No se pudieron cargar los datos de referencia. Intenta más tarde.")
        return
        

    if st.button("🔍 Analizar Riesgo", type="primary", use_container_width=True):
        id_paciente = get_id_paciente_por_dni(dni)
        user_medical_data = load_user_medical_data(id_paciente)
        user_profile = map_user_profile_to_comparison(user_medical_data)
        
        with st.expander("Ver perfil de usuario mapeado (para depuración)"):
            st.json(user_profile)

        non_null_values = sum(1 for v in user_profile.values() if v is not None and v != '')
        if non_null_values < 5:
            st.warning("⚠️ El perfil del usuario tiene información limitada. Los resultados pueden no ser precisos.")
        
        st.subheader("📈 Resultados del Análisis")
        diseases = df_ref['enfermedad'].unique()
        diseases = [d for d in diseases if d != 'Saludable']
        
        results = []
        for disease in diseases:
            disease_profiles = df_ref[df_ref['enfermedad'] == disease]
            similarity = calculate_similarity(user_profile, disease_profiles)
            results.append({'enfermedad': disease, 'similitud': similarity})
        
        if not results:
            st.info("No se pudo calcular la similitud para ninguna enfermedad.")
            return

        results = sorted(results, key=lambda x: x['similitud'], reverse=True)
        
        cols = st.columns(min(3, len(results)))
        for i, result in enumerate(results[:3]):
            with cols[i]:
                fig = create_risk_gauge(result['similitud'], result['enfermedad'])
                st.plotly_chart(fig, use_container_width=True)
                sim_value = result['similitud']
                if sim_value >= 70:
                    st.error(f"**Alta Similitud ({sim_value:.0f}%)**")
                elif sim_value >= 40:
                    st.warning(f"**Similitud Moderada ({sim_value:.0f}%)**")
                else:
                    st.success(f"**Baja Similitud ({sim_value:.0f}%)**")

        st.info("""
        **Descargo de responsabilidad:** Este análisis es una herramienta educativa basada en similitudes estadísticas, no un diagnóstico. 
        Consulta siempre a un profesional de la salud para cualquier decisión médica.
        """)


def main():
    st.set_page_config(
        page_title="MedCheck - Estadísticas",
        page_icon="📊",
        layout="wide"
    )
    
    show_statistics_tab()

if __name__ == "__main__":
    main()

# Dentro de la función show_statistics_tab

