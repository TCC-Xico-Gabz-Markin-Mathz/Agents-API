from datetime import timedelta
from typing import Annotated, Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import get_api_key
from services.context import rag_process
from models.payloadRAG import RAGQueryRequest, RAGQueryResponse

router = APIRouter(prefix="/rag", tags=["Query"], dependencies=[Depends(get_api_key)])

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    try:
        optimized_query = await rag_process(
            database_structure=request.database_structure,
            query=request.query,
            process=request.process
        )
        return RAGQueryResponse(optimized_query=optimized_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar RAG: {str(e)}")