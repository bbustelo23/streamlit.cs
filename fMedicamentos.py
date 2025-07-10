# fMedicamentos.py
import pandas as pd
from datetime import date
import json
from functions import execute_query
from fEncuesta import get_id_paciente_por_dni

def get_medicamentos(dni, solo_actuales=False, solo_finalizados=False, conn=None):
    """
    Obtiene los medicamentos de un paciente con información del paciente.
    MEJORADO: Excluye medicamentos ocultos por defecto.
    """
    id_paciente = get_id_paciente_por_dni(dni, conn)
    if not id_paciente:
        return pd.DataFrame()

    # MEJORADO: JOIN con tabla pacientes + filtro de medicamentos no ocultos
    query = """
        SELECT m.*, p.nombre as nombre_paciente 
        FROM medicamentos m 
        JOIN pacientes p ON m.id_paciente = p.id_paciente 
        WHERE m.id_paciente = %s AND (m.oculto IS NULL OR m.oculto = FALSE)
    """
    params = [int(id_paciente)]

    if solo_actuales:
        # Un medicamento está activo si:
        # 1. No tiene fecha_fin (tratamiento indefinido)
        # 2. O tiene fecha_fin pero es futura (aún no terminó)
        query += " AND (m.fecha_fin IS NULL OR m.fecha_fin > CURRENT_DATE)"
        
    if solo_finalizados:
        # Un medicamento está finalizado si tiene fecha_fin y es pasada o presente
        query += " AND m.fecha_fin IS NOT NULL AND m.fecha_fin <= CURRENT_DATE"
    
    query += " ORDER BY m.fecha_inicio DESC"

    return execute_query(query=query, params=params, conn=conn, is_select=True)

def marcar_medicamento_como_finalizado(id_medicamento, conn=None):
    """
    Establece la fecha de finalización de un medicamento a hoy.
    """
    query = "UPDATE medicamentos SET fecha_fin = %s WHERE id_medicamento = %s"
    params = (date.today(), id_medicamento)
    execute_query(query, params=params, conn=conn, is_select=False)

def ocultar_medicamento(id_medicamento, conn=None):
    """
    NUEVA FUNCIÓN: Marca un medicamento como oculto (soft delete).
    No se elimina de la base de datos, solo se oculta de la vista.
    """
    query = "UPDATE medicamentos SET oculto = TRUE WHERE id_medicamento = %s"
    params = (id_medicamento,)
    execute_query(query, params=params, conn=conn, is_select=False)

def mostrar_medicamento(id_medicamento, conn=None):
    """
    NUEVA FUNCIÓN: Restaura un medicamento oculto para que vuelva a ser visible.
    """
    query = "UPDATE medicamentos SET oculto = FALSE WHERE id_medicamento = %s"
    params = (id_medicamento,)
    execute_query(query, params=params, conn=conn, is_select=False)

def get_medicamentos_ocultos(dni, conn=None):
    """
    NUEVA FUNCIÓN: Obtiene todos los medicamentos ocultos de un paciente.
    Útil para una futura página de "Papelera" o "Medicamentos Ocultos".
    """
    id_paciente = get_id_paciente_por_dni(dni, conn)
    if not id_paciente:
        return pd.DataFrame()

    query = """
        SELECT m.*, p.nombre as nombre_paciente 
        FROM medicamentos m 
        JOIN pacientes p ON m.id_paciente = p.id_paciente 
        WHERE m.id_paciente = %s AND m.oculto = TRUE
        ORDER BY m.fecha_inicio DESC
    """
    params = [int(id_paciente)]
    return execute_query(query=query, params=params, conn=conn, is_select=True)

def registrar_toma(id_medicamento, cantidad_tomada, conn=None):
    """
    Resta la cantidad tomada del stock actual de un medicamento.
    """
    query = "UPDATE medicamentos SET stock_actual = stock_actual - %s WHERE id_medicamento = %s AND stock_actual > 0"
    params = (cantidad_tomada, id_medicamento)
    execute_query(query, params=params, conn=conn, is_select=False)

def insertar_medicamento(dni, droga, nombre, gramaje_mg, concentracion, motivo, fecha_inicio, fecha_fin,
                         dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor,
                         stock_inicial, conn=None):
    """
    Inserta un nuevo medicamento con la lógica mejorada de tipo y frecuencia.
    """
    id_paciente = int(get_id_paciente_por_dni(dni, conn))
    stock_actual = stock_inicial if stock_inicial > 0 else None
    frecuencia_valor_json = json.dumps(frecuencia_valor) if frecuencia_valor else None

    query = """
        INSERT INTO medicamentos 
        (id_paciente, droga, nombre, gramaje_mg, concentracion, motivo, fecha_inicio, fecha_fin,
         dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor,
         stock_inicial, stock_actual, oculto)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
    """
    params = (id_paciente, droga, nombre, gramaje_mg, concentracion, motivo, fecha_inicio, fecha_fin,
              dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor_json,
              stock_inicial, stock_actual)
    
    execute_query(query, params=params, conn=conn, is_select=False)

def formatear_dosis_texto(row):
    """
    Función helper MEJORADA para crear un texto legible.
    """
    try:
        cantidad = row['dosis_cantidad']
        unidad = row['dosis_unidad']
        tipo_frec = row['frecuencia_tipo']
        valor_frec = row['frecuencia_valor']

        if isinstance(valor_frec, str):
            valor_frec = json.loads(valor_frec)
        
        texto_frecuencia = ""
        if tipo_frec == "Cada 'X' horas":
            intervalo = valor_frec.get('intervalo_horas', '?')
            texto_frecuencia = f"cada {intervalo} horas"
            
        elif tipo_frec == "En horarios específicos del día":
            horas = ', '.join(valor_frec.get('horarios_dia', []))
            texto_frecuencia = f"a las {horas}" if horas else ""

        elif tipo_frec == "En días específicos de la semana":
            dias = ', '.join(valor_frec.get('dias_semana', []))
            horas = ', '.join(valor_frec.get('horarios_en_dias', []))
            if dias and horas:
                texto_frecuencia = f"los {dias} a las {horas}"
            elif dias:
                texto_frecuencia = f"los {dias}"
            else:
                texto_frecuencia = ""
        
        return f"{cantidad} {unidad} {texto_frecuencia}".strip()
    except Exception as e:
        return "Información de dosis no disponible"