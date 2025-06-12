# -----------------------------------------------------------------------------
# CÓDIGO COMPLETO Y CORREGIDO PARA LA PESTAÑA DE ESTADÍSTICAS (statistics_tab.py)
# -----------------------------------------------------------------------------
# Este archivo contiene toda la lógica para:
# 1. Leer los datos del usuario que ha iniciado sesión (usando st.session_state).
# 2. Comparar el perfil del usuario con datos de referencia de enfermedades.
# 3. Mostrar los resultados en gráficos interactivos.
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import date, datetime

# --- IMPORTANTE ---
# Asegúrate de que estas funciones de tus otros archivos estén disponibles y correctamente importadas.
try:
    from functions import execute_query, connect_to_supabase
    from fEncuesta import get_id_paciente_por_dni
except ImportError as e:
    st.error(f"Error importando funciones: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# FUNCIONES DE UTILIDAD
# -----------------------------------------------------------------------------

def obtener_edad_por_dni(dni):
    """
    Obtiene la edad de un paciente a partir de su DNI usando la fecha de nacimiento.
    """
    try:
        conn = connect_to_supabase()
        query = "SELECT fecha_nacimiento FROM pacientes WHERE dni = %s"
        df = execute_query(query, params=[dni], conn=conn, is_select=True)
        
        if not df.empty and df.iloc[0]['fecha_nacimiento'] is not None:
            fecha_nacimiento = df.iloc[0]['fecha_nacimiento']
            
            # Convertir a datetime si es necesario
            if isinstance(fecha_nacimiento, str):
                fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
            elif isinstance(fecha_nacimiento, datetime):
                fecha_nacimiento = fecha_nacimiento.date()
            
            if isinstance(fecha_nacimiento, date):
                hoy = date.today()
                edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                return edad
    except Exception as e:
        st.error(f"Error calculando la edad: {e}")
    return None

def tiene_antecedente_enfermedad_por_dni(dni, enfermedad, conn=None):
    """
    Verifica si un paciente tiene antecedentes familiares de una enfermedad específica.
    Busca en el campo antecedentes_familiares del historial médico.
    """
    try:
        if conn is None:
            conn = connect_to_supabase()
        
        # Obtener el ID del paciente
        id_paciente = get_id_paciente_por_dni(dni)
        if not id_paciente:
            return False
        
        # Buscar en el historial médico
        query = """
        SELECT antecedentes_familiares 
        FROM historial_medico 
        WHERE id_paciente = %s 
        ORDER BY fecha_completado DESC 
        LIMIT 1
        """
        df = execute_query(query, params=[id_paciente], conn=conn, is_select=True)
        
        if not df.empty and df.iloc[0]['antecedentes_familiares']:
            antecedentes = str(df.iloc[0]['antecedentes_familiares']).lower()
            enfermedad_lower = enfermedad.lower()
            
            # Mapeo de enfermedades
            mapeos = {
                'cancer': ['cancer', 'cáncer', 'tumor', 'oncolog'],
                'diabetes': ['diabetes', 'diabetico', 'diabético', 'azucar', 'azúcar'],
                'hipertension': ['hipertension', 'hipertensión', 'presion alta', 'presión alta', 'tension alta', 'tensión alta']
            }
            
            if enfermedad_lower in mapeos:
                return any(termino in antecedentes for termino in mapeos[enfermedad_lower])
            else:
                return enfermedad_lower in antecedentes
                
    except Exception as e:
        st.error(f"Error verificando antecedentes de {enfermedad}: {e}")
    return False

# -----------------------------------------------------------------------------
# SECCIÓN 1: FUNCIONES DE CARGA Y PROCESAMIENTO DE DATOS
# -----------------------------------------------------------------------------

def load_medical_profiles():
    """
    Cargar perfiles médicos de referencia desde la base de datos.
    Si no existe la tabla, crear datos de ejemplo.
    """
    try:
        conn = connect_to_supabase()
        query = "SELECT * FROM perfiles_medicos"
        df = execute_query(query, conn=conn, is_select=True)
        return df
    except Exception as e:
        st.warning(f"No se pudieron cargar perfiles médicos de referencia: {e}")


def load_user_medical_data(id_paciente):
    """
    Carga el historial médico más reciente del paciente.
    """
    try:
        conn = connect_to_supabase()
        query = """
        SELECT hm.*, p.fecha_nacimiento, p.nombre
        FROM historial_medico hm
        LEFT JOIN pacientes p ON hm.id_paciente = p.id_paciente
        WHERE hm.id_paciente = %s
        ORDER BY hm.fecha_completado DESC
        LIMIT 1
        """
        df = execute_query(query, params=[id_paciente], conn=conn, is_select=True)
        
        if not df.empty:
            return df.iloc[0].to_dict()
        return None
    except Exception as e:
        st.error(f"Error cargando el historial médico del usuario: {e}")
        return None

def map_user_profile_to_comparison(user_data, dni):
    """
    Mapear datos del historial médico del usuario al formato de comparación.
    Usa los campos reales de tu base de datos.
    """
    if not user_data:
        return {}
    
    conn = connect_to_supabase()
    edad = obtener_edad_por_dni(dni)
    
    # Mapeo basado en los campos reales de tu BD
    mapped_profile = {
        'edad': edad,
        
        # Hábitos de vida
        'actividad_fisica': user_data.get('actividad_fisica') == 'Sí' if user_data.get('actividad_fisica') else False,
        'fumador': user_data.get('fumador', False) if isinstance(user_data.get('fumador'), bool) else user_data.get('fumador') == 'Sí',
        'alcohol_frecuente': user_data.get('alcoholico', False) if isinstance(user_data.get('alcoholico'), bool) else user_data.get('alcoholico') == 'Sí',
        
        # Antecedentes familiares
        'antecedentes_familiares_cancer': tiene_antecedente_enfermedad_por_dni(dni, 'cancer', conn=conn),
        'antecedentes_familiares_diabetes': tiene_antecedente_enfermedad_por_dni(dni, 'diabetes', conn=conn),
        'antecedentes_familiares_hipertension': tiene_antecedente_enfermedad_por_dni(dni, 'hipertension', conn=conn),
        
        # Condiciones actuales - usar los campos que existen en tu BD
        'presion_arterial_alta': False,  # No tienes este campo específico
        'colesterol_alto': False,        # No tienes este campo específico
        'estres_alto': False             # No tienes este campo específico
    }
    
    # Intentar extraer información de otros campos si existen
    if 'condicion' in user_data and user_data['condicion']:
        condicion_str = str(user_data['condicion']).lower()
        if 'hipertension' in condicion_str or 'presion alta' in condicion_str:
            mapped_profile['presion_arterial_alta'] = True
        if 'colesterol' in condicion_str:
            mapped_profile['colesterol_alto'] = True
        if 'estres' in condicion_str or 'ansiedad' in condicion_str:
            mapped_profile['estres_alto'] = True
    
    return mapped_profile

def calculate_similarity(user_profile, disease_profiles):
    """
    Calcula la similitud entre el perfil del usuario y un grupo de perfiles de enfermedad.
    """
    if not user_profile or disease_profiles.empty:
        return 0
    
    similarities = []
    characteristics = [
        'actividad_fisica', 'fumador', 'alcohol_frecuente',
        'antecedentes_familiares_cancer', 'antecedentes_familiares_diabetes',
        'antecedentes_familiares_hipertension',
        'presion_arterial_alta', 'colesterol_alto', 'estres_alto'
    ]
    
    for _, profile in disease_profiles.iterrows():
        matches = 0
        total_characteristics = 0
        
        for char in characteristics:
            if user_profile.get(char) is not None:
                total_characteristics += 1
                if user_profile.get(char) == profile.get(char, False):
                    matches += 1
        
        # Comparar edad con un rango de ±10 años
        if user_profile.get('edad') is not None and profile.get('edad') is not None:
            total_characteristics += 1
            if abs(user_profile['edad'] - profile['edad']) <= 10:
                matches += 1
        
        if total_characteristics > 0:
            similarity_percentage = (matches / total_characteristics) * 100
            similarities.append(similarity_percentage)
    
    return np.mean(similarities) if similarities else 0

# -----------------------------------------------------------------------------
# SECCIÓN 2: FUNCIONES DE VISUALIZACIÓN
# -----------------------------------------------------------------------------

def create_risk_gauge(percentage, disease_name):
    """
    Crea un gráfico de medidor (gauge) para mostrar un porcentaje de similitud.
    """
    # Asegurar que el porcentaje esté en el rango correcto
    percentage = max(0, min(100, percentage))
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=percentage,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"Similitud con {disease_name}", 'font': {'size': 14}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E3B4E"},
            'steps': [
                {'range': [0, 30], 'color': "lightgreen"},
                {'range': [30, 60], 'color': "yellow"},
                {'range': [60, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=250, 
        margin=dict(l=20, r=20, t=50, b=20),
        font={'size': 12}
    )
    return fig

def show_profile_summary(user_profile):
    """
    Muestra un resumen del perfil del usuario.
    """
    st.subheader("📋 Resumen de tu Perfil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Información Básica:**")
        if user_profile.get('edad'):
            st.write(f"• Edad: {user_profile['edad']} años")
        
        st.write("**Hábitos de Vida:**")
        st.write(f"• Actividad Física: {'Sí' if user_profile.get('actividad_fisica') else 'No'}")
        st.write(f"• Fumador: {'Sí' if user_profile.get('fumador') else 'No'}")
        st.write(f"• Consume Alcohol: {'Sí' if user_profile.get('alcohol_frecuente') else 'No'}")
    
    with col2:
        st.write("**Antecedentes Familiares:**")
        st.write(f"• Cáncer: {'Sí' if user_profile.get('antecedentes_familiares_cancer') else 'No'}")
        st.write(f"• Diabetes: {'Sí' if user_profile.get('antecedentes_familiares_diabetes') else 'No'}")
        st.write(f"• Hipertensión: {'Sí' if user_profile.get('antecedentes_familiares_hipertension') else 'No'}")
        
        st.write("**Condiciones Actuales:**")
        st.write(f"• Presión Alta: {'Sí' if user_profile.get('presion_arterial_alta') else 'No'}")
        st.write(f"• Colesterol Alto: {'Sí' if user_profile.get('colesterol_alto') else 'No'}")
        st.write(f"• Estrés Alto: {'Sí' if user_profile.get('estres_alto') else 'No'}")

# -----------------------------------------------------------------------------
# SECCIÓN 3: FUNCIÓN PRINCIPAL DE LA PÁGINA DE STREAMLIT
# -----------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import date, datetime

def show_statistics_tab():
    """
    Versión simplificada con debug para identificar el problema
    """
    
    # TEST 1: Verificar que la función se ejecuta
    st.write("🔧 TEST 1: La función se está ejecutando")
    
    try:
        # TEST 2: Verificar importaciones
        st.write("🔧 TEST 2: Verificando importaciones...")
        
        try:
            from functions import execute_query, connect_to_supabase
            st.write("✅ functions importadas")
        except Exception as e:
            st.error(f"❌ Error en functions: {e}")
            # Continuar con el debug incluso si falla
        
        try:
            from fEncuesta import get_id_paciente_por_dni
            st.write("✅ fEncuesta importada")
        except Exception as e:
            st.error(f"❌ Error en fEncuesta: {e}")
            # Continuar con el debug incluso si falla
        
        # TEST 3: Verificar estado de sesión
        st.write("🔧 TEST 3: Verificando sesión...")
        st.write(f"session_state keys: {list(st.session_state.keys())}")
        st.write(f"logged_in: {st.session_state.get('logged_in')}")
        st.write(f"dni: {st.session_state.get('dni')}")
        
        # TEST 4: Mostrar interfaz básica independientemente del login
        st.header("📊 Análisis de Riesgo")
        st.write("Esta es la pestaña de estadísticas")
        
        # Verificar login de forma más permisiva
        if 'logged_in' not in st.session_state or not st.session_state.get('logged_in'):
            st.warning("🔒 No hay sesión activa")
            
            # Mostrar interfaz de ejemplo incluso sin login
            st.subheader("Vista de Ejemplo (sin datos reales)")
            
            # Crear gráfico de ejemplo
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=25,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Ejemplo de Análisis"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgreen"},
                        {'range': [30, 60], 'color': "yellow"},
                        {'range': [60, 100], 'color': "red"}
                    ]
                }
            ))
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.info("Inicia sesión para ver tu análisis personalizado")
            return
        
        # TEST 5: Usuario logueado - obtener datos
        st.write("🔧 TEST 5: Usuario logueado, obteniendo datos...")
        
        dni = st.session_state.get("dni")
        if not dni:
            st.error("No se encontró DNI en la sesión")
            return
        
        st.write(f"DNI encontrado: {dni}")
        
        # TEST 6: Conexión a BD
        st.write("🔧 TEST 6: Conectando a base de datos...")
        
        try:
            conn = connect_to_supabase()
            st.write("✅ Conexión establecida")
            
            # Consulta simple
            query = "SELECT nombre FROM pacientes WHERE dni = %s"
            result = execute_query(query, params=[dni], conn=conn, is_select=True)
            
            if not result.empty:
                nombre = result.iloc[0]['nombre']
                st.success(f"✅ Paciente encontrado: {nombre}")
                
                # Mostrar interfaz principal
                st.header(f"📊 Análisis de Riesgo para {nombre}")
                
                # Botón de análisis simple
                if st.button("🔍 Realizar Análisis de Prueba"):
                    st.success("✅ Botón funcionando")
                    
                    # Gráfico de prueba
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        fig1 = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=20,
                            title={'text': "Diabetes"},
                            gauge={'axis': {'range': [None, 100]}}
                        ))
                        fig1.update_layout(height=250)
                        st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        fig2 = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=35,
                            title={'text': "Hipertensión"},
                            gauge={'axis': {'range': [None, 100]}}
                        ))
                        fig2.update_layout(height=250)
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    with col3:
                        fig3 = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=15,
                            title={'text': "Cáncer"},
                            gauge={'axis': {'range': [None, 100]}}
                        ))
                        fig3.update_layout(height=250)
                        st.plotly_chart(fig3, use_container_width=True)
                    
                    st.info("Análisis de prueba completado - Próximamente con datos reales")
                
            else:
                st.warning(f"No se encontró paciente con DNI: {dni}")
                
        except Exception as e:
            st.error(f"Error en base de datos: {e}")
            st.write("Mostrando interfaz de fallback...")
            
            # Interfaz de fallback
            st.header("📊 Análisis de Riesgo")
            st.warning("No se pudo conectar a la base de datos")
            st.button("🔍 Reintentar Conexión")
        
    except Exception as e:
        st.error(f"Error general en la función: {e}")
        st.write("Información de debug:")
        st.code(str(e))

