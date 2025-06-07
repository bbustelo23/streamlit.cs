import streamlit as st
import pandas as pd
from datetime import date
# CORREGIDO: Importar todas las funciones necesarias
from fMedicamentos import (
    get_medicamentos, 
    marcar_medicamento_como_finalizado, 
    insertar_medicamento, 
    formatear_dosis_texto, 
    registrar_toma,
    ocultar_medicamento  # NUEVA función
)
from fEncuesta import get_encuesta_completada
from functions import connect_to_supabase

# Inicializar estados de sesión
if 'showing_form' not in st.session_state:
    st.session_state.showing_form = False
if 'show_history' not in st.session_state:
    st.session_state.show_history = False
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None

# --- Conexión y Setup Inicial ---
try:
    conn = connect_to_supabase()
    st.title("💊 Gestión de Medicación")
except Exception as e:
    st.error(f"No se pudo conectar a la base de datos: {e}")
    st.stop()

dni = st.session_state.get("dni")
if not dni:
    st.warning("Por favor, iniciá sesión para ver tu medicación.")
    st.stop()

# --- Obtener información del paciente actual ---
try:
    from functions import execute_query
    query = "SELECT dni, nombre FROM pacientes WHERE dni = %s"
    paciente_info = execute_query(query, [dni], conn=conn, is_select=True)
    
    if not paciente_info.empty:
        dni_actual = dni
        nombre_paciente_actual = paciente_info.iloc[0]['nombre']
    else:
        dni_actual = dni
        nombre_paciente_actual = "Usuario"
        
except Exception as e:
    st.error(f"Error al cargar información del paciente: {e}")
    dni_actual = dni
    nombre_paciente_actual = "Usuario"

# --- Verificación de Encuesta ---
encuesta_completada = get_encuesta_completada(dni_actual, conn=conn)
if not encuesta_completada.empty and not encuesta_completada.iloc[0]["encuesta_realizada"]:
    st.warning("Antes de continuar, necesitamos que completes una breve encuesta sobre tu salud y hábitos.")
    if st.button("📝 Completar Encuesta"):
        st.switch_page("pages/_Encuesta.py")
    st.stop()

# --- MEJORADO: Mostrar Medicamentos Actuales ---
st.markdown(f"### 👤  Hola {nombre_paciente_actual}!")
st.subheader(" Tratamientos Actuales")

try:
    med_actuales = get_medicamentos(dni=dni_actual, solo_actuales=True, conn=conn)
    if med_actuales.empty:
        st.info("No hay tratamientos activos registrados.")
    else:
        for i, row in med_actuales.iterrows():
            col1, col2, col3 = st.columns([0.7, 0.15, 0.15])
            
            with col1:
                dosis_formateada = formatear_dosis_texto(row)
                stock_texto = ""
                if row.get('stock_actual') is not None:
                    stock_texto = f"Stock restante: <b>{row['stock_actual']}</b>"
                    if row['stock_actual'] <= 10 and row['stock_actual'] > 0:
                        stock_texto += " ⚠️ ¡Stock bajo!"
                    elif row['stock_actual'] == 0:
                        stock_texto = "<b>⚠️ ¡Stock agotado!</b>"

                # Información sobre fecha de finalización
                fecha_fin_texto = ""
                if row.get('fecha_fin'):
                    fecha_fin_str = row['fecha_fin'].strftime('%d/%m/%Y') if hasattr(row['fecha_fin'], 'strftime') else str(row['fecha_fin'])
                    fecha_fin_texto = f"<br><small>📅 Finaliza el: {fecha_fin_str}</small>"

                st.markdown(f"""
                <div style='padding: 15px; border: 1px solid #ddd; border-radius: 10px; margin-bottom: 10px; background-color: #f9f9f9;'>
                    <h4 style='margin: 0; color: #2E86AB;'>{row['nombre']} ({row['droga']})</h4>
                    <p style='margin: 5px 0;'><b>Dosis:</b> {dosis_formateada}</p>
                    <p style='margin: 5px 0;'><b>Motivo:</b> {row.get('motivo', 'No especificado')}</p>
                    {stock_texto}
                    {fecha_fin_texto}
                </div>
                """, unsafe_allow_html=True)
                
                if row.get('stock_actual') is not None and row['stock_actual'] > 0:
                    if st.button(f"💊 Registrar toma", key=f"toma_{row['id_medicamento']}"):
                        registrar_toma(row['id_medicamento'], row['dosis_cantidad'], conn=conn)
                        st.rerun()
            
            with col2:
                if st.button("✅ Finalizar", key=f"finalizar_{row['id_medicamento']}", help="Marcar tratamiento como terminado"):
                    marcar_medicamento_como_finalizado(row['id_medicamento'], conn=conn)
                    st.success(f"¡Tratamiento finalizado!")
                    st.rerun()
            
            with col3:
                # NUEVO: Botón para ocultar medicamento
                if st.button("👁️‍🗨️ Ocultar", key=f"ocultar_{row['id_medicamento']}", help="Ocultar de la vista (no se elimina de la base de datos)"):
                    ocultar_medicamento(row['id_medicamento'], conn=conn)
                    st.success("Medicamento ocultado")
                    st.rerun()
                    
