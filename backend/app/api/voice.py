from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Security
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, constr, Field
from typing import Optional, List, Dict, Any
import logging
import time
import os
import json
import traceback
from datetime import datetime
import base64
import speech_recognition as sr
from werkzeug.utils import secure_filename

from app.api.auth import get_current_user, verify_firebase_token
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.services.voice_service import voice_service

from app.services.text_to_speech_service import text_to_speech_service

# Add missing router definition
router = APIRouter()
from app.core.config import settings
from app.core.database import get_collection

security = HTTPBearer()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Models
class VoiceTranscribeResponse(BaseModel):
    success: bool = Field(description="Whether the transcription was successful")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Transcription data if successful")
    error: Optional[str] = Field(default=None, description="Error message if unsuccessful")

class MicrophoneInfo(BaseModel):
    index: int = Field(description="Index of the microphone device")
    name: str = Field(description="Name of the microphone device")

class VoiceSummarizeRequest(BaseModel):
    transcription: str
    max_length: Optional[int] = 200

class VoiceSummarizeResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None



# Text-to-Speech endpoint
class TextToSpeechRequest(BaseModel):
    text: str
    language: str = 'en'
    translate: bool = False

@router.post("/text-to-speech")
async def text_to_speech(request: TextToSpeechRequest):
    """Convert text to speech and return audio file path."""
    result = await text_to_speech_service.text_to_speech(
        text=request.text,
        language=request.language,
        translate=request.translate
    )
    if result["success"]:
        return {"success": True, "data": result["data"]}
    else:
        return {"success": False, "error": result["error"]}

@router.post("/transcribe", response_model=VoiceTranscribeResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Transcribe uploaded audio file to text."""
    temp_file_path = None
    try:
        # Verify token and get user info
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Get file extension and validate format
        file_ext = os.path.splitext(file.filename)[1][1:].lower()
        if not file_ext:
            raise HTTPException(status_code=400, detail="File must have an extension")
            
        # Check supported formats
        supported_formats = voice_service.supported_formats
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_ext}. Supported formats: {', '.join(supported_formats)}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > voice_service.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {voice_service.max_file_size // (1024*1024)}MB"
            )
        
        # Reset file pointer and save to temp file
        await file.seek(0)
        
        # Create secure filename and temp path
        secure_name = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)
        temp_file_path = os.path.join("uploads", "temp", f"{timestamp}_{secure_name}")
        
        # Ensure temp directory exists
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)
        
        # Save file
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file_content)

        # Process the audio file using voice service
        result = await voice_service.transcribe_audio_file(temp_file_path, file_ext)
        
        if not result.get("success"):
            return VoiceTranscribeResponse(
                success=False,
                error=result.get("error", "Transcription failed")
            )

        return VoiceTranscribeResponse(
            success=True,
            data=result["data"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing audio file: {str(e)}\n{traceback.format_exc()}")
        return VoiceTranscribeResponse(
            success=False,
            error=f"Error processing audio file: {str(e)}"
        )
    finally:
        # Cleanup temp files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Error cleaning up temp file: {e}")

@router.post("/microphone", response_model=VoiceTranscribeResponse)
async def transcribe_microphone(
    duration: int = Form(10),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Transcribe audio from microphone in real-time."""
    try:
        # Verify token
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Validate duration
        if duration < 1 or duration > 60:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duration must be between 1 and 60 seconds"
            )
        
        # Process microphone audio
        result = await voice_service.transcribe_microphone(duration)
        
        if not result.get("success"):
            return VoiceTranscribeResponse(
                success=False,
                error=result.get("error", "Microphone transcription failed")
            )
        
        return VoiceTranscribeResponse(
            success=True,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transcribing microphone: {e}")
        return VoiceTranscribeResponse(
            success=False,
            error=f"Microphone transcription failed: {str(e)}"
        )

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported audio formats."""
    try:
        return voice_service.get_supported_formats()
    except Exception as e:
        logger.error(f"Error getting formats: {e}")
        return {
            "success": True,
            "data": {
                "supported_formats": ["wav", "mp3", "m4a", "ogg", "flac"],
                "max_file_size": 10 * 1024 * 1024,
                "max_file_size_mb": "10MB"
            }
        }

@router.post("/summarize", response_model=VoiceSummarizeResponse)
async def summarize_transcription(
    request: VoiceSummarizeRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Generate a summary of transcribed audio content."""
    try:
        # Verify token
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Validate input
        if not request.transcription.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transcription cannot be empty"
            )
        
        # Generate summary
        result = await voice_service.summarize_audio(
            request.transcription, 
            request.max_length
        )
        
        if not result.get("success"):
            return VoiceSummarizeResponse(
                success=False,
                error=result.get("error", "Summary generation failed")
            )
        
        return VoiceSummarizeResponse(
            success=True,
            data=result["data"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error summarizing transcription: {e}")
        return VoiceSummarizeResponse(
            success=False,
            error=f"Summary generation failed: {str(e)}"
        )

@router.get("/microphones", response_model=List[MicrophoneInfo])
async def get_microphones(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get list of available microphones"""
    try:
        # Verify token
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
        microphones = voice_service.get_available_microphones()
        return [MicrophoneInfo(index=idx, name=name) for idx, name in enumerate(microphones)]
    except Exception as e:
        logger.error(f"Error getting microphones: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting microphones: {str(e)}"
        )

@router.post("/record")
async def record_audio(
    device_index: Optional[int] = Form(None),
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Record audio from selected microphone"""
    try:
        # Verify token
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
            
        # Record audio using voice service with optional device index
        audio_file = await voice_service.record_audio(device_index=device_index)
        
        # Return the path to recorded audio
        return JSONResponse({
            "success": True,
            "audioPath": audio_file
        })
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "error": f"Error recording audio: {str(e)}"
        })

@router.get("/stats")
async def get_voice_stats(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Get user's voice processing statistics."""
    try:
        # Verify token
        firebase_user = await verify_firebase_token(credentials.credentials)
        if not firebase_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # This would typically fetch from database
        # For now, return mock stats
        return {
            "success": True,
            "data": {
                "total_processed": 0,
                "total_words": 0,
                "average_processing_time": 0,
                "format_breakdown": {},
                "last_processed": None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voice stats: {e}")
        return {
            "success": False,
            "error": "Failed to get statistics"
        }