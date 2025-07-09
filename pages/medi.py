import streamlit as st
import pandas as pd
from datetime import date, time
# Se importan las funciones necesarias del backend, incluyendo la nueva
from fmedi import (
    get_medicamentos, 
    marcar_medicamento_como_finalizado, 
    insertar_medicamento, 
    formatear_dosis_texto, 
    registrar_toma, 
    contar_tomas_hoy  # Reemplaza a verificar_toma_hoy
)
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

# --- Configuración de la página y conexión ---
conn = connect_to_supabase()

st.set_page_config(
    page_title="MedCheck - Medicamentos",
    page_icon="💊",
    layout="wide"
)

# --- Estilos CSS (sin cambios de color) ---
st.markdown("""
    <style>
    .main-title { color: #800020; font-size: 3em; font-weight: bold; margin-bottom: 1em; }
    .stButton>button { background-color: #800020 !important; color: white !important; border-radius: 5px; width: 100%; margin-bottom: 5px;}
    .stButton>button:hover { background-color: #600010 !important; color: white !important; }
    .medcheck-text { color: #800020; font-weight: bold; }
    .med-card { border: 1px solid #ddd; border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stock-info { font-size: 0.9em; color: #555; }
    .low-stock-warning { font-weight: bold; color: #D32F2F; margin-top: 5px; display: block; }
    .action-container { padding-top: 15px; }
    .st-expander { border: 1px solid #ddd !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">💊 <span class="medcheck-text">MedCheck</span> - Medicamentos</h1>', unsafe_allow_html=True)

# --- Verificación de sesión y encuesta ---
dni = st.session_state.get("dni")
if not dni:
    st.warning("Por favor, inicie sesión para ver sus medicamentos.")
    st.stop()

# --- Sección de Medicamentos Actuales ---
st.subheader("Tratamientos actuales")
med_actuales = get_medicamentos(dni=dni, solo_actuales=True, conn=conn)
if med_actuales.empty:
    st.info("No hay medicamentos actualmente registrados.")
else:
    med_actuales['dosis_formateada'] = med_actuales.apply(formatear_dosis_texto, axis=1)
    for i, row in med_actuales.iterrows():
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            stock_actual = row.get('stock_actual')
            recordatorio_activo = row.get('recordatorio', False)
            tomas_registradas_hoy = contar_tomas_hoy(row['id_medicamento'], conn=conn)
            
            stock_text = f"<b>Stock:</b> {int(stock_actual)} unidades" if pd.notna(stock_actual) else "<b>Stock:</b> No registrado"
            tomas_text = f"<b>Tomas registradas hoy:</b> {tomas_registradas_hoy}"

            low_stock_html = ""
            if recordatorio_activo and pd.notna(stock_actual) and stock_actual <= 5:
                 low_stock_html = f"<div class='low-stock-warning'>🔔 ¡QUEDAN POCAS UNIDADES!</div>"
            
            st.markdown(f"""
                <div class='med-card'>
                    <b>{row['nombre']} ({row['gramaje_mg']} mg)</b><br>
                    <i>{row['dosis_formateada']}</i><br>
                    <b>Motivo:</b> {row['motivo']}<br>
                    <span class='stock-info'>{stock_text}</span><br>
                    <span class='stock-info'>{tomas_text}</span>
                    {low_stock_html}
                </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("<div class='action-container'>", unsafe_allow_html=True)
            # --- Botón para registrar la toma ---
            if st.button("Registrar Toma 💊", key=f"toma_btn_{row['id_medicamento']}", help="Registra una toma y descuenta del stock."):
                registrar_toma(row['id_medicamento'], row['dosis_cantidad'], conn=conn)
                st.rerun()

            # --- Botón para finalizar el tratamiento ---
            if st.button("Finalizar ❌", key=f"final_btn_{row['id_medicamento']}", help="Mueve este tratamiento al historial."):
                marcar_medicamento_como_finalizado(row['id_medicamento'], conn=conn)
                st.toast(f"El tratamiento con '{row['nombre']}' se movió al historial.", icon="📜")
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# --- FORMULARIO AVANZADO PARA AGREGAR MEDICAMENTO ---
with st.expander("➕ Agregar nuevo medicamento", expanded=True):
    with st.form("nuevo_medicamento_avanzado", clear_on_submit=True):
        st.write("Información General")
        col_nombre, col_droga, col_gramaje = st.columns(3)
        with col_nombre:
            nombre = st.text_input("Nombre comercial", placeholder="Ej: Actron")
        with col_droga:
            droga = st.text_input("Droga", placeholder="Ej: Ibuprofeno")
        with col_gramaje:
            gramaje_mg = st.number_input("Gramaje (mg)", min_value=0.0, step=0.1, format="%.2f")

        st.write("Dosis y Frecuencia")
        col_cant, col_unidad, col_tipo_frec = st.columns(3)
        with col_cant:
            dosis_cantidad = st.number_input("Cantidad por toma", min_value=1, step=1)
        with col_unidad:
            dosis_unidad = st.selectbox("Unidad", ["comprimido(s)", "mililitro(s)", "gota(s)", "aplicación(es)", "unidad(es)"])
        with col_tipo_frec:
            frecuencia_tipo = st.selectbox("Tipo de frecuencia", ["Cada 'X' horas", "En horarios específicos del día", "En días específicos de la semana"])

        frecuencia_valor = {}
        if frecuencia_tipo == "Cada 'X' horas":
            # --- Texto del input mejorado ---
            intervalo = st.number_input("Frecuencia de la toma (intervalo en horas)", min_value=1, max_value=48, step=1, key="intervalo_horas")
            frecuencia_valor = {"intervalo_horas": intervalo}
        elif frecuencia_tipo == "En horarios específicos del día":
            horas_opts = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 30)]
            horas_seleccionadas = st.multiselect("Frecuencia de la toma (seleccione horarios)", options=horas_opts, key="horarios_dia")
            frecuencia_valor = {"horarios_dia": sorted(horas_seleccionadas)}
        elif frecuencia_tipo == "En días específicos de la semana":
            dias_opts = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            dias_seleccionados = st.multiselect("Frecuencia de la toma (seleccione días)", options=dias_opts, key="dias_semana")
            horas_opts_dias = [time(h, m).strftime("%H:%M") for h in range(24) for m in (0, 30)]
            horas_seleccionadas_dias = st.multiselect("Horarios para los días seleccionados", options=horas_opts_dias, key="horarios_en_dias")
            frecuencia_valor = {"dias_semana": dias_seleccionados, "horarios_en_dias": sorted(horas_seleccionadas_dias)}

        st.write("Stock y Fechas")
        col_stock, col_recordatorio = st.columns(2)
        with col_stock:
            stock_inicial = st.number_input("Cantidad inicial en blíster/caja", min_value=0, step=1)
        with col_recordatorio:
            st.write("‎") 
            recordatorio = st.checkbox("Avisarme si se está acabando", value=True)
        
        motivo = st.text_input("Motivo del tratamiento", placeholder="Ej: Gripe, control de alergia, etc.")
        
        col_fecha1, col_fecha2 = st.columns(2)
        with col_fecha1:
            fecha_inicio = st.date_input("Fecha de inicio", date.today())
        with col_fecha2:
            fecha_fin = st.date_input("Fecha de finalización (opcional)", value=None)

        enviar = st.form_submit_button("Guardar Medicamento")

        if enviar:
            if not all([nombre, droga]) or not frecuencia_valor:
                st.warning("Por favor, complete todos los campos obligatorios (Nombre, Droga, y detalles de Frecuencia).")
            else:
                insertar_medicamento(dni, droga, nombre, gramaje_mg, motivo, fecha_inicio, fecha_fin,
                                     dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor,
                                     stock_inicial, recordatorio, conn=conn)
                st.success(f"Medicamento '{nombre}' agregado correctamente.")
                st.rerun()

# --- Historial de Medicamentos (sin cambios) ---
st.markdown("---")
st.subheader("📜 Historial de medicamentos finalizados")
med_historial = get_medicamentos(dni=dni, solo_finalizados=True, conn=conn)
if med_historial.empty:
    st.info("Aún no hay medicamentos finalizados.")
else:
    med_historial['dosis_formateada'] = med_historial.apply(formatear_dosis_texto, axis=1)
    st.dataframe(med_historial[["nombre", "dosis_formateada", "motivo", "fecha_inicio", "fecha_fin"]],
                 use_container_width=True, hide_index=True,
                 column_config={"nombre": "Nombre", "dosis_formateada": "Dosis y Frecuencia", "motivo": "Motivo",
                                "fecha_inicio": st.column_config.DateColumn("Desde", format="DD/MM/YYYY"),
                                "fecha_fin": st.column_config.DateColumn("Hasta", format="DD/MM/YYYY")})
