import logging
from typing import Dict, Any
from pathlib import Path
import os
import time
from gtts import gTTS
import tempfile
import uuid
from .translation_service import translation_service

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        self.temp_dir = Path("uploads/audio/tts")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.supported_languages = {
            'en': 'English',
            'ta': 'Tamil',
            'hi': 'Hindi',
            'te': 'Telugu',
            'ml': 'Malayalam',
            'kn': 'Kannada',
            'be': 'Bengali',
            'mr': 'Marathi',
            'sa': 'Sanskrit',
            'ur': 'Urdu',
            'sd': 'Sindhi',
            'pa': 'Punjabi',
            'ar': 'Arabic',
            'zh-cn': 'Chinese (Simplified)',
            'zh-tw': 'Chinese (Traditional)',
            'el': 'Greek',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ru': 'Russian'
        }
        
    async def text_to_speech(self, text: str, language: str = 'en', translate: bool = False) -> Dict[str, Any]:
        """Convert text to speech and save as audio file. Optionally translate the text."""
        try:
            logger.debug(f"TTS request - Language: {language}, Translate: {translate}")
            if language not in self.supported_languages:
                raise ValueError(f"Unsupported language: {language}")

            # Translate text if needed (assuming source is English)
            if translate and language != 'en':
                logger.debug(f"Translating text from English to {language}")
                text = await translation_service.translate_text(text, 'en', language)
                logger.debug(f"Translated text: {text}")

            # Generate a unique filename
            filename = f"tts_{uuid.uuid4()}.mp3"
            filepath = self.temp_dir / filename
            
            # Generate speech
            logger.debug(f"Generating speech in language: {language}")
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(filepath))
            logger.debug(f"Speech file saved to: {filepath}")
            
            return {
                "success": True,
                "data": {
                    "file_path": f"/audio/{filename}",  # Use the mounted path
                    "file_name": filename,
                    "duration": len(text.split()) * 0.3,  # Rough estimate of duration
                    "translated_text": text if translate else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error in text to speech conversion: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def cleanup_old_files(self, max_age_hours: int = 1):
        """Clean up old TTS files."""
        try:
            current_time = time.time()
            for file in self.temp_dir.glob("*.mp3"):
                if (current_time - os.path.getctime(file)) > (max_age_hours * 3600):
                    try:
                        os.remove(file)
                    except Exception as e:
                        logger.warning(f"Failed to remove old file {file}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")

# Create singleton instance
text_to_speech_service = TextToSpeechService()
