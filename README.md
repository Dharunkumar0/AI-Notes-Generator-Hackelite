# AI-Powered Notes Summarizer

A comprehensive full-stack application that helps students automatically summarize long notes, extract text from voice or PDFs, generate quizzes, simplify complex topics, and create mind maps using AI.

## Features

- 🔐 **Authentication**: Firebase Authentication with Google sign-in and email/password
- 📝 **Notes Summarization**: AI-powered summarization of long text notes
- 🎤 **Voice-to-Text**: Convert voice recordings to text using SpeechRecognition
- 📄 **PDF Processing**: Extract and process text from PDF documents using Poppler
- ❓ **Quiz Generation**: Automatically generate quizzes from study materials
- 🧠 **Mind Map Creation**: Generate visual mind maps for complex topics
- 💡 **ELI5 (Explain Like I'm 5)**: Simplify complex topics for better understanding
- 📊 **User History**: Store and retrieve all user interactions and AI outputs
- 🎨 **Modern UI**: Beautiful React interface with Tailwind CSS
- 🌙 **Dark Mode**: Full dark mode support throughout the application

## Tech Stack

### Frontend
- **React 18** with JavaScript (JSX)
- **Tailwind CSS** for styling with dark mode support
- **Firebase Authentication** for user management
- **Axios** for API communication
- **React Router** for navigation
- **React Hot Toast** for notifications
- **Lucide React** for icons

### Backend
- **FastAPI** (Python) for REST API
- **Gemini 2.5 Flash Pro** for AI tasks
- **SpeechRecognition** for voice processing
- **Poppler** for PDF parsing
- **MongoDB** for data storage
- **Pydantic** for data validation
- **Uvicorn** for ASGI server

## Project Structure

```
HACKELITE/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API and Firebase services
│   │   ├── contexts/       # React contexts (Auth, Theme)
│   │   └── utils/          # Utility functions
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── backend/                 # FastAPI backend application
│   ├── app/
│   │   ├── api/            # API route handlers
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Utility functions
│   ├── requirements.txt    # Python dependencies
│   └── main.py            # FastAPI application entry point
├── docs/                   # Documentation
└── README.md              # Project documentation
```

## Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- MongoDB (local or cloud)
- Google Cloud Project with Gemini API enabled
- Firebase project for authentication

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Environment Variables

#### Frontend (.env)
```env
REACT_APP_API_BASE_URL=http://localhost:8000
REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
REACT_APP_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your_project_id
REACT_APP_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
REACT_APP_FIREBASE_APP_ID=your_app_id
```

#### Backend (.env)
```env
SECRET_KEY=your_secret_key_here
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=notes_summarizer
FIREBASE_API_KEY=your_firebase_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
GEMINI_API_KEY=your_gemini_api_key
```

## API Endpoints

- `POST /api/auth/login` - User authentication
- `POST /api/notes/summarize` - Summarize text notes
- `POST /api/voice/transcribe` - Convert voice to text
- `POST /api/pdf/extract` - Extract text from PDF
- `POST /api/quiz/generate` - Generate quizzes
- `POST /api/mindmap/create` - Create mind maps
- `POST /api/eli5/simplify` - Simplify complex topics
- `GET /api/history` - Get user history

## Dark Mode

The application includes comprehensive dark mode support:
- Automatic system preference detection
- Manual toggle with theme persistence
- Consistent dark styling across all components
- Smooth transitions between light and dark themes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details 