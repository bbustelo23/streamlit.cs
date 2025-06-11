import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from functions import execute_query

def load_medical_profiles():
    """Cargar perfiles médicos desde la base de datos"""
    try:
        query = "SELECT * FROM perfiles_medicos"
        df = execute_query(query, is_select=True)
        return df
    except Exception as e:
        st.error(f"Error cargando perfiles médicos: {e}")
        return pd.DataFrame()

def load_user_medical_history(id_paciente):
    """Cargar historial médico del usuario desde la base de datos"""
    try:
        query = "SELECT * FROM historial_medico WHERE id_paciente = %s"
        df = execute_query(query, params=(id_paciente,), is_select=True)
        if not df.empty:
            return df.iloc[0].to_dict()  # Convertir la primera fila a diccionario
        return None
    except Exception as e:
        st.error(f"Error cargando historial médico: {e}")
        return None

def get_all_users():
    """Obtener lista de usuarios disponibles"""
    try:
        # Ajusta los nombres de campos según tu tabla historial_medico
        query = "SELECT DISTINCT id_paciente, nombre FROM historial_medico WHERE id_paciente IS NOT NULL"
        df = execute_query(query, is_select=True)
        return df
    except Exception as e:
        st.error(f"Error cargando usuarios: {e}")
        return pd.DataFrame()

def map_user_profile_to_comparison(user_data):
    """
    Mapear datos del historial médico del usuario al formato de comparación
    
    IMPORTANTE: Ajusta los nombres de campos según tu tabla historial_medico real
    Este es un mapeo de ejemplo - necesitas cambiarlo según tus campos
    """
    
    # Ejemplo de mapeo - CAMBIA estos nombres por los de tu tabla real
    mapped_profile = {
        'edad': user_data.get('edad'),
        'genero': user_data.get('genero') or user_data.get('sexo'),
        
        # Hábitos de vida - ajusta según tus campos
        'actividad_fisica': user_data.get('hace_ejercicio') or user_data.get('actividad_fisica') or user_data.get('ejercicio_regular'),
        'fumador': user_data.get('fuma') or user_data.get('fumador') or user_data.get('es_fumador'),
        'alcohol_frecuente': user_data.get('consume_alcohol') or user_data.get('alcohol_frecuente') or user_data.get('bebe_alcohol'),
        
        # Antecedentes familiares - ajusta según tus campos
        'antecedentes_familiares_cancer': user_data.get('antecedentes_cancer'),
        'antecedentes_familiares_diabetes': user_data.get('antecedentes_diabetes'),
        'antecedentes_familiares_hipertension': user_data.get('antecedentes_hipertension'),
        
        # Métricas físicas
        'imc': user_data.get('imc') or calculate_imc(user_data.get('peso'), user_data.get('altura')),
        
        # Condiciones actuales - ajusta según tus campos
        'colesterol_alto': user_data.get('colesterol_alto') or user_data.get('colesterol_elevado'),
        'estres_alto': user_data.get('nivel_estres') == 'Alto' if user_data.get('nivel_estres') else user_data.get('estres_alto')
    }
    
    return mapped_profile

def calculate_imc(peso, altura):
    """Calcular IMC si no está disponible directamente"""
    if peso and altura:
        # Convertir altura a metros si está en cm
        altura_m = altura / 100 if altura > 3 else altura
        return peso / (altura_m ** 2)
    return None

def calculate_similarity(user_profile, disease_profiles):
    """Calcular similitud entre perfil del usuario y perfiles de enfermedad"""
    similarities = []
    
    # Características a comparar
    characteristics = [
        'actividad_fisica', 'fumador', 'alcohol_frecuente',
        'antecedentes_familiares_cancer', 'antecedentes_familiares_diabetes',
        'antecedentes_familiares_hipertension', 'presion_arterial_alta',
        'colesterol_alto', 'estres_alto'
    ]
    
    for _, profile in disease_profiles.iterrows():
        matches = 0
        total_characteristics = 0
        
        # Comparar características booleanas
        for char in characteristics:
            if user_profile.get(char) is not None and profile[char] is not None:
                if user_profile.get(char) == profile[char]:
                    matches += 1
                total_characteristics += 1
        
        # Comparar edad (similar si está dentro de ±10 años)
        if user_profile.get('edad') and profile['edad']:
            age_match = abs(user_profile.get('edad') - profile['edad']) <= 10
            if age_match:
                matches += 1
            total_characteristics += 1
        
        # Comparar IMC (similar si está dentro de ±3 puntos)
        if user_profile.get('imc') and profile['imc']:
            imc_match = abs(user_profile.get('imc') - profile['imc']) <= 3
            if imc_match:
                matches += 1
            total_characteristics += 1
        
        if total_characteristics > 0:
            similarity_percentage = (matches / total_characteristics) * 100
            similarities.append(similarity_percentage)
    
    return np.mean(similarities) if similarities else 0

