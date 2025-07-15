import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from functions import connect_to_supabase
# Se importan las funciones corregidas del nuevo archivo fEstadisticas.py
from festa import load_medical_profiles, load_user_medical_history, map_user_profile_to_comparison, calculate_similarity

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Análisis de Riesgo - MedCheck",
    page_icon="📊",
    layout="wide"
)

# --- Estilos CSS para el nuevo diseño ---
st.markdown("""
    <style>
        .main-title { color: #800020; font-size: 2.5em; font-weight: bold; }
        .medcheck-text { color: #800020; }
        .stButton>button {
            background-color: #800020 !important;
            color: white !important;
            border-radius: 8px;
            border: none;
            padding: 10px 24px;
        }
        .stButton>button:hover { background-color: #600010 !important; }
        .card {
            background-color: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; padding: 10px; }
        .stTabs [aria-selected="true"] { background-color: #F8F8F8; font-weight: bold; color: #800020; }
    </style>
    """, unsafe_allow_html=True)

def create_risk_gauge(percentage, disease_name):
    """Crea un gráfico de medidor mejorado."""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = float(percentage), # Asegurarse de que sea float
        title = {'text': f"<b>{disease_name}</b>", 'font': {'size': 20}},
        domain = {'x': [0, 1], 'y': [0, 1]},
        delta = {'reference': 50, 'increasing': {'color': "#D9534F"}, 'decreasing': {'color': "#5CB85C"}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E3B4E"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'lightgreen'},
                {'range': [50, 75], 'color': 'gold'},
                {'range': [75, 100], 'color': 'lightcoral'}
            ],
        }
    ))
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# --- INICIO DE LA APLICACIÓN ---
st.markdown('<h1 class="main-title">📊 <span class="medcheck-text">MedCheck</span> - Análisis de Riesgo</h1>', unsafe_allow_html=True)
st.write("Compara tu perfil de salud con patrones de riesgo conocidos para obtener una visión general. **Esto no es un diagnóstico médico.**")
st.divider()

# --- Verificación de Sesión ---
conn = connect_to_supabase()
dni = st.session_state.get("dni")
if not dni:
    st.warning("⚠️ Por favor, inicia sesión para ver tu análisis de riesgo personalizado.")
    st.stop()

# --- Carga de Datos ---
df_profiles = load_medical_profiles()
user_medical_data = load_user_medical_history(dni, conn)

if df_profiles.empty:
    st.error("No se pudieron cargar los datos de referencia. El análisis no puede continuar.")
    st.stop()

if not user_medical_data:
    st.info("ℹ️ Aún no tienes un historial médico registrado. Completa tu encuesta para poder realizar un análisis.")
    st.stop()

# --- Tarjeta de Perfil de Usuario ---
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader(f"👤 Perfil de {st.session_state.get('nombre', 'Usuario')}")
    user_profile_mapped = map_user_profile_to_comparison(user_medical_data)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Edad", f"{user_profile_mapped.get('edad', 'N/A')} años")
    with col2:
        st.metric("Actividad Física", "Sí" if user_profile_mapped.get('actividad_fisica') else "No")
    with col3:
        st.metric("Fumador", "Sí" if user_profile_mapped.get('fumador') else "No")
    
    if st.button("🔍 Analizar Mi Riesgo", type="primary"):
        st.session_state.analysis_done = True
    st.markdown('</div>', unsafe_allow_html=True)

# --- Resultados del Análisis (si se ha hecho) ---
if st.session_state.get("analysis_done", False):
    st.divider()
    st.header("📈 Resultados del Análisis")

    diseases = df_profiles['enfermedad'].unique()
    diseases = [d for d in diseases if d and d.lower() != 'saludable']

    results = []
    for disease in diseases:
        disease_profiles = df_profiles[df_profiles['enfermedad'] == disease]
        similarity, factors_df = calculate_similarity(user_profile_mapped, disease_profiles)
        results.append({
            'enfermedad': disease, 
            'similitud': similarity,
            'factores': factors_df
        })

    results = sorted(results, key=lambda x: x['similitud'], reverse=True)

    # --- Pestañas de Resultados ---
    tab_resumen, tab_detalle, tab_recom = st.tabs(["Resumen de Riesgo", "Análisis Detallado", "Recomendaciones"])

    with tab_resumen:
        st.subheader("🎯 Similitud con Perfiles de Enfermedades")
        cols = st.columns(min(3, len(results)))
        for i, result in enumerate(results[:3]):
            with cols[i]:
                fig = create_risk_gauge(result['similitud'], result['enfermedad'])
                st.plotly_chart(fig, use_container_width=True)

    with tab_detalle:
        st.subheader("🔬 Comparación de Factores de Riesgo")
        st.write("Aquí puedes ver qué factores de tu perfil coinciden con los perfiles de riesgo analizados.")
        
        for result in results:
            with st.expander(f"**{result['enfermedad']}** - Similitud: {result['similitud']:.1f}%"):
                st.dataframe(result['factores'], use_container_width=True, hide_index=True)

    with tab_recom:
        st.subheader("💡 Recomendaciones Personalizadas")
        recommendations = []
        if not user_profile_mapped.get('actividad_fisica'): recommendations.append("🏃‍♂️ **Actividad Física:** Incorporar al menos 150 minutos de ejercicio moderado por semana.")
        if user_profile_mapped.get('fumador'): recommendations.append("🚭 **Dejar de Fumar:** Buscar apoyo y programas para cesación tabáquica es un paso crucial.")
        if user_profile_mapped.get('alcohol_frecuente'): recommendations.append("🍷 **Moderar Alcohol:** Limitar el consumo de alcohol según las guías de salud.")
        if user_profile_mapped.get('estres_alto'): recommendations.append("🧘‍♀️ **Manejo del Estrés:** Practicar técnicas como meditación, yoga o mindfulness.")
        if user_profile_mapped.get('presion_arterial_alta'): recommendations.append("🩺 **Presión Arterial:** Realizar seguimientos regulares y consultar a un médico sobre la dieta y medicación.")
        if user_profile_mapped.get('colesterol_alto'): recommendations.append("🥗 **Colesterol:** Adoptar una dieta baja en grasas saturadas y trans.")

        if recommendations:
            st.write("**Para reducir tus riesgos potenciales, considera los siguientes hábitos:**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
        else:
            st.success("🎉 ¡Tu perfil muestra hábitos de vida saludables! Continúa así.")
        
        st.divider()
        st.info("""
            **Descargo de responsabilidad:** Este análisis es informativo y no reemplaza una consulta médica. 
            Consulta siempre a un profesional de la salud para obtener un diagnóstico y tratamiento adecuados.
        """)
