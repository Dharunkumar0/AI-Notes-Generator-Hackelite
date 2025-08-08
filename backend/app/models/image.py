from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId
from .user import PyObjectId

class ImageProcessRequest(BaseModel):
    """Request model for image processing."""
    pass  # File upload handled by FastAPI

class ImageProcessResponse(BaseModel):
    """Response model for image processing."""
    id: str
    user_id: str
    filename: str
    extracted_text: str
    summary: Dict[str, Any]
    word_count: int
    character_count: int
    processing_time: Optional[float] = None
    status: str = "completed"
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class ImageHistoryItem(BaseModel):
    """Model for storing image processing history."""
    user_id: str
    filename: str
    extracted_text: str
    summary: Dict[str, Any]
    word_count: int
    character_count: int
    processing_time: Optional[float] = None
    status: str = "completed"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class ImageHistoryInDB(ImageHistoryItem):
    """Model for image history stored in database."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