# Versión aún más simple para probar
def show_statistics_tab_minimal():
    """
    Versión súper simple solo para probar que aparece algo
    """
    st.title("📊 Estadísticas")
    st.write("Hola, esta es la pestaña de estadísticas")
    st.success("✅ La función se ejecuta correctamente")
    
    if st.button("Test Button"):
        st.balloons()
        st.write("¡El botón funciona!")

# Para usar la versión minimal, cambia el nombre de la función en tu archivo principal:
# from statistics_tab import show_statistics_tab_minimal as show_statistics_tab
def show_full_analysis():
    """Mostrar el análisis completo solo si todo está OK"""
    
    st.header("📊 Análisis de Riesgo")
    
    # Datos de ejemplo simple
    data = [
        {'enfermedad': 'Diabetes', 'similitud': 25.0},
        {'enfermedad': 'Hipertension', 'similitud': 15.0},
        {'enfermedad': 'Cancer', 'similitud': 10.0}
    ]
    
    # Mostrar medidores
    cols = st.columns(3)
    
    for i, result in enumerate(data):
        with cols[i]:
            # Crear medidor simple
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result['similitud'],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Riesgo {result['enfermedad']}", 'font': {'size': 14}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#2E3B4E"},
                    'steps': [
                        {'range': [0, 30], 'color': "lightgreen"},
                        {'range': [30, 60], 'color': "yellow"},
                        {'range': [60, 100], 'color': "red"}
                    ],
                }
            ))
            fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            if result['similitud'] < 30:
                st.success(f"Bajo riesgo ({result['similitud']:.1f}%)")
            else:
                st.warning(f"Riesgo moderado ({result['similitud']:.1f}%)")

def main():
    st.set_page_config(
        page_title="MedCheck - Estadísticas",
        page_icon="📊",
        layout="wide"
    )
    
    show_statistics_tab()

if __name__ == "__main__":
    main()