except Exception as e:
    st.error(f"Error al cargar los medicamentos actuales: {e}")

# --- Agregar Nuevo Medicamento ---
st.markdown("---")
st.subheader("➕ Agregar Nuevo Tratamiento")

if not st.session_state.showing_form:
    if st.button("Agregar Nuevo Medicamento", type="primary"):
        st.session_state.showing_form = True
        st.rerun()

if st.session_state.showing_form:
    
    # PASO 1: IDENTIFICACIÓN
    st.markdown("##### 1. ¿Qué medicamento es?")
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Marca comercial", help="Ej: Tafirol, Ibupirac", key="med_nombre") 
    with col2:
        st.text_input("Droga principal", help="Ej: Paracetamol, Ibuprofeno", key="med_droga")

    # PASO 2: TIPO Y CONCENTRACIÓN
    st.markdown("##### 2. ¿Cómo viene presentado?")
    st.selectbox(
        "Forma farmacéutica",
        ["Comprimidos / Cápsulas", "Líquido (Jarabe / Gotas)", "Otro (Crema, Inyectable, etc.)"],
        key="med_tipo_medicamento"
    )

    if st.session_state.med_tipo_medicamento == "Comprimidos / Cápsulas":
        st.number_input("Gramaje por unidad (en mg)", min_value=0, help="Ej: 500", key="med_gramaje_mg")
    elif st.session_state.med_tipo_medicamento == "Líquido (Jarabe / Gotas)":
        st.text_input("Concentración", help="Ej: '5mg/ml' o '10%'", key="med_concentracion")

    # PASO 3: DOSIS Y FRECUENCIA
    st.markdown("##### 3. ¿Cómo y cuándo se toma?")
    col1, col2 = st.columns(2)
    with col1:
        st.number_input("Cantidad por toma", min_value=0.0, step=0.5, format="%.1f", key="med_dosis_cantidad")
    with col2:
        if st.session_state.med_tipo_medicamento == "Comprimidos / Cápsulas":
            st.selectbox("Unidad", ["comprimido(s)", "cápsula(s)"], key="med_dosis_unidad")
        elif st.session_state.med_tipo_medicamento == "Líquido (Jarabe / Gotas)":
            st.selectbox("Unidad", ["ml", "gota(s)", "cucharadita(s)"], key="med_dosis_unidad")
        else:
            st.text_input("Unidad", help="Ej: aplicación, unidad, etc.", key="med_dosis_unidad")

    st.selectbox("Patrón de frecuencia", 
        ["Cada 'X' horas", "En horarios específicos del día", "En días específicos de la semana"],
        key="med_frecuencia_tipo"
    )

    # Lógica condicional para frecuencia
    frecuencia_valor = {}
    if st.session_state.med_frecuencia_tipo == "Cada 'X' horas":
        st.number_input("Indicar cada cuántas horas", min_value=1, max_value=48, step=1, key="med_freq_valor_horas")
        frecuencia_valor['intervalo_horas'] = st.session_state.med_freq_valor_horas
        
    elif st.session_state.med_frecuencia_tipo == "En horarios específicos del día":
        st.multiselect("Seleccionar los horarios de toma", [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)], key="med_freq_valor_horarios")
        frecuencia_valor['horarios_dia'] = sorted(st.session_state.med_freq_valor_horarios)

    elif st.session_state.med_frecuencia_tipo == "En días específicos de la semana":
        st.multiselect("1. Seleccionar los días de toma", ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"], key="med_freq_valor_dias")
        frecuencia_valor['dias_semana'] = st.session_state.med_freq_valor_dias
        st.multiselect("2. Seleccionar los horarios para esos días", [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)], key="med_freq_valor_horarios_sem")
        frecuencia_valor['horarios_en_dias'] = sorted(st.session_state.med_freq_valor_horarios_sem)

    # PASO 4: DETALLES ADICIONALES
    st.markdown("##### 4. Detalles adicionales")
    st.number_input("¿Cuántas dosis vienen en la caja/envase? (0 si no aplica)", min_value=0, step=1, key="med_stock_inicial")
    st.text_input("Motivo del tratamiento", help="Ej: Gripe, Hipertensión, Anticonceptivo", key="med_motivo")
    st.date_input("Fecha de inicio del tratamiento", date.today(), key="med_fecha_inicio")
    st.date_input("Fecha de finalización (opcional)", value=None, key="med_fecha_fin")

    # BOTONES DE ACCIÓN
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar Medicamento", type="primary"):
            try:
                if not st.session_state.med_nombre or not st.session_state.med_droga:
                    st.error("El nombre y la droga del medicamento son obligatorios.")
                else:
                    insertar_medicamento(
                        dni=dni_actual,  # Usar el DNI del paciente seleccionado
                        droga=st.session_state.med_droga, 
                        nombre=st.session_state.med_nombre, 
                        gramaje_mg=st.session_state.get("med_gramaje_mg"), 
                        concentracion=st.session_state.get("med_concentracion"),
                        motivo=st.session_state.med_motivo, 
                        fecha_inicio=st.session_state.med_fecha_inicio, 
                        fecha_fin=st.session_state.med_fecha_fin,
                        dosis_cantidad=st.session_state.med_dosis_cantidad, 
                        dosis_unidad=st.session_state.med_dosis_unidad, 
                        frecuencia_tipo=st.session_state.med_frecuencia_tipo, 
                        frecuencia_valor=frecuencia_valor,
                        stock_inicial=st.session_state.med_stock_inicial,
                        conn=conn
                    )
                    st.success("¡Medicamento agregado correctamente!")

                    # Limpiar formulario
                    keys_to_delete = [k for k in st.session_state if k.startswith('med_')]
                    for key in keys_to_delete:
                        del st.session_state[key]
                    
                    st.session_state.showing_form = False
                    st.rerun()

            except Exception as e:
                st.error(f"No se pudo guardar el medicamento: {e}")
                st.error(f"Detalles del error: {str(e)}")

    with col2:
        if st.button("❌ Cancelar"):
            st.session_state.showing_form = False
            keys_to_delete = [k for k in st.session_state if k.startswith('med_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.rerun()

# --- MEJORADO: Historial Colapsable ---
st.markdown("---")

# Botón para mostrar/ocultar historial
col1, col2 = st.columns([0.3, 0.7])
with col1:
    if st.button("📜 Mostrar/Ocultar Historial" if not st.session_state.show_history else "📜 Ocultar Historial"):
        st.session_state.show_history = not st.session_state.show_history
        st.rerun()

with col2:
    if st.session_state.show_history:
        st.caption("Mostrando tratamientos finalizados")

# Mostrar historial solo si está activado
if st.session_state.show_history:
    st.subheader("📜 Historial de Tratamientos Finalizados")
    
    try:
        med_historial = get_medicamentos(dni=dni_actual, solo_actuales=False, solo_finalizados=True, conn=conn)

        if med_historial.empty:
            st.info("Aún no hay tratamientos finalizados en el historial.")
        else:
            # Creamos una columna legible para la dosis antes de mostrar el dataframe
            med_historial['dosis_legible'] = med_historial.apply(formatear_dosis_texto, axis=1)
            
            st.dataframe(
                med_historial[["nombre", "dosis_legible", "motivo", "fecha_inicio", "fecha_fin"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "nombre": "Medicamento",
                    "dosis_legible": "Dosis y Frecuencia", 
                    "motivo": "Motivo",
                    "fecha_inicio": "Inicio",
                    "fecha_fin": "Fin"
                }
            )
    except Exception as e:
        st.error(f"Error al cargar el historial de medicamentos: {e}")

