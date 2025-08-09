import logging
from typing import Dict, Any
from pathlib import Path
import os
import time
from gtts import gTTS
import tempfile
import uuid

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        self.temp_dir = Path("uploads/audio/tts")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    async def text_to_speech(self, text: str, language: str = 'en') -> Dict[str, Any]:
        """Convert text to speech and save as audio file."""
        try:
            # Generate a unique filename
            filename = f"tts_{uuid.uuid4()}.mp3"
            filepath = self.temp_dir / filename
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(str(filepath))
            
            return {
                "success": True,
                "data": {
                    "file_path": f"/audio/{filename}",  # Use the mounted path
                    "file_name": filename,
                    "duration": len(text.split()) * 0.3  # Rough estimate of duration
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
