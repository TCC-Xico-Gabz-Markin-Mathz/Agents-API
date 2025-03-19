from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    order: str
    database_structure: str

class RAGQueryResponse(BaseModel):
    query: str