def create_risk_gauge(percentage, disease_name):
    """Crear gráfico de gauge para mostrar porcentaje de riesgo"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Similitud con perfil de {disease_name}"},
        delta = {'reference': 50},
        gauge = {
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': "lightgreen"},
                {'range': [25, 50], 'color': "yellow"},
                {'range': [50, 75], 'color': "orange"},
                {'range': [75, 100], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig

def show_statistics_tab():
    """Mostrar la pestaña de estadísticas"""
    st.header("📊 Análisis de Riesgo Médico")
    st.write("Compara tu perfil médico con patrones de personas que padecen ciertas enfermedades")
    
    # Cargar datos
    df = load_medical_profiles()
    users_df = get_all_users()
    
    if df.empty:
        st.warning("No se pudieron cargar los datos médicos de referencia")
        return
    
    if users_df.empty:
        st.warning("No se encontraron usuarios con historial médico")
        return
    
    # Selector de usuario
    st.subheader("Seleccionar Usuario")
    
    # Crear opciones para el selectbox
    user_options = {}
    for _, user in users_df.iterrows():
        display_name = f"{user.get('nombre', 'Sin nombre')} (ID: {user['user_id']})"
        user_options[display_name] = user['user_id']
    
    selected_user_display = st.selectbox(
        "Selecciona el usuario para analizar:",
        options=list(user_options.keys()),
        help="Elige el usuario cuyo perfil médico quieres analizar"
    )
    
    if selected_user_display:
        selected_user_id = user_options[selected_user_display]
        
        # Cargar historial médico del usuario seleccionado
        user_medical_data = load_user_medical_history(selected_user_id)
        
        if not user_medical_data:
            st.error("No se pudo cargar el historial médico del usuario seleccionado")
            return
        
        # Mostrar información del usuario
        with st.expander("📋 Ver Perfil del Usuario", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Información Básica:**")
                st.write(f"• Nombre: {user_medical_data.get('nombre', 'N/A')}")
                st.write(f"• Edad: {user_medical_data.get('edad', 'N/A')}")
                st.write(f"• Género: {user_medical_data.get('genero', 'N/A')}")
                st.write(f"• IMC: {user_medical_data.get('imc', 'N/A')}")
            
            with col2:
                st.write("**Hábitos y Condiciones:**")
                habits = []
                if user_medical_data.get('hace_ejercicio') or user_medical_data.get('actividad_fisica'):
                    habits.append("✅ Hace ejercicio")
                else:
                    habits.append("❌ No hace ejercicio")
                
                if user_medical_data.get('fuma') or user_medical_data.get('fumador'):
                    habits.append("🚬 Fumador")
                
                if user_medical_data.get('consume_alcohol') or user_medical_data.get('alcohol_frecuente'):
                    habits.append("🍷 Consume alcohol")
                
                for habit in habits:
                    st.write(f"• {habit}")
        
        # Botón para analizar
        if st.button("🔍 Analizar Riesgo", type="primary", use_container_width=True):
            
            # Mapear perfil del usuario
            user_profile = map_user_profile_to_comparison(user_medical_data)
            
            # Verificar que tenemos datos suficientes
            non_null_values = sum(1 for v in user_profile.values() if v is not None)
            if non_null_values < 5:
                st.warning("⚠️ El perfil del usuario tiene información limitada. Los resultados pueden no ser precisos.")
            
            st.subheader("📈 Resultados del Análisis")
            
            # Obtener enfermedades únicas
            diseases = df['enfermedad'].unique()
            diseases = [d for d in diseases if d != 'Saludable']  # Excluir perfiles saludables
            
            # Calcular similitudes para cada enfermedad
            results = []
            for disease in diseases:
                disease_profiles = df[df['enfermedad'] == disease]
                similarity = calculate_similarity(user_profile, disease_profiles)
                results.append({'enfermedad': disease, 'similitud': similarity})
            
            # Ordenar por similitud descendente
            results = sorted(results, key=lambda x: x['similitud'], reverse=True)
            
            # Mostrar resultados principales
            st.write("### 🎯 Similitud con Perfiles de Enfermedades")
            
            # Mostrar top 3 enfermedades con mayor similitud
            cols = st.columns(min(3, len(results)))
            
            for i, result in enumerate(results[:3]):
                with cols[i]:
                    fig = create_risk_gauge(result['similitud'], result['enfermedad'])
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Interpretación del resultado
                    if result['similitud'] >= 70:
                        st.error(f"⚠️ Alta similitud ({result['similitud']:.1f}%)")
                        st.write("Se recomienda consultar con un médico")
                    elif result['similitud'] >= 50:
                        st.warning(f"⚡ Similitud moderada ({result['similitud']:.1f}%)")
                        st.write("Mantener hábitos saludables y seguimiento")
                    else:
                        st.success(f"✅ Baja similitud ({result['similitud']:.1f}%)")
                        st.write("Perfil de riesgo bajo")
            
            # Tabla detallada de resultados
            st.write("### 📊 Detalle de Similitudes")
            results_df = pd.DataFrame(results)
            results_df['similitud'] = results_df['similitud'].round(1)
            results_df.columns = ['Enfermedad', 'Similitud (%)']
            
            # Aplicar colores según el nivel de riesgo
            def color_similarity(val):
                if val >= 70:
                    return 'background-color: #ffebee'  # Rojo claro
                elif val >= 50:
                    return 'background-color: #fff3e0'  # Naranja claro
                else:
                    return 'background-color: #e8f5e8'  # Verde claro
            
            styled_df = results_df.style.applymap(color_similarity, subset=['Similitud (%)'])
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Gráfico de barras
            st.write("### 📈 Comparación Visual")
            fig_bar = px.bar(
                results_df,
                x='Similitud (%)',
                y='Enfermedad',
                orientation='h',
                color='Similitud (%)',
                color_continuous_scale='RdYlGn_r',
                title="Porcentaje de Similitud por Enfermedad",
                text='Similitud (%)'
            )
            fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig_bar.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Recomendaciones personalizadas
            st.write("### 💡 Recomendaciones Personalizadas")
            
            recommendations = []
            if not user_profile.get('actividad_fisica'):
                recommendations.append("🏃‍♂️ Incorporar actividad física regular (150 min/semana)")
            if user_profile.get('fumador'):
                recommendations.append("🚭 Considerar un programa para dejar de fumar")
            if user_profile.get('alcohol_frecuente'):
                recommendations.append("🍷 Moderar el consumo de alcohol")
            if user_profile.get('imc') and user_profile.get('imc') > 30:
                recommendations.append("⚖️ Trabajar en mantener un peso saludable")
            if user_profile.get('estres_alto'):
                recommendations.append("🧘‍♀️ Practicar técnicas de manejo del estrés")
            if user_profile.get('presion_arterial_alta'):
                recommendations.append("🩺 Seguimiento regular de la presión arterial")
            if user_profile.get('colesterol_alto'):
                recommendations.append("🥗 Dieta baja en grasas saturadas y control del colesterol")
            
            if recommendations:
                st.write("**Para reducir riesgos potenciales, considera:**")
                for rec in recommendations:
                    st.write(f"• {rec}")
            else:
                st.success("🎉 ¡El perfil muestra hábitos de vida saludables! Continúa manteniendo estos buenos hábitos.")
            
            # Mostrar análisis de factores de riesgo más relevantes
            highest_risk = results[0] if results else None
            if highest_risk and highest_risk['similitud'] > 50:
                st.write("### ⚠️ Factor de Mayor Atención")
                st.info(f"""
                **{highest_risk['enfermedad']}** muestra la mayor similitud ({highest_risk['similitud']:.1f}%).
                
                Es importante recordar que esta similitud se basa en patrones estadísticos y factores de riesgo comunes.
                No indica diagnóstico, sino áreas donde se puede enfocar la prevención.
                """)
            
            # Disclaimer
            st.write("### ⚕️ Información Importante")
            st.info("""
            **Descargo de responsabilidad:** Este análisis es únicamente informativo y educativo. 
            No constituye un diagnóstico médico ni reemplaza la consulta con profesionales de la salud.
            Los resultados se basan en patrones estadísticos de factores de riesgo conocidos.
            
            **Recomendación:** Consulta siempre con tu médico para evaluaciones médicas completas y personalizadas.
            """)
    
    else:
        st.info("👆 Selecciona un usuario para comenzar el análisis")

# Función principal para integrar en tu app
def main():
    st.set_page_config(
        page_title="MedCheck - Estadísticas",
        page_icon="📊",
        layout="wide"
    )
    
    show_statistics_tab()

if __name__ == "__main__":
    main()