import streamlit as st
import pandas as pd
from datetime import date
from fMedicamentos import get_medicamentos, marcar_medicamento_como_finalizado, insertar_medicamento  # funciones que deberías tener
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

conn = connect_to_supabase()

st.title("💊 Medicación")

dni = st.session_state.get("dni")

if not dni:
    st.warning("No hay un DNI cargado en sesión.")
    st.stop()

encuesta_completada = get_encuesta_completada(dni, conn=conn)

if not encuesta_completada.empty and not encuesta_completada.iloc[0]["encuesta_realizada"]:
    st.warning("Antes de continuar, necesitamos que completes una breve encuesta sobre tu salud y hábitos.")
    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")   # Ajustá el path según la estructura de tu app

    st.stop()



st.subheader("Medicamentos actuales")

med_actuales = get_medicamentos(dni=dni, solo_actuales=True, conn=conn)

if med_actuales.empty:
    st.info("No hay medicamentos actualmente registrados.")
else:
    # Mostrar tabla con bordes y opción para marcar como finalizado
    for i, row in med_actuales.iterrows():
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(
                f"""
                <div style='border: 1px solid #ccc; border-radius: 10px; padding: 10px; margin-bottom: 10px;'>
                    <b>{row['nombre']}</b> — {row['dosis']} — {row['frecuencia']}<br>
                    Motivo: {row['motivo']}<br>
                    Desde: {row['inicio']}
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            if st.checkbox("✅", key=f"med_{row['id']}"):
                marcar_medicamento_como_finalizado(row['id'])  # esta función debe poner fecha de finalización (hoy)
                st.rerun()

st.markdown("---")
st.subheader("➕ Agregar nuevo medicamento")

with st.form("nuevo_medicamento"):
    nombre = st.text_input("Marca del medicamento")
    droga = st.text_input("Droga (ej: paracetamol)")
    gramaje_mg = st.number_input("Gramaje (en mg)", min_value=0.0, step=0.1)
    dosis = st.text_input("Frecuencia (ej: 1 vez al día)")
    motivo = st.text_input("Motivo (enfermedad crónica, aguda, anticonceptivo, etc.)")
    fecha_inicio = st.date_input("Fecha de inicio", date.today())
    fecha_fin = st.date_input("Fecha de finalización", date.today())
    enviar = st.form_submit_button("Guardar")

    if enviar:
        insertar_medicamento(dni, droga, nombre, gramaje_mg, dosis, motivo, fecha_inicio, fecha_fin, conn=conn)
        st.success("Medicamento agregado correctamente.")
        st.rerun()

st.markdown("---")
st.subheader("📜 Historial de medicamentos")

med_historial = get_medicamentos(dni=dni, solo_actuales=False, solo_finalizados=True, conn=conn)

if med_historial.empty:
    st.info("Aún no hay medicamentos finalizados.")
else:
    st.dataframe(
        med_historial[["nombre", "dosis", "frecuencia", "motivo", "fecha_inicio", "fecha_fin"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "nombre": "Nombre",
            "dosis": "Dosis",
            "frecuencia": "Frecuencia",
            "motivo": "Motivo",
            "fecha_inicio": "Desde",
            "fecha_fin": "Hasta"
        }
    )
