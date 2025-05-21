import streamlit as st
from datetime import date

# Simulación de base de datos temporal en session_state
if "medicamentos" not in st.session_state:
    st.session_state.medicamentos = []

# Función para agregar o editar medicamento
def guardar_medicamento(nombre, dosis, frecuencia, motivo, inicio, fin, tipo, observaciones, idx=None):
    nuevo = {
        "nombre": nombre,
        "dosis": dosis,
        "frecuencia": frecuencia,
        "motivo": motivo,
        "inicio": inicio,
        "fin": fin,
        "tipo": tipo,
        "observaciones": observaciones
    }
    if idx is not None:
        st.session_state.medicamentos[idx] = nuevo
    else:
        st.session_state.medicamentos.append(nuevo)

# Función para eliminar
def eliminar_medicamento(idx):
    st.session_state.medicamentos.pop(idx)

# Título
st.title("🧪 Medicamentos actuales")

# Elegir visualización
vista = st.radio("Visualización:", ["Tabla", "Cards"], horizontal=True)

# Botón para mostrar formulario
if "mostrar_formulario" not in st.session_state:
    st.session_state.mostrar_formulario = False
if st.button("➕ Añadir medicamento"):
    st.session_state.mostrar_formulario = True
    st.session_state.editar_idx = None

# Mostrar medicamentos (tabla o cards)
if vista == "Tabla":
    if st.session_state.medicamentos:
        st.subheader("📋 Medicamentos en curso (Tabla)")
        for idx, med in enumerate(st.session_state.medicamentos):
            cols = st.columns([2, 1, 1, 2, 1, 1, 1])
            cols[0].write(f"**{med['nombre']}**")
            cols[1].write(med['dosis'])
            cols[2].write(med['frecuencia'])
            cols[3].write(med['motivo'])
            cols[4].write(med['inicio'])
            cols[5].write(med['fin'] if med['fin'] else "—")
            with cols[6]:
                if st.button("✏️", key=f"editar_{idx}"):
                    st.session_state.mostrar_formulario = True
                    st.session_state.editar_idx = idx
                if st.button("🗑️", key=f"borrar_{idx}"):
                    eliminar_medicamento(idx)
                    st.experimental_rerun()
    else:
        st.info("No hay medicamentos cargados.")
else:
    st.subheader("🧾 Medicamentos en curso (Cards)")
    for idx, med in enumerate(st.session_state.medicamentos):
        with st.container():
            st.markdown(f"### 💊 {med['nombre']}")
            st.write(f"- **Dosis:** {med['dosis']}")
            st.write(f"- **Frecuencia:** {med['frecuencia']}")
            st.write(f"- **Motivo:** {med['motivo']}")
            st.write(f"- **Inicio:** {med['inicio']}")
            st.write(f"- **Fin:** {med['fin'] if med['fin'] else '—'}")
            st.write(f"- **Tipo:** {med['tipo']}")
            if med['observaciones']:
                st.write(f"- **Observaciones:** {med['observaciones']}")
            col1, col2 = st.columns(2)
            if col1.button("✏️ Editar", key=f"editar_card_{idx}"):
                st.session_state.mostrar_formulario = True
                st.session_state.editar_idx = idx
            if col2.button("🗑️ Eliminar", key=f"eliminar_card_{idx}"):
                eliminar_medicamento(idx)
                st.experimental_rerun()
            st.markdown("---")

# Formulario para agregar o editar
if st.session_state.mostrar_formulario:
    st.subheader("📥 Formulario de medicamento")
    idx = st.session_state.get("editar_idx")
    data = st.session_state.medicamentos[idx] if idx is not None else {}

    with st.form("form_medicamento", clear_on_submit=(idx is None)):
        nombre = st.text_input("Nombre del medicamento", value=data.get("nombre", ""))
        dosis = st.text_input("Dosis (ej. 10 mg)", value=data.get("dosis", ""))
        frecuencia = st.text_input("Frecuencia (ej. cada 8 h)", value=data.get("frecuencia", ""))
        motivo = st.text_input("Motivo", value=data.get("motivo", ""))
        inicio = st.date_input("Inicio", value=data.get("inicio", date.today()))
        fin = st.date_input("Fin (si aplica)", value=data.get("fin", date.today())) if data.get("tipo") != "Crónico" else None
        tipo = st.selectbox("Tipo", ["Crónico", "Agudo", "Otro"], index=["Crónico", "Agudo", "Otro"].index(data.get("tipo", "Crónico")))
        observaciones = st.text_area("Observaciones (opcional)", value=data.get("observaciones", ""))

        submitted = st.form_submit_button("💾 Guardar")
        if submitted:
            guardar_medicamento(nombre, dosis, frecuencia, motivo, inicio, fin if tipo != "Crónico" else None, tipo, observaciones, idx=idx)
            st.success("Medicamento guardado.")
            st.session_state.mostrar_formulario = False
            st.rerun()

