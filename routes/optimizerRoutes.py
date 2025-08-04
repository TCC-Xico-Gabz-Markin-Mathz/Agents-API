import json
import re
from fastapi import APIRouter, Depends, HTTPException, Query
from dependencies import get_api_key
from services.llmRouter import get_llm
from models.payloadOptimizer import (
    OptimizerRequest,
    OptimizerResponse,
    CreateDatabaseRequest,
    CreateDatabaseResponse,
    PopulateDatabaseResponse,
    PopulateDatabaseRequest,
    OptimizationAnalysisRequest,
    OptimizationAnalysisResponse,
    WeightRequest,
)

router = APIRouter(
    prefix="/optimizer", tags=["Optimizer"], dependencies=[Depends(get_api_key)]
)


@router.post("/generate", response_model=OptimizerResponse)
async def optimize_query(
    request: OptimizerRequest,
    model_name: str = Query("default", description="Nome do modelo LLM a usar"),
):
    try:
        llm = get_llm(model_name)
        result = await llm.optimize_generate(
            query=request.query,
            database_structure=request.database_structure,
        )
        return OptimizerResponse(result=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-database", response_model=CreateDatabaseResponse)
async def create_db(
    request: CreateDatabaseRequest,
    model_name: str = Query("default", description="Nome do modelo LLM a usar"),
):
    try:
        llm = get_llm(model_name)
        sql = await llm.create_database(database_structure=request.database_structure)
        return CreateDatabaseResponse(sql=sql)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/populate", response_model=PopulateDatabaseResponse)
async def populate_db(request: PopulateDatabaseRequest, model_name: str = "groq"):
    try:
        sql_raw = await get_llm(model_name).populate_database(
            creation_command=request.creation_command,
            number_insertions=request.number_insertions,
        )

        cleaned = re.sub(r"```(?:json)?", "", sql_raw).strip("`\n ")

        sql_list = json.loads(cleaned)

        return PopulateDatabaseResponse(sql=sql_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=OptimizationAnalysisResponse)
async def analyze(
    request: OptimizationAnalysisRequest,
    model_name: str = Query("default", description="Nome do modelo LLM a usar"),
):
    try:
        llm = get_llm(model_name)
        result = llm.analyze_optimization_effects(
            original_metrics=request.original_metrics,
            optimized_metrics=request.optimized_metrics,
            original_query=request.original_query,
            optimized_query=request.optimized_query,
            applied_indexes=request.applied_indexes,
        )
        return OptimizationAnalysisResponse(analysis=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weights", response_model=OptimizationAnalysisResponse)
async def weights(
    request: WeightRequest,
    model_name: str = Query("default", description="Nome do modelo LLM a usar"),
):
    try:
        llm = get_llm(model_name)
        result = await llm.get_weights(ram_gb=request.ram_gb, priority=request.priority)
        # return OptimizationAnalysisResponse(analysis=result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
