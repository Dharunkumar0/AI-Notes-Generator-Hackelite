# AI-Powered Notes Summarizer - Setup Guide

This guide will help you set up the complete AI-Powered Notes Summarizer project with both frontend and backend components.

## Prerequisites

Before starting, ensure you have the following installed:

- **Node.js 18+** and npm
- **Python 3.9+** and pip
- **MongoDB** (local installation or MongoDB Atlas account)
- **Google Cloud Project** with Gemini API enabled
- **Firebase Project** for authentication

## Project Structure

```
HACKELITE/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API and Firebase services
│   │   ├── contexts/       # React contexts
│   │   └── ...
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
└── README.md              # Project documentation
```

## Step 1: Backend Setup

### 1.1 Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 1.2 Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your actual values:

```env
# API Configuration
SECRET_KEY=your-secret-key-here-change-this-in-production
API_V1_STR=/api/v1
PROJECT_NAME=AI-Powered Notes Summarizer

# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=notes_summarizer

# Firebase Configuration
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=123456789
FIREBASE_APP_ID=your-app-id

# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# File Upload Configuration
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760  # 10MB in bytes

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# Security Configuration
ACCESS_TOKEN_EXPIRE_MINUTES=30
ALGORITHM=HS256
```

### 1.3 Set Up MongoDB

**Option A: Local MongoDB**
```bash
# Install MongoDB locally
# Start MongoDB service
mongod
```

**Option B: MongoDB Atlas**
- Create a free MongoDB Atlas account
- Create a new cluster
- Get your connection string
- Update `MONGODB_URL` in `.env`

### 1.4 Set Up Google Gemini API

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the key to your `.env` file as `GEMINI_API_KEY`

### 1.5 Set Up Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication with Google and Email/Password providers
4. Get your Firebase configuration
5. Add the configuration to your `.env` file

### 1.6 Start the Backend Server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## Step 2: Frontend Setup

### 2.1 Install Node.js Dependencies

```bash
cd frontend
npm install
```

### 2.2 Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your actual values:

```env
# API Configuration
REACT_APP_API_BASE_URL=http://localhost:8000

# Firebase Configuration
REACT_APP_FIREBASE_API_KEY=your-firebase-api-key
REACT_APP_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
REACT_APP_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=123456789
REACT_APP_FIREBASE_APP_ID=your-app-id

# App Configuration
REACT_APP_NAME=AI Notes Summarizer
REACT_APP_VERSION=1.0.0
```

### 2.3 Start the Frontend Development Server

```bash
cd frontend
npm start
```

The application will be available at `http://localhost:3000`

## Step 3: Testing the Setup

### 3.1 Test Backend API

1. Visit `http://localhost:8000/docs` to see the API documentation
2. Test the health endpoint: `http://localhost:8000/health`

### 3.2 Test Frontend

1. Open `http://localhost:3000` in your browser
2. You should see the login page
3. Try creating an account or signing in with Google

### 3.3 Test Features

1. **Notes Summarizer**: Go to `/notes` and try summarizing some text
2. **Voice to Text**: Go to `/voice` and test audio transcription
3. **PDF Processor**: Go to `/pdf` and test PDF text extraction
4. **Quiz Generator**: Go to `/quiz` and test quiz generation
5. **Mind Map Creator**: Go to `/mindmap` and test mind map creation
6. **ELI5 Simplifier**: Go to `/eli5` and test topic simplification

## Step 4: Production Deployment

### 4.1 Backend Deployment

**Option A: Heroku**
```bash
# Create Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile

# Deploy to Heroku
heroku create your-app-name
heroku config:set MONGODB_URL=your-mongodb-url
heroku config:set GEMINI_API_KEY=your-gemini-key
heroku config:set FIREBASE_API_KEY=your-firebase-key
git push heroku main
```

**Option B: DigitalOcean App Platform**
- Connect your GitHub repository
- Set environment variables
- Deploy automatically

### 4.2 Frontend Deployment

**Option A: Vercel**
```bash
npm install -g vercel
vercel
```

**Option B: Netlify**
- Connect your GitHub repository
- Build command: `npm run build`
- Publish directory: `build`

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Check if MongoDB is running
   - Verify connection string in `.env`
   - Ensure network access if using MongoDB Atlas

2. **Firebase Authentication Error**
   - Verify Firebase configuration
   - Check if Authentication is enabled in Firebase Console
   - Ensure correct API keys

3. **Gemini API Error**
   - Verify API key is correct
   - Check API quota and billing
   - Ensure API is enabled in Google Cloud Console

4. **CORS Error**
   - Check CORS configuration in backend
   - Verify frontend URL is in allowed origins

5. **Port Already in Use**
   - Change port in backend: `uvicorn main:app --port 8001`
   - Update frontend API URL accordingly

### Getting Help

- Check the API documentation at `http://localhost:8000/docs`
- Review the console logs for detailed error messages
- Ensure all environment variables are properly set

## Security Considerations

1. **Environment Variables**: Never commit `.env` files to version control
2. **API Keys**: Keep your API keys secure and rotate them regularly
3. **CORS**: Configure CORS properly for production
4. **Rate Limiting**: Implement rate limiting for production use
5. **Input Validation**: All user inputs are validated on both frontend and backend

## Performance Optimization

1. **Database Indexing**: Add indexes to frequently queried fields
2. **Caching**: Implement Redis caching for frequently accessed data
3. **File Upload**: Use CDN for file storage in production
4. **API Optimization**: Implement pagination and filtering
5. **Frontend Optimization**: Use React.memo and useMemo for performance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 