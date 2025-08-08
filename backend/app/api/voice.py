from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import time
import os
import json
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.models.voice import EmotionAnalysisResponse
from app.core.database import get_collection
from app.services.voice_service import voice_service
from app.services.emotion_analysis_service import analyze_voice_emotion
from app.core.config import settings
import logging
import time
import os
import json
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.models.voice import EmotionAnalysisResponse
from app.core.database import get_collection
from app.services.voice_service import voice_service
from app.services.emotion_analysis_service import analyze_voice_emotion
from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

class TimestampModel(BaseModel):
    word: str
    start_time: float
    end_time: float

class VoiceTranscribeResponse(BaseModel):
    transcription: str
    confidence: float
    word_count: int
    processing_time: float
    duration: Optional[float] = None
    timestamps: Optional[List[TimestampModel]] = None
    file_path: Optional[str] = None

class VoiceSummarizeResponse(BaseModel):
    summary: str
    main_points: List[str]
    word_count: int
    key_phrases: List[str]
    action_items: Optional[List[str]] = None
    context: str
    processing_time: float

class VoiceAnalysisResponse(BaseModel):
    summary: str
    key_points: List[str]
    topics_discussed: List[str]
    sentiment: str
    sentiment_reasons: List[str]
    clarity_score: int
    suggested_improvements: List[str]
    processing_time: float

class VoiceMicrophoneRequest(BaseModel):
    duration: Optional[int] = 10
    save_recording: Optional[bool] = True

class VoiceSummarizeRequest(BaseModel):
    transcription: str
    max_length: Optional[int] = 200

@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio_file(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Transcribe uploaded audio file to text."""
    temp_file_path = None
    try:
        start_time = time.time()
        logger.debug(f"Starting audio transcription for file: {file.filename}")
        
        # Validate file
        if not file.filename:
            logger.error("No file name provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
            
        # Check file size before reading
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        file_size = 0
        chunk_size = 8192
        
        # Read file in chunks to check size
        while chunk := await file.read(chunk_size):
            file_size += len(chunk)
            if file_size > MAX_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds 10MB limit"
                )
            
        # Reset file position for later reading
        await file.seek(0)
        
        # Get file extension
        file_extension = file.filename.split('.')[-1].lower()
        supported_formats = voice_service.get_supported_formats()["data"]["supported_formats"]
        
        if file_extension not in supported_formats:
            logger.error(f"Unsupported format: {file_extension}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Create temporary directories if they don't exist
        for dir_path in [
            os.path.join(os.getcwd(), "uploads"),
            os.path.join(os.getcwd(), "uploads", "temp"),
            os.path.join(os.getcwd(), "uploads", "audio")
        ]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Generate unique temp file path
        timestamp = int(time.time() * 1000)
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
        temp_file_path = os.path.join(
            os.getcwd(), 
            "uploads", 
            "temp", 
            f"upload_{timestamp}_{safe_filename}"
        )
        
        logger.debug(f"Saving uploaded file to: {temp_file_path}")
        
        # Save uploaded file
        file_size = 0
        try:
            with open(temp_file_path, "wb") as temp_file:
                while chunk := await file.read(8192):
                    file_size += len(chunk)
                    if file_size > 10 * 1024 * 1024:  # 10MB
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File too large. Maximum 10MB allowed."
                        )
                    temp_file.write(chunk)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error saving file: {str(e)}"
            )
        
        if file_size == 0:
            logger.error("Empty file uploaded")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        logger.debug(f"File saved successfully. Size: {file_size} bytes")
        
        # Check if file exists and is readable
        if not os.path.exists(temp_file_path):
            logger.error(f"Saved file not found: {temp_file_path}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error saving file"
            )
        
        # Process audio
        try:
            result = await voice_service.transcribe_audio_file(temp_file_path, file_extension)
        except Exception as e:
            logger.error(f"Error during transcription: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during transcription: {str(e)}"
            )
        
        if not result["success"]:
            logger.error(f"Transcription failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Transcription failed: {result.get('error', 'Unknown error')}"
            )
        
        processing_time = time.time() - start_time
        logger.debug(f"Transcription completed in {processing_time:.2f} seconds")
            
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
        
        # Add processing time to result
        result["data"]["processing_time"] = processing_time
        return result["data"]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing audio file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Removed temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file: {str(e)}")

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

@router.post("/summarize", response_model=VoiceSummarizeResponse)
async def summarize_transcription(
    request: VoiceSummarizeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate a summary of transcribed audio content."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.transcription.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription cannot be empty"
            )
        
        # Process with AI
        result = await voice_service.summarize_audio(
            request.transcription, 
            request.max_length
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Summarization failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Add processing time to the result
        result["data"]["processing_time"] = processing_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="voice_summary",
            input_data={
                "transcription_length": len(request.transcription.split()),
                "max_length": request.max_length
            },
            output_data={
                "summary_length": len(result["data"]["summary"].split()),
                "main_points_count": len(result["data"]["main_points"])
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return result["data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to summarize transcription"
        )

@router.post("/analyze", response_model=VoiceAnalysisResponse)
async def analyze_transcription(
    request: VoiceSummarizeRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Analyze transcribed audio content for key points and sentiment."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.transcription.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription cannot be empty"
            )
        
        # Process with AI
        result = await voice_service.analyze_audio_content(request.transcription)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Analysis failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Add processing time to the result
        result["data"]["processing_time"] = processing_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="voice_analysis",
            input_data={
                "transcription_length": len(request.transcription.split())
            },
            output_data={
                "sentiment": result["data"]["sentiment"],
                "clarity_score": result["data"]["clarity_score"],
                "topics_count": len(result["data"]["topics_discussed"])
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return result["data"]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing transcription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze transcription"
        )

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