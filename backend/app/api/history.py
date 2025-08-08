from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from pydantic import BaseModel
from typing import Optional, List
import logging
from datetime import datetime, timedelta

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryResponse
from app.core.database import get_collection

logger = logging.getLogger(__name__)
router = APIRouter()

from bson import ObjectId

class HistoryItem(BaseModel):
    id: str
    user_id: str
    feature_type: str
    input_data: dict
    output_data: dict
    processing_time: Optional[float]
    status: str = "completed"
    created_at: datetime

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

class HistorySummary(BaseModel):
    total_items: int
    feature_breakdown: dict
    recent_activity: List[HistoryItem]
    processing_stats: dict

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True

@router.get("/", response_model=List[HistoryItem])
async def get_user_history(
    feature_type: Optional[str] = Query(None, description="Filter by feature type"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's processing history with optional filtering."""
    try:
        history_collection = get_collection("history")
        logger.info(f"Fetching history for user: {current_user.firebase_uid}, feature_type: {feature_type}, limit: {limit}, offset: {offset}")
        # Build query
        query = {"user_id": current_user.firebase_uid}
        if feature_type:
            query["feature_type"] = feature_type
        # Get history items
        cursor = history_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
        history_items = await cursor.to_list(length=limit)
        logger.info(f"Found {len(history_items)} history items for user {current_user.firebase_uid}")
        # Convert to response format
        items = []
        for item in history_items:
            try:
                history_item = HistoryItem(
                    id=str(item["_id"]),
                    user_id=item["user_id"],
                    feature_type=item["feature_type"],
                    input_data=item["input_data"],
                    output_data=item["output_data"],
                    processing_time=item.get("processing_time"),
                    status=item.get("status", "completed"),
                    created_at=item["created_at"]
                )
                items.append(history_item)
            except Exception as e:
                logger.error(f"Error converting history item: {e}, item: {item}")
                continue
        return items
    except Exception as e:
        logger.error(f"Error getting user history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history"
        )

@router.get("/summary", response_model=HistorySummary)
async def get_history_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get summary of user's processing history."""
    try:
        history_collection = get_collection("history")
        logger.info(f"Getting history summary for user: {current_user.firebase_uid}, days: {days}")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get history items in date range - use firebase_uid instead of id
        query = {
            "user_id": current_user.firebase_uid,
            "created_at": {"$gte": start_date, "$lte": end_date}
        }
        
        history_items = await history_collection.find(query).sort("created_at", -1).to_list(length=None)
        logger.info(f"Found {len(history_items)} history items for user {current_user.firebase_uid}")
        
        # Calculate feature breakdown
        feature_breakdown = {}
        total_processing_time = 0
        successful_items = 0
        
        for item in history_items:
            feature_type = item["feature_type"]
            feature_breakdown[feature_type] = feature_breakdown.get(feature_type, 0) + 1
            
            if item.get("processing_time"):
                total_processing_time += item["processing_time"]
            
            if item["status"] == "completed":
                successful_items += 1
        
        # Get recent activity (last 10 items)
        recent_items = []
        for item in history_items[:10]:
            try:
                history_item = HistoryItem(
                    id=str(item["_id"]),
                    user_id=item["user_id"],
                    feature_type=item["feature_type"],
                    input_data=item["input_data"],
                    output_data=item["output_data"],
                    processing_time=item.get("processing_time"),
                    status=item.get("status", "completed"),
                    created_at=item["created_at"]
                )
                recent_items.append(history_item)
            except Exception as e:
                logger.error(f"Error converting recent history item: {e}, item: {item}")
                continue
        
        # Calculate processing stats
        total_items = len(history_items)
        avg_processing_time = total_processing_time / total_items if total_items > 0 else 0
        success_rate = (successful_items / total_items * 100) if total_items > 0 else 0
        
        logger.info(f"Summary stats - total_items: {total_items}, success_rate: {success_rate}, avg_time: {avg_processing_time}")
        
        return HistorySummary(
            total_items=total_items,
            feature_breakdown=feature_breakdown,
            recent_activity=recent_items,
            processing_stats={
                "average_processing_time": round(avg_processing_time, 2),
                "success_rate": round(success_rate, 1),
                "total_processing_time": round(total_processing_time, 2)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting history summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve history summary"
        )

@router.get("/feature/{feature_type}")
async def get_feature_history(
    feature_type: str,
    limit: int = Query(20, ge=1, le=50, description="Number of items to return"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get history for a specific feature type."""
    try:
        history_collection = get_collection("history")
        
        # Get history items for specific feature
        query = {
            "user_id": str(current_user.id),
            "feature_type": feature_type
        }
        
        cursor = history_collection.find(query).sort("created_at", -1).limit(limit)
        history_items = await cursor.to_list(length=limit)
        
        # Convert to response format
        items = []
        for item in history_items:
            items.append(HistoryItem(
                id=str(item["_id"]),
                feature_type=item["feature_type"],
                input_data=item["input_data"],
                output_data=item["output_data"],
                processing_time=item.get("processing_time"),
                status=item["status"],
                created_at=item["created_at"]
            ))
        
        return {
            "feature_type": feature_type,
            "total_items": len(items),
            "items": items
        }
        
    except Exception as e:
        logger.error(f"Error getting feature history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feature history"
        )

@router.post("/seed-test", tags=["Debug"], include_in_schema=False)
async def seed_test_history(request: Request):
    """Temporary endpoint to seed a test history item for debugging (local dev only)."""
    try:
        history_collection = get_collection("history")
        test_item = {
            "user_id": "test-user-id",
            "feature_type": "eli5",
            "input_data": {"topic": "Test Topic", "complexity_level": "easy"},
            "output_data": {"original_topic": "Test Topic", "key_concepts_count": 2, "examples_count": 1, "analogies_count": 1},
            "processing_time": 1.23,
            "status": "completed",
            "created_at": datetime.utcnow()
        }
        result = await history_collection.insert_one(test_item)
        return {"message": "Seeded test history item", "id": str(result.inserted_id)}
    except Exception as e:
        return {"error": str(e)}

@router.post("/seed-dashboard-test", tags=["Debug"], include_in_schema=False)
async def seed_dashboard_test_data(request: Request):
    """Seed comprehensive test data for dashboard statistics testing."""
    try:
        history_collection = get_collection("history")
        
        # Create test data for different features
        test_data = [
            {
                "user_id": "test-user-id",
                "feature_type": "eli5",
                "input_data": {"topic": "Machine Learning", "complexity_level": "easy"},
                "output_data": {"original_topic": "Machine Learning", "key_concepts_count": 3, "examples_count": 2, "analogies_count": 2},
                "processing_time": 2.5,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "user_id": "test-user-id",
                "feature_type": "notes",
                "input_data": {"text": "Sample text for summarization", "max_length": 200},
                "output_data": {"summary": "Summarized text", "key_points": ["point1", "point2"], "word_count": 50},
                "processing_time": 1.8,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "user_id": "test-user-id",
                "feature_type": "quiz",
                "input_data": {"text": "Sample quiz content", "num_questions": 5},
                "output_data": {"total_questions": 5, "questions_count": 5},
                "processing_time": 3.2,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=3)
            },
            {
                "user_id": "test-user-id",
                "feature_type": "pdf",
                "input_data": {"filename": "test.pdf", "file_size": 1024000, "total_pages": 5},
                "output_data": {"word_count": 1500, "extraction_method": "pymupdf"},
                "processing_time": 4.1,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=4)
            },
            {
                "user_id": "test-user-id",
                "feature_type": "voice",
                "input_data": {"filename": "audio.mp3", "file_size": 512000, "file_format": "mp3"},
                "output_data": {"transcription": "Sample transcription", "confidence": 0.95, "word_count": 25},
                "processing_time": 2.8,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=5)
            },
            {
                "user_id": "test-user-id",
                "feature_type": "mindmap",
                "input_data": {"topic": "Artificial Intelligence", "complexity": "intermediate"},
                "output_data": {"topic": "AI", "branches_count": 4, "subtopics_count": 12},
                "processing_time": 3.5,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=6)
            }
        ]
        
        # Insert all test data
        result = await history_collection.insert_many(test_data)
        
        return {
            "message": f"Seeded {len(test_data)} dashboard test items", 
            "inserted_count": len(result.inserted_ids)
        }
    except Exception as e:
        return {"error": str(e)}

class SeedUserDataRequest(BaseModel):
    user_id: str

@router.post("/seed-user-data", tags=["Debug"], include_in_schema=False)
async def seed_user_data(request: SeedUserDataRequest):
    """Seed test data for a specific user ID."""
    try:
        history_collection = get_collection("history")
        
        # Create test data for the specified user
        test_data = [
            {
                "user_id": request.user_id,
                "feature_type": "eli5",
                "input_data": {"topic": "Machine Learning", "complexity_level": "easy"},
                "output_data": {"original_topic": "Machine Learning", "key_concepts_count": 3, "examples_count": 2, "analogies_count": 2},
                "processing_time": 2.5,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=1)
            },
            {
                "user_id": request.user_id,
                "feature_type": "notes",
                "input_data": {"text": "Sample text for summarization", "max_length": 200},
                "output_data": {"summary": "Summarized text", "key_points": ["point1", "point2"], "word_count": 50},
                "processing_time": 1.8,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "user_id": request.user_id,
                "feature_type": "quiz",
                "input_data": {"text": "Sample quiz content", "num_questions": 5},
                "output_data": {"total_questions": 5, "questions_count": 5},
                "processing_time": 3.2,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=3)
            },
            {
                "user_id": request.user_id,
                "feature_type": "pdf",
                "input_data": {"filename": "test.pdf", "file_size": 1024000, "total_pages": 5},
                "output_data": {"word_count": 1500, "extraction_method": "pymupdf"},
                "processing_time": 4.1,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=4)
            },
            {
                "user_id": request.user_id,
                "feature_type": "voice",
                "input_data": {"filename": "audio.mp3", "file_size": 512000, "file_format": "mp3"},
                "output_data": {"transcription": "Sample transcription", "confidence": 0.95, "word_count": 25},
                "processing_time": 2.8,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=5)
            },
            {
                "user_id": request.user_id,
                "feature_type": "mindmap",
                "input_data": {"topic": "Artificial Intelligence", "complexity": "intermediate"},
                "output_data": {"topic": "AI", "branches_count": 4, "subtopics_count": 12},
                "processing_time": 3.5,
                "status": "completed",
                "created_at": datetime.utcnow() - timedelta(hours=6)
            }
        ]
        
        # Insert all test data
        result = await history_collection.insert_many(test_data)
        
        return {
            "message": f"Seeded {len(test_data)} items for user {request.user_id}", 
            "inserted_count": len(result.inserted_ids)
        }
    except Exception as e:
        return {"error": str(e)}

@router.delete("/{history_id}")
async def delete_history_item(
    history_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete a specific history item."""
    try:
        from bson import ObjectId
        
        history_collection = get_collection("history")
        
        # Verify the item belongs to the user
        item = await history_collection.find_one({
            "_id": ObjectId(history_id),
            "user_id": str(current_user.id)
        })
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="History item not found"
            )
        
        # Delete the item
        await history_collection.delete_one({"_id": ObjectId(history_id)})
        
        return {"message": "History item deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting history item: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete history item"
        )

@router.delete("/")
async def clear_history(
    feature_type: Optional[str] = Query(None, description="Clear only specific feature type"),
    current_user: UserResponse = Depends(get_current_user)
):
    """Clear user's history (all or by feature type)."""
    try:
        history_collection = get_collection("history")
        
        # Build query
        query = {"user_id": str(current_user.id)}
        if feature_type:
            query["feature_type"] = feature_type
        
        # Delete items
        result = await history_collection.delete_many(query)
        
        return {
            "message": f"Cleared {result.deleted_count} history items",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear history"
        ) 