import streamlit as st
import calendar
import pandas as pd
from datetime import datetime, timedelta, date
import psycopg2
from functions import connect_to_supabase 

# ------------------------
# 🔍 Obtener días con turnos
# ------------------------
def obtener_dias_con_turnos(year, month, dni):
    from functions import connect_to_supabase
    import pandas as pd

    conn = connect_to_supabase()

    query = f"""
        SELECT fecha
        FROM turnos
        INNER JOIN pacientes ON turnos.id_paciente = pacientes.id_paciente
        WHERE EXTRACT(YEAR FROM fecha) = {year}
          AND EXTRACT(MONTH FROM fecha) = {month}
          AND pacientes.dni = '{dni}';
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return set(pd.to_datetime(df["fecha"]).dt.date)

# ------------------------
# 🔍 Obtener, editar y eliminar turnos
# ------------------------
def obtener_turnos_mes(año, mes, dni):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id_turno, t.fecha, p.nombre AS paciente, m.nombre AS medico, t.lugar
        FROM Turnos t
        JOIN Pacientes p ON t.id_paciente = p.id_paciente
        JOIN Medicos m ON t.id_medico = m.id_medico
        WHERE EXTRACT(MONTH FROM t.fecha) = %s
          AND EXTRACT(YEAR FROM t.fecha) = %s
          AND p.dni = %s
        ORDER BY t.fecha
    """, (mes, año, dni))
    datos = cur.fetchall()
    cur.close()
    conn.close()
    return pd.DataFrame(datos, columns=["ID", "Fecha", "Paciente", "Médico", "Lugar"])

def eliminar_turno(id_turno):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("DELETE FROM Turnos WHERE id_turno = %s", (id_turno,))
    conn.commit()
    cur.close()
    conn.close()

def editar_turno(id_turno, nueva_fecha, nuevo_lugar):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("UPDATE Turnos SET fecha = %s, lugar = %s WHERE id_turno = %s", (nueva_fecha, nuevo_lugar, id_turno))
    conn.commit()
    cur.close()
    conn.close()

# ------------------------
# 📋 Pacientes y médicos
# ------------------------
def obtener_o_crear_paciente(dni):
    conn = connect_to_supabase()
    cur = conn.cursor()

    # Buscar si el paciente ya existe
    cur.execute("SELECT id_paciente FROM Pacientes WHERE dni = %s", (dni,))
    paciente = cur.fetchone()

    if paciente:
        id_paciente = paciente[0]
    else:
        # Insertar nuevo paciente sin especificar id_paciente
        cur.execute("INSERT INTO Pacientes (dni) VALUES (%s) RETURNING id_paciente", (dni,))
        id_paciente = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()
    return id_paciente

def obtener_o_crear_medico(nombre, especialidad, lugar):
    conn = connect_to_supabase()
    cursor = conn.cursor()

    try:
        # Verificar si ya existe el médico con ese nombre y especialidad
        cursor.execute(
            "SELECT id_medico FROM Medicos WHERE nombre = %s AND especialidad = %s",
            (nombre, especialidad)
        )
        result = cursor.fetchone()

        if result:
            id_medico = result[0]
            # Actualizar el lugar si es diferente
            cursor.execute(
                "UPDATE Medicos SET lugar = %s WHERE id_medico = %s",
                (lugar, id_medico)
            )
        else:
            # Obtener el próximo ID disponible
            cursor.execute("SELECT COALESCE(MAX(id_medico), 0) + 1 FROM Medicos")
            next_id = cursor.fetchone()[0]
            
            # Insertar nuevo médico con ID específico
            cursor.execute(
                "INSERT INTO Medicos (id_medico, nombre, especialidad, lugar) VALUES (%s, %s, %s, %s)",
                (next_id, nombre, especialidad, lugar)
            )
            id_medico = next_id
        
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Error al crear/obtener médico: {e}")
        raise e
    finally:
        cursor.close()
        conn.close()
    
    return id_medico

def guardar_turno(id_paciente, id_medico, fecha, hora, lugar):
    conn = connect_to_supabase()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO Turnos (fecha, hora, id_paciente, id_medico, lugar) VALUES (%s, %s, %s, %s, %s)",
            (fecha, hora, id_paciente, id_medico, lugar)
        )
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error al guardar turno: {e}")
        raise e
    finally:
        cur.close()
        conn.close()

def obtener_todos_los_medicos():
    conn = connect_to_supabase()
    cursor = conn.cursor()

    cursor.execute("SELECT id_medico, nombre, especialidad FROM Medicos ORDER BY nombre")
    medicos = cursor.fetchall()

    cursor.close()
    conn.close()

    # Retornar una lista de tuplas (id, "Nombre - Especialidad")
    return [(m[0], f"{m[1]} - {m[2]}") for m in medicos]

def obtener_lugares_por_medico(id_medico):
    conn = connect_to_supabase()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT lugar FROM Medicos WHERE id_medico = %s", (id_medico,))
    lugares = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return lugares if lugares else ["Lugar no especificado"]



def obtener_turnos_mes(año, mes, dni):
    """
    Obtiene los turnos de un mes específico para un paciente.
    CORREGIDO: Ahora selecciona y procesa correctamente la columna 'hora'.
    """
    conn = connect_to_supabase()
    if not conn: return pd.DataFrame()

    query = """
        SELECT t.id_turno, t.fecha, t.hora, m.nombre AS medico, t.lugar
        FROM Turnos t
        JOIN Pacientes p ON t.id_paciente = p.id_paciente
        JOIN Medicos m ON t.id_medico = m.id_medico
        WHERE EXTRACT(MONTH FROM t.fecha) = %s
          AND EXTRACT(YEAR FROM t.fecha) = %s
          AND p.dni = %s
        ORDER BY t.fecha, t.hora
    """
    try:
        # Usamos pd.read_sql para obtener un DataFrame directamente
        df = pd.read_sql(query, conn, params=(mes, año, dni))
        
        # Asegurarse de que las columnas de fecha y hora tengan el tipo correcto
        df['Fecha'] = pd.to_datetime(df['fecha']).dt.date
        df['Hora'] = pd.to_datetime(df['hora'].astype(str)).dt.time
        
        # Renombrar columnas para consistencia en el frontend
        df = df.rename(columns={"id_turno": "ID", "medico": "Médico", "lugar": "Lugar"})
        return df
    except Exception as e:
        st.error(f"Error al obtener turnos del mes: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

def editar_turno(id_turno, nueva_fecha, nueva_hora, nuevo_lugar):
    """
    Actualiza la fecha, hora y lugar de un turno existente.
    CORREGIDO: Ahora incluye la actualización de la columna 'hora'.
    """
    conn = connect_to_supabase()
    if not conn: return
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE Turnos SET fecha = %s, hora = %s, lugar = %s WHERE id_turno = %s",
                (nueva_fecha, nueva_hora, nuevo_lugar, id_turno)
            )
        conn.commit()
    except Exception as e:
        st.error(f"Error al editar el turno: {e}")
        conn.rollback()
    finally:
        if conn: conn.close()


