from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DocumentSearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResult(BaseModel):
    content: str
    metadata: dict
    similarity_score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int
