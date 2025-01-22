from pydantic import BaseModel
from typing import Optional, Dict, Any, List


class ContextIn(BaseModel):
    id: Optional[int] = None
    vector: Optional[List[float]] = None  
    payload: Optional[Dict[str, Any]] = None  


class ContextOut(BaseModel):
    id: Optional[int] = None
    score: Optional[float] = None  
    payload: Optional[Dict[str, Any]] = None  
