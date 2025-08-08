from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, List
import logging
import time
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.core.database import get_collection
from app.services.ai_service import ai_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class QuizGenerateRequest(BaseModel):
    text: str
    num_questions: Optional[int] = 5

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizGenerateResponse(BaseModel):
    questions: List[QuizQuestion]
    total_questions: int
    processing_time: float

@router.post("/generate", response_model=QuizGenerateResponse)
async def generate_quiz(
    request: QuizGenerateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate quiz questions from text using AI."""
    try:
        start_time = time.time()
        logger.debug(f"Starting quiz generation for user {current_user.id}")
        
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
        
        if request.num_questions < 1 or request.num_questions > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of questions must be between 1 and 20"
            )
        
        # Check if Gemini API key is configured
        if not settings.gemini_api_key:
            logger.error("Gemini API key not configured")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI service not properly configured. Please check GEMINI_API_KEY in environment variables."
            )
        
        # Process with AI
        logger.debug("Calling AI service to generate quiz")
        result = await ai_service.generate_quiz(request.text, request.num_questions)
        
        if not result["success"]:
            logger.error(f"Quiz generation failed: {result['error']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Quiz generation failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="quiz",
            input_data={
                "text": request.text[:1000],  # Store first 1000 chars
                "num_questions": request.num_questions
            },
            output_data={
                "total_questions": result["data"]["total_questions"],
                "questions_count": len(result["data"]["questions"])
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        # Convert questions to response format
        questions = []
        for q in result["data"]["questions"]:
            questions.append(QuizQuestion(
                question=q["question"],
                options=q["options"],
                correct_answer=q["correct_answer"],
                explanation=q["explanation"]
            ))
        
        return QuizGenerateResponse(
            questions=questions,
            total_questions=result["data"]["total_questions"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz"
        )

@router.get("/stats")
async def get_quiz_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's quiz generation statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get quiz-related history
        quiz_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": "quiz"
        }).to_list(length=None)
        
        total_generated = len(quiz_history)
        total_questions = sum(
            item.get("output_data", {}).get("total_questions", 0) 
            for item in quiz_history 
            if item.get("output_data", {}).get("total_questions")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in quiz_history
        ) / total_generated if total_generated > 0 else 0
        
        # Average questions per quiz
        avg_questions_per_quiz = total_questions / total_generated if total_generated > 0 else 0
        
        return {
            "total_quizzes_generated": total_generated,
            "total_questions": total_questions,
            "average_questions_per_quiz": round(avg_questions_per_quiz, 1),
            "average_processing_time": round(avg_processing_time, 2),
            "last_generated": quiz_history[-1]["created_at"] if quiz_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting quiz stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 