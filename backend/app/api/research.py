from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime

from app.api.auth import get_current_user
from app.models.user import UserResponse
from app.core.database import get_collection
from app.services.research_service import research_service

logger = logging.getLogger(__name__)
router = APIRouter()

class ResearchSearchRequest(BaseModel):
    topic: str
    num_papers: Optional[int] = 5
    summarization_type: Optional[str] = 'abstractive'
    summary_mode: Optional[str] = 'technical'

class ResearchPaperResponse(BaseModel):
    title: str
    authors: List[str]
    year: str
    citations: int
    abstract: str
    url: str
    venue: str
    summary: dict
    citations_format: dict

class ResearchSearchResponse(BaseModel):
    papers: List[ResearchPaperResponse]
    comparative_analysis: Optional[dict]

@router.post("/search", response_model=ResearchSearchResponse)
async def search_research_papers(
    request: ResearchSearchRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Search and analyze research papers."""
    try:
        # Validate input
        if not request.topic.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search topic cannot be empty"
            )

        # Validate summarization options
        if request.summarization_type not in ['abstractive', 'extractive']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summarization type"
            )

        if request.summary_mode not in ['narrative', 'beginner', 'technical', 'bullet']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid summary mode"
            )

        # Search for papers
        papers = await research_service.search_papers(request.topic, request.num_papers)
        
        if not papers:
            return ResearchSearchResponse(
                papers=[],
                comparative_analysis=None,
                message="No papers found. Try modifying your search terms or increasing the number of papers."
            )

        # Process each paper
        processed_papers = []
        for paper in papers:
            try:
                # Generate summary if abstract is available
                summary = await research_service.generate_summary(
                    paper['abstract'],
                    request.summarization_type,
                    request.summary_mode
                ) if paper['abstract'] else {
                    "summary": "Abstract not available for summarization.",
                    "key_findings": ["Unable to extract key findings without abstract."],
                    "methodology": "Not available",
                    "implications": "Not available"
                }

                # Generate citations
                citations = research_service.generate_citations(paper)

                # Combine all information
                processed_paper = {
                    **paper,
                    'summary': summary,
                    'citations_format': citations
                }
                processed_papers.append(processed_paper)
            except Exception as e:
                logger.error(f"Error processing paper {paper.get('title')}: {str(e)}")
                continue

        # Generate comparative analysis if multiple papers
        comparative_analysis = None
        if len(processed_papers) > 1:
            try:
                comparative_analysis = await research_service.generate_comparative_analysis(
                    papers,
                    request.summarization_type,
                    request.summary_mode
                )
            except Exception as e:
                logger.error(f"Error generating comparative analysis: {str(e)}")

        # Save to database
        try:
            search_record = {
                "user_id": str(current_user.id),
                "topic": request.topic,
                "timestamp": datetime.utcnow(),
                "papers": processed_papers,
                "comparative_analysis": comparative_analysis,
                "preferences": {
                "summarization_type": request.summarization_type,
                    "summary_mode": request.summary_mode,
                    "num_papers": request.num_papers
                }
            }

            research_collection = get_collection("research_history")
            await research_collection.insert_one(search_record)
        except Exception as e:
            logger.error(f"Error saving to database: {str(e)}")

        return ResearchSearchResponse(
            papers=processed_papers,
            comparative_analysis=comparative_analysis,
            message="Successfully retrieved and analyzed papers."
        )    
    except Exception as e:
        logger.error(f"Error in research paper search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process research papers: {str(e)}"
        )

@router.get("/history", response_model=List[dict])
async def get_research_history(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user's research search history."""
    try:
        research_collection = get_collection("research_history")
        history = await research_collection.find(
            {"user_id": str(current_user.id)}
        ).sort("timestamp", -1).to_list(length=100)
        
        return history
    except Exception as e:
        logger.error(f"Error fetching research history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch research history"
        )
