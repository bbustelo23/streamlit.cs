import pandas as pd
import numpy as np
from functions import execute_query, connect_to_supabase
from fEncuesta import obtener_edad

def load_medical_profiles():
    """Carga todos los perfiles médicos de referencia desde la base de datos."""
    try:
        conn = connect_to_supabase()
        query = "SELECT * FROM perfiles_medicos"
        df = execute_query(query, conn=conn, is_select=True)
        return df
    except Exception as e:
        print(f"Error cargando perfiles médicos: {e}")
        return pd.DataFrame()

def load_user_medical_history(dni, conn):
    """
    Carga el historial médico completo del usuario actual.
    CORREGIDO: Se asegura de que el DNI se use como un número para la búsqueda,
    evitando errores de tipo de dato.
    """
    try:
        # 1. Convertir DNI a entero para la búsqueda en la base de datos.
        # Esta es la corrección clave para resolver el problema.
        dni_int = int(dni)

        # 2. Buscar id_paciente directamente usando el DNI como número.
        id_query = "SELECT id_paciente FROM pacientes WHERE dni = %s"
        df_id = execute_query(id_query, params=(dni_int,), conn=conn, is_select=True)
        
        if df_id.empty:
            print(f"DEBUG: No se encontró paciente con DNI: {dni_int}")
            return None
        
        id_paciente = int(df_id.iloc[0]['id_paciente'])

        # 3. Buscar historial con el id_paciente encontrado.
        historial_query = "SELECT * FROM historial_medico WHERE id_paciente = %s LIMIT 1"
        df_historial = execute_query(historial_query, params=(id_paciente,), conn=conn, is_select=True)
        
        if not df_historial.empty:
            data_numpy = df_historial.iloc[0].to_dict()
            # Convertir tipos de NumPy a tipos nativos de Python
            data = {key: (value.item() if hasattr(value, 'item') else value) for key, value in data_numpy.items()}
            data['edad'] = obtener_edad(id_paciente, conn)
            return data
        else:
            print(f"DEBUG: Se encontró id_paciente ({id_paciente}), pero no hay datos en historial_medico.")
            return None
            
    except Exception as e:
        print(f"Error cargando historial médico del usuario: {e}")
        return None

def map_user_profile_to_comparison(user_data):
    """Mapea los datos del usuario a un formato estandarizado para la comparación."""
    if not user_data:
        return {}
    
    return {
        'edad': user_data.get('edad'),
        'actividad_fisica': user_data.get('actividad_fisica', False),
        'fumador': user_data.get('fumador', False),
        'alcohol_frecuente': user_data.get('alcoholico', False),
        'antecedentes_familiares_cancer': 'cancer' in (user_data.get('antecedentes_familiares_enfermedad') or '').lower(),
        'antecedentes_familiares_diabetes': 'diabetes' in (user_data.get('antecedentes_familiares_enfermedad') or '').lower(),
        'antecedentes_familiares_hipertension': 'hipertension' in (user_data.get('antecedentes_familiares_enfermedad') or '').lower(),
        'presion_arterial_alta': user_data.get('colesterol_alto', False),
        'colesterol_alto': user_data.get('colesterol_alto', False),
        'estres_alto': user_data.get('estres_alto', False)
    }

def calculate_similarity(user_profile, disease_profiles):
    """
    Calcula la similitud y devuelve el porcentaje y los factores de coincidencia.
    """
    similarities = []
    all_factors = []

    characteristics = [
        ('actividad_fisica', 'Actividad Física'), ('fumador', 'Fumador'), 
        ('alcohol_frecuente', 'Consume Alcohol'), ('presion_arterial_alta', 'Presión Alta'),
        ('colesterol_alto', 'Colesterol Alto'), ('estres_alto', 'Estrés Alto'),
        ('antecedentes_familiares_cancer', 'Ant. Fam. Cáncer'), 
        ('antecedentes_familiares_diabetes', 'Ant. Fam. Diabetes'), 
        ('antecedentes_familiares_hipertension', 'Ant. Fam. Hipertensión')
    ]

    for _, profile in disease_profiles.iterrows():
        matches = 0
        total_characteristics = 0
        factors = []

        for key, name in characteristics:
            user_val = user_profile.get(key)
            profile_val = profile.get(key)
            if user_val is not None and profile_val is not None:
                match = (user_val == profile_val)
                if match:
                    matches += 1
                factors.append({
                    'factor': name,
                    'tu_perfil': "Sí" if user_val else "No",
                    'perfil_riesgo': "Sí" if profile_val else "No",
                    'coincide': "✅" if match else "❌"
                })
                total_characteristics += 1
        
        if total_characteristics > 0:
            similarity_percentage = (matches / total_characteristics) * 100
            similarities.append(similarity_percentage)
            all_factors.extend(factors)

    avg_similarity = np.mean(similarities) if similarities else 0
    
    if all_factors:
        df_factors = pd.DataFrame(all_factors)
        final_factors = df_factors.groupby('factor').agg({
            'tu_perfil': 'first',
            'perfil_riesgo': lambda x: x.mode()[0] if not x.mode().empty else 'N/A',
            'coincide': lambda x: "✅" if (x == "✅").any() else "❌"
        }).reset_index()
    else:
        final_factors = pd.DataFrame(columns=['factor', 'tu_perfil', 'perfil_riesgo', 'coincide'])

    return avg_similarity, final_factors
