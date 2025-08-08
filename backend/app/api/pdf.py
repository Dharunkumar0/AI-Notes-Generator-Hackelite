from fastapi import APIRouter, HTTPException, Depends, status, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
import logging
import time
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.models.history import HistoryCreate
from app.core.database import get_collection
from app.services.pdf_service import pdf_service

logger = logging.getLogger(__name__)
router = APIRouter()

class PDFExtractResponse(BaseModel):
    text: str
    pages: List[dict]
    total_pages: int
    word_count: int
    extraction_method: str
    processing_time: float

class PDFInfoResponse(BaseModel):
    total_pages: int
    title: str
    author: str
    subject: str
    creator: str
    producer: str
    creation_date: str
    modification_date: str

@router.post("/extract", response_model=PDFExtractResponse)
async def extract_pdf_text(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Extract text from uploaded PDF file."""
    try:
        start_time = time.time()
        
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )
        
        # Check file size (10MB limit)
        file_size = 0
        pdf_bytes = b""
        
        while chunk := await file.read(8192):
            file_size += len(chunk)
            if file_size > 10 * 1024 * 1024:  # 10MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File too large. Maximum 10MB allowed."
                )
            pdf_bytes += chunk
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Process PDF
        result = await pdf_service.extract_text_combined(pdf_bytes)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"PDF processing failed: {result['error']}"
            )
        
        processing_time = time.time() - start_time
        
        # Save to history
        history_data = HistoryCreate(
            user_id=str(current_user.id),
            feature_type="pdf",
            input_data={
                "filename": file.filename,
                "file_size": file_size,
                "total_pages": result["data"]["total_pages"]
            },
            output_data={
                "word_count": result["data"]["word_count"],
                "extraction_method": result["data"]["extraction_method"]
            },
            processing_time=processing_time
        )
        
        history_collection = get_collection("history")
        await history_collection.insert_one(history_data.dict(by_alias=True))
        
        return PDFExtractResponse(
            text=result["data"]["text"],
            pages=result["data"]["pages"],
            total_pages=result["data"]["total_pages"],
            word_count=result["data"]["word_count"],
            extraction_method=result["data"]["extraction_method"],
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting PDF text: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract PDF text"
        )

@router.post("/info", response_model=PDFInfoResponse)
async def get_pdf_info(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get basic information about uploaded PDF file."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a PDF"
            )
        
        # Read file
        pdf_bytes = await file.read()
        
        if len(pdf_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Empty file"
            )
        
        # Get PDF info
        result = await pdf_service.get_pdf_info(pdf_bytes)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get PDF info: {result['error']}"
            )
        
        return PDFInfoResponse(**result["data"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get PDF information"
        )

@router.get("/formats")
async def get_supported_formats():
    """Get list of supported PDF features."""
    return pdf_service.get_supported_formats()

@router.get("/stats")
async def get_pdf_stats(current_user: UserResponse = Depends(get_current_user)):
    """Get user's PDF processing statistics."""
    try:
        history_collection = get_collection("history")
        
        # Get PDF-related history
        pdf_history = await history_collection.find({
            "user_id": str(current_user.id),
            "feature_type": "pdf"
        }).to_list(length=None)
        
        total_processed = len(pdf_history)
        total_words = sum(
            item.get("output_data", {}).get("word_count", 0) 
            for item in pdf_history 
            if item.get("output_data", {}).get("word_count")
        )
        total_pages = sum(
            item.get("input_data", {}).get("total_pages", 0) 
            for item in pdf_history 
            if item.get("input_data", {}).get("total_pages")
        )
        avg_processing_time = sum(
            item.get("processing_time", 0) 
            for item in pdf_history
        ) / total_processed if total_processed > 0 else 0
        
        # Count by extraction method
        method_counts = {}
        for item in pdf_history:
            method = item.get("output_data", {}).get("extraction_method", "unknown")
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            "total_processed": total_processed,
            "total_words": total_words,
            "total_pages": total_pages,
            "average_processing_time": round(avg_processing_time, 2),
            "extraction_methods": method_counts,
            "last_processed": pdf_history[-1]["created_at"] if pdf_history else None
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        ) 