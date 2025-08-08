from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from typing import List
import time
import logging
from datetime import datetime
from bson import ObjectId

from app.models.image import ImageProcessResponse, ImageHistoryItem
from app.models.user import UserResponse
from app.services.image_service import ImageService
from app.core.database import get_collection
from app.api.auth import get_current_user

router = APIRouter(tags=["Image Processing"])
logger = logging.getLogger(__name__)

# Initialize image service with error handling
image_service = ImageService()
IMAGE_SERVICE_AVAILABLE = True

@router.post("/process", response_model=ImageProcessResponse)
async def process_image(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Process uploaded image: extract text and generate summary."""
    if not IMAGE_SERVICE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Image processing service is not available. Please check server configuration."
        )
    
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image (JPG, PNG, etc.)"
            )
        
        # Check file size (max 10MB)
        file_size = 0
        image_data = b""
        for chunk in file.file:
            file_size += len(chunk)
            image_data += chunk
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size too large. Maximum size is 10MB."
                )
        
        logger.info(f"Processing image for user {current_user.firebase_uid}: {file.filename}")
        
        # Start timing
        start_time = time.time()
        
        # Process image
        result = await image_service.process_image(image_data, file.filename)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create history item
        history_item = ImageHistoryItem(
            user_id=current_user.firebase_uid,
            filename=file.filename,
            extracted_text=result["extracted_text"],
            summary=result["summary"],
            word_count=result["word_count"],
            character_count=result["character_count"],
            processing_time=processing_time,
            status="completed",
            created_at=datetime.utcnow()
        )
        
        # Store in database
        image_collection = get_collection("image_history")
        db_result = await image_collection.insert_one(history_item.dict())
        
        # Create response
        response = ImageProcessResponse(
            id=str(db_result.inserted_id),
            user_id=current_user.firebase_uid,
            filename=file.filename,
            extracted_text=result["extracted_text"],
            summary=result["summary"],
            word_count=result["word_count"],
            character_count=result["character_count"],
            processing_time=processing_time,
            status="completed",
            created_at=history_item.created_at
        )
        
        logger.info(f"Successfully processed image for user {current_user.firebase_uid}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )

@router.get("/history", response_model=List[ImageProcessResponse])
async def get_image_history(
    limit: int = 20,
    offset: int = 0,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's image processing history."""
    try:
        image_collection = get_collection("image_history")
        
        # Get history items
        cursor = image_collection.find(
            {"user_id": current_user.firebase_uid}
        ).sort("created_at", -1).skip(offset).limit(limit)
        
        history_items = await cursor.to_list(length=limit)
        
        # Convert to response format
        items = []
        for item in history_items:
            response_item = ImageProcessResponse(
                id=str(item["_id"]),
                user_id=item["user_id"],
                filename=item["filename"],
                extracted_text=item["extracted_text"],
                summary=item["summary"],
                word_count=item["word_count"],
                character_count=item["character_count"],
                processing_time=item.get("processing_time"),
                status=item.get("status", "completed"),
                created_at=item["created_at"]
            )
            items.append(response_item)
        
        return items
        
    except Exception as e:
        logger.error(f"Error getting image history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image history"
        )

@router.get("/history/{image_id}", response_model=ImageProcessResponse)
async def get_image_detail(
    image_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get specific image processing detail."""
    try:
        image_collection = get_collection("image_history")
        
        # Get specific item
        item = await image_collection.find_one({
            "_id": ObjectId(image_id),
            "user_id": current_user.firebase_uid
        })
        
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image processing record not found"
            )
        
        response_item = ImageProcessResponse(
            id=str(item["_id"]),
            user_id=item["user_id"],
            filename=item["filename"],
            extracted_text=item["extracted_text"],
            summary=item["summary"],
            word_count=item["word_count"],
            character_count=item["character_count"],
            processing_time=item.get("processing_time"),
            status=item.get("status", "completed"),
            created_at=item["created_at"]
        )
        
        return response_item
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve image detail"
        )

@router.delete("/history/{image_id}")
async def delete_image_record(
    image_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Delete specific image processing record."""
    try:
        image_collection = get_collection("image_history")
        
        # Delete item
        result = await image_collection.delete_one({
            "_id": ObjectId(image_id),
            "user_id": current_user.firebase_uid
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image processing record not found"
            )
        
        return {"message": "Image processing record deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image processing record"
        )

@router.delete("/history")
async def clear_image_history(
    current_user: UserResponse = Depends(get_current_user)
):
    """Clear all image processing history for user."""
    try:
        image_collection = get_collection("image_history")
        
        # Delete all items for user
        result = await image_collection.delete_many({
            "user_id": current_user.firebase_uid
        })
        
        return {
            "message": f"Cleared {result.deleted_count} image processing records"
        }
        
    except Exception as e:
        logger.error(f"Error clearing image history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear image history"
        )
