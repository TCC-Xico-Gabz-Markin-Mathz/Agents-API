from fastapi import HTTPException
from typing import List, Optional
from sentence_transformers import SentenceTransformer

from services.db import connect
from services.groq import llm_connect
from models.contextModel import ContextOut

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

async def rag_process(database_structure: str, query: str, process: str) -> str:
    contexts = await retrieve_context(query)
    
    if not contexts:
        raise HTTPException(
            status_code=404, 
            detail="Nenhum contexto relevante foi encontrado para a query fornecida."
        )
    
    client = llm_connect()
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Contexto: {contexts[0].payload} "
                        f"+ Considere a seguinte estrutura do banco de dados: {database_structure}. "
                        f"{process}"
                    ),
                },
                {
                    "role": "user",
                    "content": query,
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
