from pydantic import BaseModel


class InterpreterQueryRequest(BaseModel):
    order: str
    result: str

class InterpreterQueryResponse(BaseModel):
    response: str