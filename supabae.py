
import psycopg2
def connect_to_supabase():
    try:
        conn = psycopg2.connect(
            host="tu_host.supabase.co",
            database="postgres",
            user="tu_usuario",
            password="tu_contraseña",
            port=5432  # Asegurate de que sea un número, no un string
        )
        return conn
    except Exception as e:
        print(f"Error connecting to Supabase database: {e}")
        return None
    
    