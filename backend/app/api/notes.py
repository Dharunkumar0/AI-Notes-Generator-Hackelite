from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import logging
import time
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate, HistoryInDB
from app.core.database import get_collection
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)
router = APIRouter()

class NotesSummarizeRequest(BaseModel):
    text: str
    max_length: Optional[int] = 500
    summarization_type: Optional[str] = 'abstractive'
    summary_mode: Optional[str] = 'narrative'
    use_blooms_taxonomy: Optional[bool] = False
    use_blooms_taxonomy: Optional[bool] = False

class NotesSummarizeResponse(BaseModel):
    summary: str
    key_points: list
    word_count: int
    processing_time: float

class NotesExtractRequest(BaseModel):
    text: str

class NotesExtractResponse(BaseModel):
    key_points: list
    important_facts: list
    main_ideas: list
    vocabulary: list

@router.post("/summarize", response_model=NotesSummarizeResponse)
async def summarize_notes(
    request: NotesSummarizeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Summarize long text notes using AI."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        if len(request.text) > 10000:  # 10KB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text too long. Maximum 10,000 characters allowed."
            )
        
        # Validate summarization type
        if request.summarization_type not in ['abstractive', 'extractive']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summarization type. Must be 'abstractive' or 'extractive'"
            )
            
        # Validate summary mode
        if request.summary_mode not in ['narrative', 'beginner', 'technical', 'bullet']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary mode. Must be 'narrative', 'beginner', 'technical', or 'bullet'"
            )
        
        try:
            # Process with AI
            result = await ai_service.summarize_notes(
                text=request.text,
                max_length=request.max_length,
                summarization_type=request.summarization_type,
                summary_mode=request.summary_mode
            )
            
            if not result or not isinstance(result, dict):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from AI service"
                )
            
            if not result.get("success", False):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"AI processing failed: {result.get('error', 'Unknown error')}"
                )
            
            summary_data = result.get("data")
            if not summary_data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="No summary data in AI response"
                )
            
            processing_time = time.time() - start_time
            
            # Create response object with defaults for missing fields
            response = NotesSummarizeResponse(
                summary=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points", []),
                word_count=summary_data.get("word_count", 0),
                processing_time=processing_time
            )
        except Exception as e:
            logger.error(f"Error summarizing notes: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="notes",
            input_data={
                "text": request.text[:1000],  # Store first 1000 chars
                "max_length": request.max_length
            },
            output_data=summary_data,
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return NotesSummarizeResponse(
            summary=result["data"]["summary"],
            key_points=result["data"]["key_points"],
            word_count=result["data"]["word_count"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to summarize notes"
        )

@router.post("/extract", response_model=NotesExtractResponse)
async def extract_key_points(
    request: NotesExtractRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Extract key points and important information from text."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text cannot be empty"
            )
        
        if len(request.text) > 10000:  # 10KB limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text too long. Maximum 10,000 characters allowed."
            )
        
        # Process with AI
        result = await ai_service.extract_key_points(request.text)
        
        if not result["success"]:
            error_message = result.get("error", "Unknown error occurred")
            logger.error(f"AI processing failed: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI processing failed: {error_message}"
            )
        
        # Validate AI response structure
        if not result.get("data"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service returned invalid response structure"
            )
            
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="notes_extract",
            input_data={
                "text": request.text[:1000]  # Store first 1000 chars
            },
            output_data=result["data"],
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return NotesExtractResponse(
            key_points=result["data"]["key_points"],
            important_facts=result["data"]["important_facts"],
            main_ideas=result["data"]["main_ideas"],
            vocabulary=result["data"]["vocabulary"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting key points: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract key points"
        )

@router.get("/stats")
async def get_notes_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's notes processing statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get notes-related history
        notes_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": {"$in": ["notes", "notes_extract"]}
        }).to_list(length=None)
        
        total_processed = len(notes_history)
        total_words = sum(
            item.get("output_data", {}).get("word_count", 0) 
            for item in notes_history 
            if item.get("output_data", {}).get("word_count")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in notes_history
        ) / total_processed if total_processed > 0 else 0
        
        return {
            "total_processed": total_processed,
            "total_words": total_words,
            "average_processing_time": round(avg_processing_time, 2),
            "last_processed": notes_history[-1]["created_at"] if notes_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting notes stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 