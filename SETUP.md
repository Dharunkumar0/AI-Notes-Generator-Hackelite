# AI-Powered Notes Summarizer - Setup Guide

## Overview
This application provides AI-powered tools for processing and summarizing various types of content including text notes, voice recordings, PDF documents, images, and more.

## Features
- **Notes Summarizer**: AI-powered text summarization
- **Voice to Text**: Speech recognition and transcription
- **PDF Processor**: Extract and process text from PDFs
- **Image OCR**: Extract text from images and generate summaries
- **Quiz Generator**: Create quizzes from study materials
- **Mind Map Creator**: Generate visual mind maps
- **ELI5 Simplifier**: Simplify complex topics
- **History**: Track all processing activities
- **User Authentication**: Firebase-based authentication

## Prerequisites

### System Requirements
- Python 3.8+
- Node.js 16+
- MongoDB
- Tesseract OCR (for image processing)

### API Keys Required
- Firebase API Key
- Google Gemini API Key

## Installation

### 1. Backend Setup

#### Install Python Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Install Tesseract OCR
**Windows:**
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install to `C:\Program Files\Tesseract-OCR\`
3. Add to PATH environment variable

**macOS:**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

#### Environment Configuration
```bash
cp env.example .env
```

Edit `.env` file with your API keys:
```env
# Firebase Configuration
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=notes_summarizer

# Security
SECRET_KEY=your-secret-key-here
```

#### Start Backend Server
```bash
cd backend
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`

### 2. Frontend Setup

#### Install Node.js Dependencies
```bash
cd frontend
npm install
```

#### Environment Configuration
```bash
cp env.example .env
```

Edit `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_FIREBASE_API_KEY=your-firebase-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
```

#### Start Frontend Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user
- `PUT /api/auth/profile` - Update user profile

### Notes Processing
- `POST /api/notes/summarize` - Summarize text notes

### Voice Processing
- `POST /api/voice/transcribe` - Transcribe audio files

### PDF Processing
- `POST /api/pdf/process` - Process PDF files

### Image Processing
- `POST /api/image/process` - Process images (OCR + summarization)
- `GET /api/image/history` - Get image processing history
- `GET /api/image/history/{id}` - Get specific image processing detail
- `DELETE /api/image/history/{id}` - Delete image processing record
- `DELETE /api/image/history` - Clear all image history

### Quiz Generation
- `POST /api/quiz/generate` - Generate quizzes

### Mind Map Creation
- `POST /api/mindmap/create` - Create mind maps

### ELI5 Simplification
- `POST /api/eli5/simplify` - Simplify complex topics

### History
- `GET /api/history` - Get processing history
- `GET /api/history/summary` - Get history summary
- `DELETE /api/history/{id}` - Delete history item
- `DELETE /api/history` - Clear all history

## Database Collections

The application uses MongoDB with the following collections:
- `users` - User information
- `history` - Processing history for all features
- `image_history` - Image processing history

## Security Features

- JWT-based authentication
- Firebase authentication integration
- File upload validation
- CORS configuration
- Input sanitization
- Rate limiting (configurable)

## File Upload Limits

- **Images**: 10MB max, supports JPG, PNG, and other image formats
- **Audio**: 10MB max, supports MP3, WAV, and other audio formats
- **PDFs**: 10MB max

## Troubleshooting

### Common Issues

1. **Tesseract not found**
   - Ensure Tesseract is installed and in PATH
   - For Windows, verify installation path in `image_service.py`

2. **CORS errors**
   - Check CORS configuration in `main.py`
   - Verify frontend URL is in allowed origins

3. **Authentication errors**
   - Verify Firebase configuration
   - Check JWT token expiration

4. **API key errors**
   - Ensure all required API keys are set in `.env`
   - Verify Gemini API key is valid

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export LOG_LEVEL=DEBUG
```

## Development

### Backend Development
- FastAPI with automatic API documentation
- Available at `http://localhost:8000/docs`

### Frontend Development
- React with Tailwind CSS
- Hot reload enabled
- Component-based architecture

## Deployment

### Backend Deployment
1. Set production environment variables
2. Use production WSGI server (e.g., Gunicorn)
3. Configure reverse proxy (e.g., Nginx)

### Frontend Deployment
1. Build production bundle: `npm run build`
2. Serve static files
3. Configure API URL for production

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## License

This project is licensed under the MIT License. 