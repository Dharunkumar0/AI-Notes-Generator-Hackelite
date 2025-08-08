from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EmotionAnalysisResponse(BaseModel):
    primary_emotion: str
    emotion_scores: dict
    context: str
    suggestions: List[str]
    additional_notes: Optional[str] = None
    processing_time: float
    analysis_timestamp: datetime = datetime.now()
