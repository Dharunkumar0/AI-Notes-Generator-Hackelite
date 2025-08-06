from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional
import logging
import time
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.core.database import get_collection
from app.services.voice_service import voice_service

logger = logging.getLogger(__name__)
router = APIRouter()

class VoiceTranscribeResponse(BaseModel):
    transcription: str
    confidence: float
    word_count: int
    processing_time: float

class VoiceMicrophoneRequest(BaseModel):
    duration: Optional[int] = 10

@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribe uploaded audio file to text."""
    try:
        start_time = time.time()
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size (10MB limit)
        file_size = 0
        audio_bytes = b""
        
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large. Maximum 10MB allowed."
                )
            audio_bytes += chunk
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Get file extension
        file_extension = file.filename.split('.')[-1].lower()
        supported_formats = voice_service.get_supported_formats()["data"]["supported_formats"]
        
        if file_extension not in supported_formats:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Process audio
        result = await voice_service.transcribe_audio_bytes(audio_bytes, file_extension)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="voice",
            input_data={
                "filename": file.filename,
                "file_size": file_size,
                "file_format": file_extension
            },
            output_data=result["data"],
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return VoiceTranscribeResponse(
            transcription=result["data"]["transcription"],
            confidence=result["data"]["confidence"],
            word_count=result["data"]["word_count"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )

@router.post("/microphone", response_model=VoiceTranscribeResponse)
async def transcribe_microphone(
    request: VoiceMicrophoneRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribe audio from microphone in real-time."""
    try:
        start_time = time.time()
        
        # Validate duration
        if request.duration < 1 or request.duration > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be between 1 and 60 seconds"
            )
        
        # Process audio
        result = await voice_service.transcribe_microphone(request.duration)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="voice_microphone",
            input_data={
                "duration": request.duration
            },
            output_data=result["data"],
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return VoiceTranscribeResponse(
            transcription=result["data"]["transcription"],
            confidence=result["data"]["confidence"],
            word_count=result["data"]["word_count"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing microphone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported audio formats."""
    return voice_service.get_supported_formats()

@router.get("/stats")
async def get_voice_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's voice processing statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get voice-related history
        voice_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": {"$in": ["voice", "voice_microphone"]}
        }).to_list(length=None)
        
        total_processed = len(voice_history)
        total_words = sum(
            item.get("output_data", {}).get("word_count", 0) 
            for item in voice_history 
            if item.get("output_data", {}).get("word_count")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in voice_history
        ) / total_processed if total_processed > 0 else 0
        
        # Count by format
        format_counts = {}
        for item in voice_history:
            if item.get("input_data", {}).get("file_format"):
                format_name = item["input_data"]["file_format"]
                format_counts[format_name] = format_counts.get(format_name, 0) + 1
        
        return {
            "total_processed": total_processed,
            "total_words": total_words,
            "average_processing_time": round(avg_processing_time, 2),
            "format_breakdown": format_counts,
            "last_processed": voice_history[-1]["created_at"] if voice_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting voice stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 