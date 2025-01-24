from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")


def llm_connect():
    try:
        client = Groq(api_key=api_key)
        if client:
            print("Conexão LLM estabelecida com sucesso.")
        return client
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        raise e