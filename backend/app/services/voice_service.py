import speech_recognition as sr
import tempfile
import os
import logging
import sys
from typing import Dict, Any
import wave
import io
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000
        self.recognizer.dynamic_energy_threshold = True
        self._has_pyaudio = False
        try:
            import pyaudio
            self._has_pyaudio = True
        except ImportError:
            logger.warning("PyAudio not installed. Microphone functionality will be disabled.")

    async def transcribe_audio_file(self, audio_file_path: str) -> Dict[str, Any]:
        """Transcribe audio file to text using Google Speech Recognition."""
        try:
            with sr.AudioFile(audio_file_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Record audio
                audio = self.recognizer.record(source)
                
                # Transcribe using Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                
                return {
                    "success": True,
                    "data": {
                        "transcription": text,
                        "confidence": 0.9,  # Google doesn't provide confidence for file recognition
                        "word_count": len(text.split())
                    }
                }
                
        except sr.UnknownValueError:
            return {
                "success": False,
                "error": "Speech could not be understood"
            }
        except sr.RequestError as e:
            return {
                "success": False,
                "error": f"Could not request results from speech recognition service: {e}"
            }
        except Exception as e:
            logger.error(f"Error transcribing audio file: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def transcribe_audio_bytes(self, audio_bytes: bytes, format: str = "wav") -> Dict[str, Any]:
        """Transcribe audio bytes to text."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                result = await self.transcribe_audio_file(temp_file_path)
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error transcribing audio bytes: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def transcribe_microphone(self, duration: int = 10) -> Dict[str, Any]:
        """Transcribe audio from microphone in real-time."""
        if not self._has_pyaudio:
            return {
                "success": False,
                "error": "Microphone functionality is not available. PyAudio is not installed."
            }
            
        try:
            logger.debug("Checking for microphone...")
            try:
                sr.Microphone.list_microphone_names()
            except Exception as e:
                logger.error(f"No microphone found: {e}")
                return {
                    "success": False,
                    "error": "No microphone found. Please check your microphone settings."
                }

            logger.debug("Initializing microphone...")
            with sr.Microphone() as source:
                logger.info("Listening...")
                try:
                    audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                    logger.debug("Audio captured successfully")
                except Exception as e:
                    logger.error(f"Error capturing audio: {e}")
                    return {
                        "success": False,
                        "error": f"Error capturing audio: {str(e)}"
                    }
                
                try:
                    logger.debug("Recognizing speech...")
                    text = self.recognizer.recognize_google(audio)
                    logger.info("Speech recognized successfully")
                    return {
                        "success": True,
                        "data": {
                            "transcription": text,
                            "confidence": 0.9,
                            "word_count": len(text.split())
                        }
                    }
                except sr.UnknownValueError:
                    logger.error("Speech could not be understood")
                    return {
                        "success": False,
                        "error": "Speech could not be understood"
                    }
                except sr.RequestError as e:
                    logger.error(f"Could not request results from speech recognition service: {e}")
                    return {
                        "success": False,
                        "error": f"Could not request results from speech recognition service: {e}"
                    }
                    
        except Exception as e:
            logger.error(f"Error transcribing microphone: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get list of supported audio formats."""
        return {
            "success": True,
            "data": {
                "supported_formats": [
                    "wav", "mp3", "m4a", "flac", "ogg"
                ],
                "recommended_format": "wav",
                "max_file_size": "10MB"
            }
        }

# Create a singleton instance
voice_service = VoiceService() 