import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

qdrant_host = os.getenv("QDRANT_HOST", "localhost")
qdrant_port = os.getenv("QDRANT_PORT", 6333)


def connect():
    try:
        client = QdrantClient(host=qdrant_host, port=qdrant_port)
        if client:
            print("Conexão estabelecida com sucesso.")
        return client
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise e