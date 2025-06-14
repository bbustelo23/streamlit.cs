import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from functions import execute_query, connect_to_supabase
from fEncuesta import obtener_edad, get_id_paciente_por_dni, tiene_antecedente_enfermedad_por_dni


def load_medical_profiles():
    """Cargar perfiles médicos desde la base de datos"""
    try:
        query = "SELECT * FROM perfiles_medicos"
        df = execute_query(query, is_select=True)
        return df
    except Exception as e:
        st.error(f"Error cargando perfiles médicos: {e}")
        return pd.DataFrame()

def load_user_medical_history():
    """Cargar historial médico del usuario de la sesión actual desde la base de datos"""
    try:
        dni = st.session_state.get("dni")
        if not dni:
            return None
            
        id_paciente = int(get_id_paciente_por_dni(dni))
        if not id_paciente:
            return None

        query = "SELECT * FROM historial_medico WHERE id_paciente = %s"
        df = execute_query(query, params=(id_paciente,), is_select=True)
        
        if not df.empty:
            # Diccionario original con posibles tipos de NumPy (ej: numpy.int64)
            data_numpy = df.iloc[0].to_dict()
            data = {key: value.item() if hasattr(value, 'item') else value for key, value in data_numpy.items()}

            data['id_paciente'] = id_paciente
            return data
            
        return None
    except Exception as e:
        st.error(f"Error cargando tu historial médico: {e}")
        return None

# El resto del código no necesita cambios, ya que el problema se soluciona en el origen de los datos.
# Sin embargo, para máxima seguridad, también haré una pequeña conversión explícita
# al llamar al gráfico de gauge, por si `calculate_similarity` devolviera un `numpy.float64`.

def map_user_profile_to_comparison(user_data):
    """Mapear datos del historial médico del usuario al formato de comparación."""
    dni = st.session_state.get("dni")
    conn = connect_to_supabase()
    
    mapped_profile = {
        'edad': obtener_edad(user_data.get('id_paciente')),
        'genero': user_data.get('genero') or user_data.get('sexo'),
        'actividad_fisica': user_data.get('actividad_fisica'),
        'fumador': user_data.get('fumador'),
        'alcohol_frecuente': user_data.get('consume_alcohol') or user_data.get('alcohol_frecuente') or user_data.get('bebe_alcohol'),
        'antecedentes_familiares_cancer': tiene_antecedente_enfermedad_por_dni(dni, 'cancer', conn=conn),
        'antecedentes_familiares_diabetes': tiene_antecedente_enfermedad_por_dni(dni, 'diabetes', conn=conn),
        'antecedentes_familiares_hipertension': tiene_antecedente_enfermedad_por_dni(dni, 'hipertension', conn=conn),
        'presion_arterial_alta': user_data.get('presion_alta') or user_data.get('presion_arterial_alta') or user_data.get('hipertension'),
        'colesterol_alto': user_data.get('colesterol_alto') or user_data.get('colesterol_elevado'),
        'estres_alto': user_data.get('nivel_estres') == 'Alto' if user_data.get('nivel_estres') else user_data.get('estres_alto')
    }
    return mapped_profile

def calculate_similarity(user_profile, disease_profiles):
    """Calcular similitud entre perfil del usuario y perfiles de enfermedad"""
    similarities = []
    characteristics = [
        'actividad_fisica', 'fumador', 'alcohol_frecuente',
        'antecedentes_familiares_cancer', 'antecedentes_familiares_diabetes',
        'antecedentes_familiares_hipertension', 'colesterol_alto', 'estres_alto'
    ]

    for _, profile in disease_profiles.iterrows():
        matches = 0
        total_characteristics = 0
        for char in characteristics:
            # Se añade .get(char) para evitar KeyError si la columna no existe en un perfil
            if user_profile.get(char) is not None and profile.get(char) is not None:
                if user_profile.get(char) == profile.get(char):
                    matches += 1
                total_characteristics += 1

        if user_profile.get('edad') and profile.get('edad'):
            if abs(user_profile.get('edad') - profile.get('edad')) <= 10:
                matches += 1
            total_characteristics += 1
        
        if total_characteristics > 0:
            similarity_percentage = (matches / total_characteristics) * 100
            similarities.append(similarity_percentage)

    return np.mean(similarities) if similarities else 0

