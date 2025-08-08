from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class HistoryBase(BaseModel):
    user_id: str
    feature_type: str  # notes, voice, pdf, quiz, mindmap, eli5
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    processing_time: Optional[float] = None
    status: str = "completed"  # completed, failed, processing

class HistoryCreate(HistoryBase):
    pass

class HistoryInDB(HistoryBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class HistoryResponse(HistoryBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str} 