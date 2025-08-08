from typing import Dict, Any
import logging
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

async def analyze_voice_emotion(audio_data: bytes, transcription: str) -> Dict[str, Any]:
    """Analyze voice characteristics and transcription to detect emotional state."""
    try:
        import google.generativeai as genai
        from app.core.config import settings
        from datetime import datetime
        import json
        
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Using transcription and context for emotion analysis
        prompt = f"""
        Analyze the following transcribed speech and detect the speaker's emotional state.
        Consider the following aspects:
        1. Content and word choice
        2. Context of learning/study environment
        3. Speech patterns and phrases used

        Transcribed text:
        {transcription}

        Provide a structured analysis in this JSON format:
        {{
            "primary_emotion": "one of [happy, confident, motivated, tired, frustrated, stressed, anxious, neutral]",
            "emotion_scores": {{
                "confidence": 0-100,
                "energy_level": 0-100,
                "stress_level": 0-100,
                "motivation_level": 0-100
            }},
            "context": "Brief description of what suggests this emotional state",
            "suggestions": [
                "1-2 specific suggestions based on the emotional state",
                "Focus on learning effectiveness and well-being"
            ],
            "additional_notes": "Any relevant observations about speaking style or patterns"
        }}
        """
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Process the response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        result = json.loads(response_text.strip())
        
        # Add timestamp
        result["analysis_timestamp"] = datetime.now().isoformat()
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing voice emotion: {e}")
        return {
            "success": False,
            "error": str(e)
        }
