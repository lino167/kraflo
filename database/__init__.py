from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, logging

# Variável global para a instância do cliente Supabase.
db_client: Client | None = None

def get_db() -> Client:
    """
    Inicializa e/ou retorna a instância do cliente Supabase.
    Garante que a conexão seja estabelecida apenas uma vez (padrão Singleton).
    """
    global db_client
    if db_client is None:
        try:
            logging.info("A inicializar a conexão com o Supabase...")
            db_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logging.info("Conexão com o Supabase estabelecida com sucesso.")
        except Exception as e:
            logging.error(f"Falha ao conectar com o Supabase: {e}")
            raise e
    return db_client