def create_risk_gauge(percentage, disease_name):
    """Crear gráfico de gauge para mostrar porcentaje de riesgo"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = percentage,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"Similitud con {disease_name}", 'font': {'size': 16}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E3B4E"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'lightgreen'},
                {'range': [50, 75], 'color': 'yellow'},
                {'range': [75, 100], 'color': 'lightcoral'}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig

def show_statistics_tab():
    """Mostrar la pestaña de estadísticas para el usuario logueado"""
    st.header("📊 Mi Análisis de Riesgo Médico")
    st.write("Compara tu perfil médico con patrones de personas que padecen ciertas enfermedades.")

    if not st.session_state.get("dni"):
        st.warning("⚠️ Por favor, inicia sesión para ver tu análisis de riesgo personalizado.")
        return

    df_profiles = load_medical_profiles()
    user_medical_data = load_user_medical_history()

    if df_profiles.empty:
        st.error("No se pudieron cargar los datos de referencia. El análisis no puede continuar.")
        return

    if not user_medical_data:
        st.info("ℹ️ Aún no tienes un historial médico registrado. Completa tu perfil para poder realizar un análisis.")
        return

    with st.expander("📋 Ver Mi Perfil Médico", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Información Básica:**")
            st.write(f"• DNI: {st.session_state.get('dni', 'N/A')}")
            st.write(f"• Edad: {obtener_edad(user_medical_data.get('id_paciente')) or 'N/A'}")
            st.write(f"• Género: {user_medical_data.get('genero', 'N/A')}")
        with col2:
            st.write("**Hábitos y Condiciones:**")
            habits = []
            if user_medical_data.get('actividad_fisica'): habits.append("✅ Realizas actividad física")
            else: habits.append("❌ No realizas actividad física")
            if user_medical_data.get('fumador'): habits.append("🚬 Fumador")
            if user_medical_data.get('alcohol_frecuente'): habits.append("🍷 Consumes alcohol frecuentemente")
            for habit in habits:
                st.write(f"• {habit}")
                
    if st.button("🔍 Analizar Mi Riesgo", type="primary", use_container_width=True):
        user_profile = map_user_profile_to_comparison(user_medical_data)

        if sum(1 for v in user_profile.values() if v is not None) < 5:
            st.warning("⚠️ Tu perfil tiene información limitada. Los resultados pueden no ser precisos.")

        st.subheader("📈 Resultados del Análisis")
        
        diseases = df_profiles['enfermedad'].unique()
        diseases = [d for d in diseases if d and d.lower() != 'saludable']

        results = []
        for disease in diseases:
            disease_profiles = df_profiles[df_profiles['enfermedad'] == disease]
            similarity = calculate_similarity(user_profile, disease_profiles)
            results.append({'enfermedad': disease, 'similitud': similarity})

        results = sorted(results, key=lambda x: x['similitud'], reverse=True)

        st.write("### 🎯 Similitud con Perfiles de Enfermedades")
        cols = st.columns(min(3, len(results)))
        for i, result in enumerate(results[:3]):
            with cols[i]:
                # --- PEQUEÑA MEJORA DE ROBUSTEZ ---
                # Convertimos a float() nativo antes de pasarlo a Plotly, por si acaso.
                fig = create_risk_gauge(float(result['similitud']), result['enfermedad'])
                st.plotly_chart(fig, use_container_width=True)
                
                sim_value = result['similitud']
                if sim_value >= 75:
                    st.error(f"**Alta similitud ({sim_value:.1f}%)**", icon="⚠️")
                elif sim_value >= 50:
                    st.warning(f"**Similitud moderada ({sim_value:.1f}%)**", icon="⚡")
                else:
                    st.success(f"**Baja similitud ({sim_value:.1f}%)**", icon="✅")

        # (El resto del código de la UI no cambia)
        st.write("### 📊 Detalle de Similitudes")
        results_df = pd.DataFrame(results)
        results_df['similitud'] = results_df['similitud'].round(1)
        results_df.columns = ['Enfermedad', 'Similitud (%)']
        def color_similarity(val):
            if val >= 75: return 'background-color: #ffebee'
            elif val >= 50: return 'background-color: #fff3e0'
            else: return 'background-color: #e8f5e9'
        styled_df = results_df.style.applymap(color_similarity, subset=['Similitud (%)'])
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.write("### 📈 Comparación Visual")
        fig_bar = px.bar(
            results_df, x='Similitud (%)', y='Enfermedad', orientation='h',
            color='Similitud (%)', color_continuous_scale='RdYlGn_r',
            title="Porcentaje de Similitud por Enfermedad", text='Similitud (%)'
        )
        fig_bar.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_bar.update_layout(height=400, showlegend=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

        st.write("### 💡 Recomendaciones Personalizadas")
        recommendations = []
        if not user_profile.get('actividad_fisica'): recommendations.append("🏃‍♂️ Incorporar actividad física regular (150 min/semana)")
        if user_profile.get('fumador'): recommendations.append("🚭 Considerar un programa para dejar de fumar")
        if user_profile.get('alcohol_frecuente'): recommendations.append("🍷 Moderar el consumo de alcohol")
        if user_profile.get('estres_alto'): recommendations.append("🧘‍♀️ Practicar técnicas de manejo del estrés")
        if user_profile.get('presion_arterial_alta'): recommendations.append("🩺 Seguimiento regular de la presión arterial")
        if user_profile.get('colesterol_alto'): recommendations.append("🥗 Dieta baja en grasas saturadas y control del colesterol")

        if recommendations:
            st.write("**Para reducir tus riesgos potenciales, considera:**")
            for rec in recommendations:
                st.write(f"• {rec}")
        else:
            st.success("🎉 ¡Tu perfil muestra hábitos de vida saludables! Continúa así.")

        highest_risk = results[0] if results else None
        if highest_risk and highest_risk['similitud'] > 50:
            st.write("### ⚠️ Factor de Mayor Atención")
            st.info(f""" **{highest_risk['enfermedad']}** muestra la mayor similitud ({highest_risk['similitud']:.1f}%). Recuerda que esto se basa en patrones estadísticos y no es un diagnóstico.""")

        st.write("### ⚕️ Información Importante")
        st.info(""" **Descargo de responsabilidad:** Este análisis es informativo y no reemplaza una consulta médica. Consulta siempre a un profesional de la salud.""")


def main():
    st.set_page_config(
        page_title="MedCheck - Estadísticas",
        page_icon="📊",
        layout="wide"
    )
    show_statistics_tab()

if __name__ == "__main__":
    main()