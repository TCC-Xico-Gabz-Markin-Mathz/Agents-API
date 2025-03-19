from datetime import timedelta
from typing import Annotated, Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import get_api_key
from services.context import get_sql_query_with_database_structure
from models.payloadRAG import RAGQueryRequest, RAGQueryResponse

router = APIRouter(prefix="/rag", tags=["Query"], dependencies=[Depends(get_api_key)])

@router.post("/query/structure", response_model=RAGQueryResponse)
async def query_rag(request: RAGQueryRequest):
    try:
        query = await get_sql_query_with_database_structure(
            database_structure=request.database_structure,
            order=request.order
        )
        return RAGQueryResponse(query=query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar RAG: {str(e)}")