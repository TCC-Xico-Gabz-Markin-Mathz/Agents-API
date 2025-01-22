from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    database_structure: str
    process: str

class RAGQueryResponse(BaseModel):
    optimized_query: str