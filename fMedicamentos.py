import streamlit as st
import pandas as pd
from datetime import date
from functions import execute_query
from fEncuesta import get_id_paciente_por_dni

def get_medicamentos(dni, solo_actuales=False, solo_finalizados=False, conn=None):
    id_paciente = get_id_paciente_por_dni(dni, conn)
    query = "SELECT * FROM medicamentos WHERE id_paciente = %s"
    params = [int(id_paciente)]
    if solo_actuales:
        query += " AND fin IS NULL"
    if solo_finalizados:
        query += " AND fin IS NOT NULL"
    return pd.read_sql(query, conn, params=params)

def marcar_medicamento_como_finalizado(id_medicamento, conn=None):
    query = "UPDATE medicamentos SET fin = %s WHERE id = %s"
    execute_query(query, params=(date.today(), id_medicamento), conn=conn)

def insertar_medicamento(dni, droga, nombre, laboratorio, gramaje, dosis, frecuencia, motivo, fecha_inicio, fecha_fin, conn=None):
    id_paciente = get_id_paciente_por_dni(dni, conn)
    query = """
        INSERT INTO medicamentos (id_paciente, droga, nombre, laboratorio, gramaje, dosis, frecuencia, motivo, fecha_inicio, fecha_fin)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (id_paciente, droga, nombre, laboratorio, gramaje, dosis, frecuencia, motivo, fecha_inicio, fecha_fin)
    execute_query(query, params, conn=conn)
