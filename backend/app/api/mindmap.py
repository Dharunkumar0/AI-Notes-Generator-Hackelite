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

class MindMapCreateRequest(BaseModel):
    topic: str
    subtopics: Optional[List[str]] = None

class MindMapBranch(BaseModel):
    name: str
    subtopics: List[dict]

class MindMapCreateResponse(BaseModel):
    topic: str
    branches: List[MindMapBranch]
    processing_time: float

@router.post("/create", response_model=MindMapCreateResponse)
async def create_mindmap(
    request: MindMapCreateRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a mind map structure for a topic using AI."""
    try:
        start_time = time.time()
        
        # Validate input
        if not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )
        
        if len(request.topic) > 500:  # 500 char limit for topic
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic too long. Maximum 500 characters allowed."
            )
        
        if request.subtopics and len(request.subtopics) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many subtopics. Maximum 10 subtopics allowed."
            )
        
        # Process with AI
        result = await ai_service.create_mindmap(request.topic, request.subtopics)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Mind map creation failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="mindmap",
            input_data={
                "topic": request.topic,
                "subtopics": request.subtopics or []
            },
            output_data={
                "topic": result["data"]["topic"],
                "branches_count": len(result["data"]["branches"])
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        # Convert branches to response format
        branches = []
        for branch in result["data"]["branches"]:
            branches.append(MindMapBranch(
                name=branch["name"],
                subtopics=branch["subtopics"]
            ))
        
        return MindMapCreateResponse(
            topic=result["data"]["topic"],
            branches=branches,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating mind map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mind map"
        )

@router.get("/stats")
async def get_mindmap_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's mind map creation statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get mindmap-related history
        mindmap_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": "mindmap"
        }).to_list(length=None)
        
        total_created = len(mindmap_history)
        total_branches = sum(
            item.get("output_data", {}).get("branches_count", 0) 
            for item in mindmap_history 
            if item.get("output_data", {}).get("branches_count")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in mindmap_history
        ) / total_created if total_created > 0 else 0
        
        # Average branches per mind map
        avg_branches_per_mindmap = total_branches / total_created if total_created > 0 else 0
        
        # Get unique topics
        unique_topics = set()
        for item in mindmap_history:
            topic = item.get("input_data", {}).get("topic", "")
            if topic:
                unique_topics.add(topic)
        
        return {
            "total_mindmaps_created": total_created,
            "total_branches": total_branches,
            "average_branches_per_mindmap": round(avg_branches_per_mindmap, 1),
            "unique_topics": len(unique_topics),
            "average_processing_time": round(avg_processing_time, 2),
            "last_created": mindmap_history[-1]["created_at"] if mindmap_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting mindmap stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 