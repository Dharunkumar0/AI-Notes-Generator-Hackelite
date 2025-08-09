import speech_recognition as sr
import tempfile
import os
import logging
import sys
from typing import Dict, Any, List, Optional, Tuple
import wave
import io
import traceback
import json
import asyncio
import httpx
from datetime import datetime
from pydub import AudioSegment
from pydub.utils import make_chunks
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.recognizer.phrase_threshold = 0.3
        self.supported_formats = ["wav", "mp3", "m4a", "ogg", "flac", "webm"]
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        
        # Create necessary directories
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.uploads_dir = os.path.join(self.base_dir, "uploads", "audio")
        self.temp_dir = os.path.join(self.base_dir, "uploads", "temp")
        
        for dir_path in [self.uploads_dir, self.temp_dir]:
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.debug(f"Created directory: {dir_path}")
            except Exception as e:
                logger.error(f"Error creating directory {dir_path}: {str(e)}")
    
    def _convert_to_wav(self, audio_path: str, original_format: str) -> str:
        """Convert audio file to WAV format for processing."""
        try:
            if original_format.lower() == 'wav':
                return audio_path
                
            # Use pydub to convert
            audio = AudioSegment.from_file(audio_path, format=original_format.lower())
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            
            # Export with better settings for speech recognition
            audio = audio.set_frame_rate(16000).set_channels(1)
            audio.export(wav_path, format='wav')
            
            return wav_path
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            raise ValueError(f"Could not convert audio file: {str(e)}")

    async def transcribe_audio_file(self, audio_file_path: str, original_format: str = "wav") -> Dict[str, Any]:
        """Transcribe audio file to text using Google Speech Recognition."""
        temp_wav_path = None
        try:
            logger.info(f"Starting transcription for file: {audio_file_path} (format: {original_format})")
            
            # Convert to WAV if needed
            if original_format.lower() != "wav":
                temp_wav_path = self._convert_to_wav(audio_file_path, original_format)
                process_path = temp_wav_path
            else:
                process_path = audio_file_path

            # Validate file exists
            if not os.path.isfile(process_path):
                raise ValueError("Audio file not found")
            
            # Get audio info
            audio = AudioSegment.from_file(process_path)
            duration = len(audio) / 1000.0  # Convert to seconds
            
            if duration == 0:
                raise ValueError("Audio file appears to be empty")
            
            # Process with speech_recognition
            with sr.AudioFile(process_path) as source:
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=min(0.5, duration/2))
                
                # Record the audio
                audio_data = self.recognizer.record(source)
                
                # Try Google Speech Recognition with multiple attempts
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        if attempt == 0:
                            # First attempt with default settings
                            text = self.recognizer.recognize_google(audio_data, language="en-US")
                        elif attempt == 1:
                            # Second attempt with Indian English
                            text = self.recognizer.recognize_google(audio_data, language="en-IN")
                        else:
                            # Third attempt with lower energy threshold
                            self.recognizer.energy_threshold = 100
                            text = self.recognizer.recognize_google(audio_data, language="en-US")
                        
                        if text and text.strip():
                            break
                            
                    except sr.UnknownValueError:
                        if attempt == max_attempts - 1:
                            raise sr.UnknownValueError("Could not understand the audio")
                        continue
                    except sr.RequestError as e:
                        raise e
                
                # Calculate word count and create timestamps
                words = text.split() if text else []
                word_count = len(words)
                timestamps = []
                
                if word_count > 0:
                    avg_word_duration = duration / word_count
                    current_time = 0
                    for word in words:
                        timestamps.append({
                            "word": word,
                            "start_time": round(current_time, 2),
                            "end_time": round(current_time + avg_word_duration, 2)
                        })
                        current_time += avg_word_duration
                
                return {
                    "success": True,
                    "data": {
                        "transcription": text,
                        "confidence": 0.95,  # Default confidence
                        "word_count": word_count,
                        "duration": round(duration, 2),
                        "timestamps": timestamps,
                        "sample_rate": 16000
                    }
                }
                
        except sr.UnknownValueError:
            logger.warning("Speech Recognition could not understand the audio")
            return {
                "success": False,
                "error": "Could not understand the audio. Please ensure the audio is clear and contains speech."
            }
        except sr.RequestError as e:
            logger.error(f"Speech Recognition service error: {e}")
            return {
                "success": False,
                "error": f"Speech recognition service error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error transcribing audio file: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Clean up temporary WAV file
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except Exception as e:
                    logger.error(f"Error cleaning up temporary file: {e}")

    async def record_audio(self, duration: int = 10) -> Dict[str, Any]:
        """Record audio from microphone."""
        try:
            # Check if microphone is available
            try:
                import pyaudio
                sr.Microphone.list_microphone_names()
            except Exception as e:
                return {
                    "success": False,
                    "error": "Microphone not available. Please check your microphone settings."
                }

            with sr.Microphone() as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info(f"Recording for {duration} seconds...")
                audio_data = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"recording_{timestamp}.wav"
                file_path = os.path.join(self.uploads_dir, filename)
                
                # Save audio data
                with open(file_path, "wb") as f:
                    f.write(audio_data.get_wav_data())
                
                logger.info(f"Audio saved to {file_path}")
                
                return {
                    "success": True,
                    "data": {
                        "duration": duration,
                        "file_path": file_path,
                        "audio_data": audio_data
                    }
                }
                
        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def transcribe_microphone(self, duration: int = 10) -> Dict[str, Any]:
        """Record and transcribe audio from microphone."""
        try:
            # First record the audio
            record_result = await self.record_audio(duration=duration)
            
            if not record_result["success"]:
                return record_result
                
            audio_data = record_result["data"]["audio_data"]
            file_path = record_result["data"]["file_path"]
            
            try:
                # Recognize speech
                text = self.recognizer.recognize_google(audio_data, language="en-US")
                
                # Get duration from file
                with wave.open(file_path, 'rb') as wave_file:
                    duration = wave_file.getnframes() / wave_file.getframerate()
                
                # Create word timestamps
                words = text.split()
                word_count = len(words)
                timestamps = []
                
                if word_count > 0:
                    avg_word_duration = duration / word_count
                    current_time = 0
                    for word in words:
                        timestamps.append({
                            "word": word,
                            "start_time": round(current_time, 2),
                            "end_time": round(current_time + avg_word_duration, 2)
                        })
                        current_time += avg_word_duration
                
                return {
                    "success": True,
                    "data": {
                        "transcription": text,
                        "confidence": 0.95,
                        "word_count": word_count,
                        "duration": round(duration, 2),
                        "timestamps": timestamps,
                        "file_path": file_path
                    }
                }
                
            except sr.UnknownValueError:
                return {
                    "success": False,
                    "error": "Could not understand the speech. Please speak clearly and try again."
                }
            except sr.RequestError as e:
                return {
                    "success": False,
                    "error": f"Speech recognition service error: {str(e)}"
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
                "supported_formats": self.supported_formats,
                "recommended_format": "wav",
                "max_file_size": self.max_file_size,
                "max_file_size_mb": "10MB",
                "recording_limits": {
                    "max_duration": 300,  # 5 minutes
                    "min_duration": 1,    # 1 second
                    "default_duration": 10 # 10 seconds
                }
            }
        }

    async def summarize_audio(self, transcription: str, max_length: int = 200) -> Dict[str, Any]:
        """Generate a simple extractive summary of the transcription."""
        try:
            if not transcription or not transcription.strip():
                return {
                    "success": False,
                    "error": "No transcription text provided"
                }
            
            # Simple extractive summary logic
            sentences = [s.strip() for s in transcription.split('.') if s.strip()]
            
            if not sentences:
                return {
                    "success": False,
                    "error": "No sentences found in transcription"
                }
            
            # Take first few sentences or middle sentences based on length
            if len(sentences) <= 3:
                summary_sentences = sentences
            else:
                # Take first sentence and some from middle
                summary_sentences = [sentences[0]]
                mid_start = len(sentences) // 3
                mid_end = (2 * len(sentences)) // 3
                summary_sentences.extend(sentences[mid_start:mid_end][:2])
            
            summary = '. '.join(summary_sentences) + '.'
            
            # Extract key phrases (simple approach)
            words = transcription.lower().split()
            word_freq = {}
            for word in words:
                if len(word) > 4:  # Only consider longer words
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Get top frequent words as key phrases
            key_phrases = sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)[:5]
            
            return {
                "success": True,
                "data": {
                    "summary": summary,
                    "main_points": summary_sentences,
                    "word_count": len(summary.split()),
                    "key_phrases": key_phrases,
                    "action_items": [],  # Could be enhanced with NLP
                    "context": "Voice transcription summary"
                }
            }
            
        except Exception as e:
            logger.error(f"Error summarizing audio content: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
voice_service = VoiceService()