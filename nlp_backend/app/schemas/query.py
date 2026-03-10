from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class QueryRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    message: str = "Success"
    thought: Optional[str] = None
    confidence: float = 0.0
    chart_image: Optional[str] = None
    chart_spec: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = 0.1

class FeedbackRequest(BaseModel):
    message_id: str
    status: str
    how: Optional[str] = None
