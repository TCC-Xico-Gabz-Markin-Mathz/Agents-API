from pydantic import BaseModel


class RAGQueryRequest(BaseModel):
    query: str
    database_structure: str

class RAGQueryResponse(BaseModel):
    query: str