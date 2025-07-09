# fMedicamentos.py
import pandas as pd
from datetime import date
import json
from functions import execute_query
from fEncuesta import get_id_paciente_por_dni

def get_medicamentos(dni, solo_actuales=False, solo_finalizados=False, conn=None):
    """
    Obtiene los medicamentos de un paciente con información del paciente.
    """
    id_paciente = get_id_paciente_por_dni(dni, conn)
    if not id_paciente:
        return pd.DataFrame()

    query = """
        SELECT m.*, p.nombre as nombre_paciente 
        FROM medicamentos m 
        JOIN pacientes p ON m.id_paciente = p.id_paciente 
        WHERE m.id_paciente = %s AND (m.oculto IS NULL OR m.oculto = FALSE)
    """
    params = [int(id_paciente)]

    if solo_actuales:
        query += " AND (m.fecha_fin IS NULL OR m.fecha_fin > CURRENT_DATE)"
    if solo_finalizados:
        query += " AND m.fecha_fin IS NOT NULL AND m.fecha_fin <= CURRENT_DATE"
    
    query += " ORDER BY m.fecha_inicio DESC"

    return execute_query(query=query, params=params, conn=conn, is_select=True)

def insertar_medicamento(dni, droga, nombre, gramaje_mg, motivo, fecha_inicio, fecha_fin,
                         dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor,
                         stock_inicial, recordatorio, conn=None):
    """
    Inserta un nuevo medicamento con la lógica mejorada de dosis, frecuencia y recordatorios.
    """
    id_paciente = int(get_id_paciente_por_dni(dni, conn))
    stock_actual = stock_inicial if stock_inicial > 0 else None
    frecuencia_valor_json = json.dumps(frecuencia_valor) if frecuencia_valor else None
    concentracion = None

    query = """
        INSERT INTO medicamentos 
        (id_paciente, droga, nombre, gramaje_mg, concentracion, motivo, fecha_inicio, fecha_fin,
         dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor,
         stock_inicial, stock_actual, oculto, recordatorio)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE, %s)
    """
    params = (id_paciente, droga, nombre, gramaje_mg, concentracion, motivo, fecha_inicio, fecha_fin,
              dosis_cantidad, dosis_unidad, frecuencia_tipo, frecuencia_valor_json,
              stock_inicial, stock_actual, recordatorio)
    
    execute_query(query, params=params, conn=conn, is_select=False)

def formatear_dosis_texto(row):
    """
    Función helper MEJORADA para crear un texto legible a partir de datos estructurados.
    """
    try:
        cantidad = row['dosis_cantidad']
        cantidad_num = int(cantidad) if pd.notna(cantidad) else 1
        unidad = row['dosis_unidad']
        tipo_frec = row['frecuencia_tipo']
        valor_frec = row['frecuencia_valor']

        unidad_texto = unidad[:-1] if cantidad_num == 1 and unidad.endswith('s') else unidad
        dosis_texto = f"{cantidad_num} {unidad_texto}"

        if isinstance(valor_frec, str):
            valor_frec = json.loads(valor_frec)
        
        texto_frecuencia = ""
        if tipo_frec == "Cada 'X' horas":
            intervalo = valor_frec.get('intervalo_horas', '?')
            texto_frecuencia = f"cada {intervalo} horas"
        elif tipo_frec == "En horarios específicos del día":
            horas = ', '.join(valor_frec.get('horarios_dia', []))
            texto_frecuencia = f"a las {horas}" if horas else "en horarios específicos"
        elif tipo_frec == "En días específicos de la semana":
            dias = ', '.join(valor_frec.get('dias_semana', []))
            horas = ', '.join(valor_frec.get('horarios_en_dias', []))
            texto_frecuencia = f"los {dias} a las {horas}" if dias and horas else f"los {dias}" if dias else "en días específicos"
        elif tipo_frec == "texto_plano":
            texto_frecuencia = valor_frec.get('texto', '')

        return f"{dosis_texto} {texto_frecuencia}".strip()
    except Exception:
        return "Información de dosis no disponible"

def marcar_medicamento_como_finalizado(id_medicamento, conn=None):
    """
    Establece la fecha de finalización de un medicamento a hoy.
    """
    query = "UPDATE medicamentos SET fecha_fin = %s WHERE id_medicamento = %s"
    params = (date.today(), id_medicamento)
    execute_query(query, params=params, conn=conn, is_select=False)

def registrar_toma(id_medicamento, cantidad_tomada, conn=None):
    """
    Registra una toma y actualiza el stock.
    """
    query_log = "INSERT INTO tomas_medicamentos (id_medicamento, cantidad_tomada) VALUES (%s, %s)"
    params_log = (id_medicamento, cantidad_tomada)
    execute_query(query_log, params=params_log, conn=conn, is_select=False)
    
    query_stock = "UPDATE medicamentos SET stock_actual = stock_actual - %s WHERE id_medicamento = %s AND stock_actual >= %s"
    params_stock = (cantidad_tomada, id_medicamento, cantidad_tomada)
    execute_query(query_stock, params=params_stock, conn=conn, is_select=False)

def verificar_toma_hoy(id_medicamento, conn=None):
    """
    DEPRECADA - Reemplazada por contar_tomas_hoy para mayor precisión.
    """
    query = "SELECT EXISTS (SELECT 1 FROM tomas_medicamentos WHERE id_medicamento = %s AND DATE(fecha_toma) = CURRENT_DATE);"
    params = (id_medicamento,)
    result = execute_query(query, params=params, conn=conn, is_select=True)
    return result.iloc[0]['exists'] if not result.empty else False

def contar_tomas_hoy(id_medicamento, conn=None):
    """
    NUEVA FUNCIÓN: Cuenta cuántas tomas se han registrado para un medicamento en el día de hoy.
    """
    query = """
        SELECT COALESCE(SUM(cantidad_tomada), 0) as total_tomado
        FROM tomas_medicamentos 
        WHERE id_medicamento = %s AND DATE(fecha_toma) = CURRENT_DATE;
    """
    params = (id_medicamento,)
    result = execute_query(query, params=params, conn=conn, is_select=True)
    if not result.empty:
        return int(result.iloc[0]['total_tomado'])
    return 0
