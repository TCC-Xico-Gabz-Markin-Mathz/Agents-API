import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

SUPABASE_USER = os.getenv("SUPABASE_USER")
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")


def connect():
    try:
        client = QdrantClient(host='localhost', port=6333)
        if client:
            print("Conexão estabelecida com sucesso.")
        return client
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise e