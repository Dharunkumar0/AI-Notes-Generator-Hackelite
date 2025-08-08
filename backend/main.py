from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
import os

from app.api import auth, notes, voice, pdf, quiz, mindmap, eli5, history, image, export, research
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="ThinkInk AI API",
    description="A comprehensive API for AI-powered educational tools including notes summarization, voice transcription, PDF processing, quiz generation, mind maps, and ELI5 explanations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(notes.router, prefix="/api/notes", tags=["Notes"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice"])
app.include_router(pdf.router, prefix="/api/pdf", tags=["PDF"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
app.include_router(mindmap.router, prefix="/api/mindmap", tags=["Mind Map"])
app.include_router(eli5.router, prefix="/api/eli5", tags=["ELI5"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(image.router, prefix="/api/image", tags=["Image Processing"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(research.router, prefix="/api/research", tags=["Research"])

# Serve static files (for uploaded images)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "ThinkInk AI API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 