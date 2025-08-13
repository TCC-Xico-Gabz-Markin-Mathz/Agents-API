from pydantic import BaseModel
from typing import List, Dict


class OptimizerRequest(BaseModel):
    query: str
    database_structure: str


class OptimizerResponse(BaseModel):
    result: List[str]


class CreateDatabaseRequest(BaseModel):
    database_structure: str


class CreateDatabaseResponse(BaseModel):
    sql: List[str]


class PopulateDatabaseResponse(BaseModel):
    sql: List[str]


class PopulateDatabaseRequest(BaseModel):
    creation_commands: list
    number_insertions: int


class OptimizationAnalysisRequest(BaseModel):
    original_metrics: Dict
    optimized_metrics: Dict
    original_query: str
    optimized_query: str
    applied_indexes: List[str]


class OptimizationAnalysisResponse(BaseModel):
    analysis: str


class WeightRequest(BaseModel):
    ram_gb: int = None
    priority: str = None


class WeightResponse(BaseModel):
    result: Dict


class OrderTablesRequest(BaseModel):
    creation_commands: List[str]