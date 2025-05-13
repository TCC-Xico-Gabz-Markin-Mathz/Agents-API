from fastapi import HTTPException
from typing import List
from sentence_transformers import SentenceTransformer

from services.db import connect
from services.groq import llm_connect
from models.llmModel import ContextOut

model = SentenceTransformer('all-mpnet-base-v2')

def transform_vector(vector: str) -> List[float]:
    return model.encode([vector])[0]

async def retrieve_context(query: str) -> List[ContextOut]:
    contexts: List[ContextOut] = []
    query_vector = transform_vector(query)
    
    try:
        client = connect() 
        results = client.search(
            collection_name="rag_queries",
            query_vector=query_vector.tolist(),
            limit=2
        )
        
        for result in results:
            contexts.append(ContextOut(id=result.id, score=result.score, payload=result.payload))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar contexto: {str(e)}")
    
    return contexts

async def get_sql_query_with_database_structure(database_structure: str, order: str) -> str:
    client = llm_connect()

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Você é um assistente especializado em SQL. "
                        f"Com base na seguinte estrutura de banco de dados:\n\n{database_structure}\n\n"
                        f"Gere uma única query SQL que atenda exatamente à seguinte solicitação do usuário. "
                        f"Retorne apenas a query SQL, sem explicações ou texto adicional."
                    ),
                },
                {
                    "role": "user",
                    "content": order,
                },
            ],
            model="gemma2-9b-it",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro no processamento da query com LLM: {str(e)}"
        )

async def get_result_interpretation(result: str, order: str) -> str:
    client = llm_connect()

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Você é um assistente especializado em SQL. "
                        f"Com base na seguinte pergunta do usuario: {order}"
                        f"Formate a resposta gerada pelo banco ao realizar a query de uma forma em linguagem natural."
                        f"Retorne apenas a resposta para o usuario, sem explicação."
                    ),
                },
                {
                    "role": "user",
                    "content": result,
                },
            ],
            model="gemma2-9b-it",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro no processamento da query com LLM: {str(e)}")
        
async def optimize_generate(query: str, database_structure: str) -> str:
    client = llm_connect()

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente especializado em SQL e otimização de desempenho de queries. A seguir, você receberá:\n\n"
                        "- A estrutura do banco de dados.\n"
                        "- Uma query SQL que precisa ser otimizada.\n\n"
                        "Sua tarefa é:\n"
                        "1. Analisar a query em relação à estrutura do banco.\n"
                        "2. Sugerir comandos de otimização, como criação de índices, caso aplicável.\n"
                        "3. Reescrever a query de forma otimizada.\n\n"
                        "Retorne sem explicação (Somente a lista) uma **lista Python** com os seguintes elementos:\n"
                        "- Um ou mais comandos CREATE INDEX (caso necessário).\n"
                        "- A query otimizada.\n\n"
                        "Formato de exemplo:\n"
                        "['CREATE INDEX idx_cliente_id ON pedidos(cliente_id);', 'SELECT * FROM pedidos WHERE cliente_id = 123;']\n\n"
                        "Caso nenhum índice seja necessário, retorne apenas:\n"
                        "['<query otimizada>']\n\n"
                        f"Estrutura do banco de dados:\n{database_structure}\n\n"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Query original:\n{query}",
                },
            ],
            model="gemma2-9b-it",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro no processamento da query com LLM: {str(e)}"
        )

async def create_database(database_structure: str) -> str:
    client = llm_connect()

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um assistente especializado em bancos de dados relacionais. "
                        "Sua tarefa é converter uma descrição de estrutura de banco de dados em comandos SQL do tipo DDL (Data Definition Language), como CREATE TABLE.\n\n"
                        "Considere tipos de dados apropriados, chaves primárias, estrangeiras e restrições se estiverem descritas.\n\n"
                        "Retorne **apenas os comandos SQL necessários** para criar as tabelas e relacionamentos descritos em ordem para criar (Atentar-se para não mandar criar uma chave estrangeira onde não exista a tabela).\n\n"
                        "Exemplo de resposta esperada:\n"
                        "CREATE TABLE clientes (\n"
                        "    id INT PRIMARY KEY,\n"
                        "    nome VARCHAR(255),\n"
                        "    email VARCHAR(255) UNIQUE\n"
                        ");\n\n"
                        "CREATE TABLE pedidos (\n"
                        "    id INT PRIMARY KEY,\n"
                        "    cliente_id INT,\n"
                        "    data DATE,\n"
                        "    FOREIGN KEY (cliente_id) REFERENCES clientes(id)\n"
                        ");"
                    ),
                },
                {
                    "role": "user",
                    "content": database_structure,
                },
            ],
            model="gemma2-9b-it",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Erro no processamento da estrutura do banco com LLM: {str(e)}"
        )
        
def analyze_optimization_effects(
    original_metrics: dict,
    optimized_metrics: dict,
    original_query: str,
    optimized_query: str,
    applied_indexes: list
) -> str:
    client = llm_connect()

    try:
        system_prompt = (
            "Você é um especialista em performance de banco de dados. "
            "Abaixo estão os resultados de execução de duas queries (original e otimizada) e os índices aplicados. "
            "Sua tarefa é avaliar se as otimizações devem ser mantidas com base nos resultados, "
            "considerando tempo, planos de execução e eficiência.\n\n"
            "Diga de forma clara e objetiva se vale a pena manter as mudanças. "
            "Considere possíveis riscos, ganhos marginais, impacto em outros tipos de consulta, e explique a decisão.\n\n"
            "Responda com uma análise técnica e objetiva."
        )

        user_prompt = (
            f"Query original:\n{original_query}\n\n"
            f"Métricas da query original:\n{original_metrics}\n\n"
            f"Query otimizada:\n{optimized_query}\n\n"
            f"Métricas da query otimizada:\n{optimized_metrics}\n\n"
            f"Índices aplicados:\n{applied_indexes}"
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model="gemma2-9b-it",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao avaliar efeitos da otimização com LLM: {str(e)}"
        )

