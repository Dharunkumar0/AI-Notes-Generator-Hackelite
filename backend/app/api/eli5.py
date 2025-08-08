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

logger = logging.getLogger(__name__)
router = APIRouter()

class ELI5SimplifyRequest(BaseModel):
    topic: str
    complexity_level: Optional[str] = "basic"  # basic, intermediate, advanced

class ELI5SimplifyResponse(BaseModel):
    original_topic: str
    simple_explanation: str
    key_concepts: List[str]
    examples: List[str]
    analogies: List[str]
    processing_time: float

@router.post("/simplify", response_model=ELI5SimplifyResponse)
async def simplify_topic(
    request: ELI5SimplifyRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Simplify complex topics using ELI5 (Explain Like I'm 5) approach."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )
        
        if len(request.topic) > 1000:  # 1KB limit for topic
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic too long. Maximum 1,000 characters allowed."
            )
        
        valid_complexity_levels = ["basic", "intermediate", "advanced"]
        if request.complexity_level not in valid_complexity_levels:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid complexity level. Must be one of: {', '.join(valid_complexity_levels)}"
            )
        
        # Process with AI
        result = await ai_service.simplify_topic(request.topic, request.complexity_level)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Topic simplification failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="eli5",
            input_data={
                "topic": request.topic,
                "complexity_level": request.complexity_level
            },
            output_data={
                "original_topic": result["data"]["original_topic"],
                "key_concepts_count": len(result["data"]["key_concepts"]),
                "examples_count": len(result["data"]["examples"]),
                "analogies_count": len(result["data"]["analogies"])
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return ELI5SimplifyResponse(
            original_topic=result["data"]["original_topic"],
            simple_explanation=result["data"]["simple_explanation"],
            key_concepts=result["data"]["key_concepts"],
            examples=result["data"]["examples"],
            analogies=result["data"]["analogies"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error simplifying topic: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to simplify topic"
        )

@router.get("/complexity-levels")
async def get_complexity_levels():
    """Get available complexity levels for ELI5."""
    return {
        "complexity_levels": [
            {
                "value": "basic",
                "description": "Simple explanations suitable for beginners or young learners"
            },
            {
                "value": "intermediate",
                "description": "Moderate complexity explanations for students with some background knowledge"
            },
            {
                "value": "advanced",
                "description": "Detailed explanations for advanced learners while still maintaining clarity"
            }
        ]
    }

@router.get("/stats")
async def get_eli5_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's ELI5 simplification statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get ELI5-related history
        eli5_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": "eli5"
        }).to_list(length=None)
        
        total_simplified = len(eli5_history)
        total_concepts = sum(
            item.get("output_data", {}).get("key_concepts_count", 0) 
            for item in eli5_history 
            if item.get("output_data", {}).get("key_concepts_count")
        )
        total_examples = sum(
            item.get("output_data", {}).get("examples_count", 0) 
            for item in eli5_history 
            if item.get("output_data", {}).get("examples_count")
        )
        total_analogies = sum(
            item.get("output_data", {}).get("analogies_count", 0) 
            for item in eli5_history 
            if item.get("output_data", {}).get("analogies_count")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in eli5_history
        ) / total_simplified if total_simplified > 0 else 0
        
        # Count by complexity level
        complexity_counts = {}
        for item in eli5_history:
            level = item.get("input_data", {}).get("complexity_level", "unknown")
            complexity_counts[level] = complexity_counts.get(level, 0) + 1
        
        # Get unique topics
        unique_topics = set()
        for item in eli5_history:
            topic = item.get("input_data", {}).get("topic", "")
            if topic:
                unique_topics.add(topic)
        
        return {
            "total_topics_simplified": total_simplified,
            "total_concepts_explained": total_concepts,
            "total_examples_provided": total_examples,
            "total_analogies_used": total_analogies,
            "unique_topics": len(unique_topics),
            "complexity_breakdown": complexity_counts,
            "average_processing_time": round(avg_processing_time, 2),
            "last_simplified": eli5_history[-1]["created_at"] if eli5_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting ELI5 stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 