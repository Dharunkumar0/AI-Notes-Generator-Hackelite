import speech_recognition as sr
import tempfile
import os
import logging
import sys
from typing import Dict, Any, List, Optional
import wave
import io
import traceback
from pydub import AudioSegment
from werkzeug.utils import secure_filename
from datetime import datetime
import json
import asyncio
import httpx

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class VoiceService:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300  # Lower threshold for better sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.5  # Shorter pause threshold
        self.recognizer.phrase_threshold = 0.3  # More sensitive to phrases
        self._has_pyaudio = False
        self._has_ffmpeg = False
        
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
        
        # Check FFmpeg installation
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            if result.returncode == 0:
                self._has_ffmpeg = True
                logger.info("FFmpeg is installed and working")
            else:
                logger.warning("FFmpeg is not properly installed")
                logger.debug(f"FFmpeg error output: {result.stderr}")
        except FileNotFoundError:
            logger.warning("FFmpeg not found. Please install FFmpeg for audio format conversion support")
            logger.info("Download FFmpeg from: https://www.gyan.dev/ffmpeg/builds/ and add to PATH")
        except Exception as e:
            logger.error(f"Error checking FFmpeg: {str(e)}")
        
        # Check PyAudio installation
        try:
            import pyaudio
            pa = pyaudio.PyAudio()
            device_count = pa.get_device_count()
            pa.terminate()
            
            self._has_pyaudio = True
            logger.info(f"PyAudio is installed and working (Found {device_count} audio devices)")
        except ImportError:
            logger.warning("PyAudio not installed. Microphone functionality will be disabled.")
            logger.info("Install PyAudio using: pip install pyaudio")
        except Exception as e:
            logger.error(f"Error initializing PyAudio: {str(e)}")
            
        # Initialize speech recognition settings
        self.recognizer.pause_threshold = 0.8  # Shorter pause threshold for better segmentation
        self.recognizer.operation_timeout = 30  # 30 seconds timeout for operations
            
    def _convert_to_wav(self, audio_path: str, original_format: str) -> str:
        """Convert audio file to WAV format for processing."""
        try:
            if not self._has_ffmpeg:
                raise ValueError("FFmpeg is not installed. Please install FFmpeg for audio format conversion support.")
                
            if original_format.lower() == 'wav':
                return audio_path
                
            # Load audio file using pydub
            try:
                if original_format.lower() == 'mp3':
                    audio = AudioSegment.from_mp3(audio_path)
                elif original_format.lower() in ['m4a', 'aac']:
                    audio = AudioSegment.from_file(audio_path, format='m4a')
                elif original_format.lower() == 'ogg':
                    audio = AudioSegment.from_ogg(audio_path)
                elif original_format.lower() == 'flac':
                    audio = AudioSegment.from_file(audio_path, format='flac')
                elif original_format.lower() == 'webm':
                    # Use FFmpeg directly for WebM
                    import subprocess
                    wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                    subprocess.run([
                        'ffmpeg', '-i', audio_path,
                        '-acodec', 'pcm_s16le',
                        '-ar', '44100',  # Higher sample rate
                        '-ac', '1',
                        '-af', 'highpass=f=50,lowpass=f=8000,volume=2',  # Audio filters to improve speech clarity
                        '-y', wav_path
                    ], check=True)
                    return wav_path
                else:
                    raise ValueError(f"Unsupported format: {original_format}")
            except Exception as e:
                logger.error(f"Error loading audio file: {e}")
                # Try using FFmpeg directly as fallback
                import subprocess
                wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
                try:
                    subprocess.run(['ffmpeg', '-i', audio_path, wav_path], 
                                check=True, capture_output=True)
                    return wav_path
                except subprocess.CalledProcessError as e:
                    logger.error(f"FFmpeg conversion failed: {e.stderr.decode()}")
                    raise ValueError(f"Could not convert audio file: {str(e)}")
            
            # Convert to WAV using pydub
            wav_path = audio_path.rsplit('.', 1)[0] + '.wav'
            audio.export(wav_path, format='wav')
            return wav_path
            
        except Exception as e:
            logger.error(f"Error converting audio to WAV: {e}")
            raise

    async def transcribe_audio_file(self, audio_file_path: str, original_format: str = "wav") -> Dict[str, Any]:
        """Transcribe audio file to text using Google Speech Recognition."""
        temp_wav_path = None
        try:
            # Convert to WAV if needed
            if original_format.lower() != "wav":
                temp_wav_path = self._convert_to_wav(audio_file_path, original_format)
                process_path = temp_wav_path
            else:
                process_path = audio_file_path
            
            segments = []
            with sr.AudioFile(process_path) as source:
                # Get audio duration
                with wave.open(process_path, 'rb') as wave_file:
                    duration = wave_file.getnframes() / wave_file.getframerate()
                    sample_rate = wave_file.getframerate()
                
                # Process in 30-second segments if longer than 60 seconds
                if duration > 60:
                    chunk_duration = 30
                    for offset in range(0, int(duration), chunk_duration):
                        source.stream.seek(int(offset * source.SAMPLE_RATE))
                        audio_chunk = self.recognizer.record(source, duration=min(chunk_duration, duration - offset))
                        try:
                            chunk_text = self.recognizer.recognize_google(audio_chunk, language="en-IN")
                            segments.append(chunk_text)
                        except sr.UnknownValueError:
                            # Skip silent segments
                            continue
                        except sr.RequestError as e:
                            raise e
                else:
                    # Multiple attempts with different noise adjustment settings
                    max_attempts = 3
                    for attempt in range(max_attempts):
                        try:
                            source.stream.seek(0)  # Reset to beginning of audio
                            
                            # Adjust noise settings based on attempt
                            if attempt == 0:
                                self.recognizer.adjust_for_ambient_noise(source, duration=min(0.5, duration/2))
                            elif attempt == 1:
                                self.recognizer.energy_threshold = 200  # Try with lower threshold
                            else:
                                self.recognizer.energy_threshold = 100  # Try with even lower threshold
                            
                            audio = self.recognizer.record(source)
                            text = self.recognizer.recognize_google(audio, language="en-IN")
                            if text:  # If we got a valid transcription
                                segments.append(text)
                                break
                        except sr.UnknownValueError:
                            if attempt == max_attempts - 1:  # Only raise on last attempt
                                raise sr.UnknownValueError("Could not understand the audio. Please speak clearly and try again.")
                            continue
                
            # Combine all segments
            full_text = " ".join(segments)
            
            # Create timestamps based on word count and duration
            words = full_text.split()
            word_count = len(words)
            timestamps = []
            
            if word_count > 0:
                avg_word_duration = duration / word_count
                current_time = 0
                for i, word in enumerate(words):
                    timestamps.append({
                        "word": word,
                        "start_time": round(current_time, 2),
                        "end_time": round(current_time + avg_word_duration, 2)
                    })
                    current_time += avg_word_duration
            
            return {
                "success": True,
                "data": {
                    "transcription": full_text,
                    "confidence": 0.9,  # Google doesn't provide confidence for file recognition
                    "word_count": word_count,
                    "duration": round(duration, 2),
                    "timestamps": timestamps,
                    "segments": len(segments),
                    "sample_rate": sample_rate
                }
            }
                
        except sr.UnknownValueError as e:
            return {
                "success": False,
                "error": str(e)
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
        finally:
            # Clean up temporary WAV file if created
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except:
                    pass

    # async def transcribe_audio_file(self, audio_file_path: str, original_format: str = "wav") -> Dict[str, Any]:
    #     """Transcribe audio file to text."""
    #     temp_wav_path = None
    #     try:
    #         logger.debug(f"Processing audio file: {audio_file_path}")
            
    #         # Check if FFmpeg is required and available
    #         if original_format.lower() != "wav" and not self._has_ffmpeg:
    #             raise ValueError("FFmpeg is required for non-WAV files but is not installed")
            
    #         # Convert to WAV if needed
    #         if original_format.lower() != "wav":
    #             logger.debug(f"Converting {original_format} to WAV format")
    #             try:
    #                 temp_wav_path = self._convert_to_wav(audio_file_path, original_format)
    #                 process_path = temp_wav_path
    #             except Exception as e:
    #                 logger.error(f"Error converting to WAV: {str(e)}")
    #                 raise ValueError(f"Failed to convert audio format: {str(e)}")
    #         else:
    #             process_path = audio_file_path
            
    #         logger.debug(f"Transcribing WAV file: {process_path}")
            
    #         try:
    #             with sr.AudioFile(process_path) as source:
    #                 # Adjust for ambient noise
    #                 self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
    #                 audio = self.recognizer.record(source)
                    
    #                 # Try recognizing with Google Speech Recognition
    #                 text = self.recognizer.recognize_google(audio)
                    
    #                 # Get audio duration
    #                 with wave.open(process_path, 'rb') as wave_file:
    #                     duration = wave_file.getnframes() / wave_file.getframerate()
                    
    #                 # Create timestamps
    #                 words = text.split()
    #                 word_count = len(words)
    #                 timestamps = []
                    
    #                 if word_count > 0:
    #                     avg_word_duration = duration / word_count
    #                     current_time = 0
    #                     for i, word in enumerate(words):
    #                         timestamps.append({
    #                             "word": word,
    #                             "start_time": round(current_time, 2),
    #                             "end_time": round(current_time + avg_word_duration, 2)
    #                         })
    #                         current_time += avg_word_duration
                    
    #                 return {
    #                     "success": True,
    #                     "data": {
    #                         "transcription": text,
    #                         "confidence": 0.9,
    #                         "word_count": word_count,
    #                         "duration": round(duration, 2),
    #                         "timestamps": timestamps
    #                     }
    #                 }
                    
    #         except sr.UnknownValueError:
    #             logger.error("Speech could not be understood")
    #             return {
    #                 "success": False,
    #                 "error": "Speech could not be understood. Please check the audio quality."
    #             }
    #         except sr.RequestError as e:
    #             logger.error(f"Could not request results from speech recognition service: {e}")
    #             return {
    #                 "success": False,
    #                 "error": f"Speech recognition service error: {str(e)}"
    #             }
                
    #     except Exception as e:
    #         logger.error(f"Error transcribing audio file: {str(e)}")
    #         return {
    #             "success": False,
    #             "error": str(e)
    #         }
    #     finally:
    #         # Clean up temporary WAV file
    #         if temp_wav_path and os.path.exists(temp_wav_path):
    #             try:
    #                 os.remove(temp_wav_path)
    #                 logger.debug(f"Removed temporary WAV file: {temp_wav_path}")
    #             except Exception as e:
    #                 logger.warning(f"Failed to remove temporary WAV file: {str(e)}")
                    
    async def transcribe_audio_bytes(self, audio_bytes: bytes, format: str = "wav") -> Dict[str, Any]:
        """Transcribe audio bytes to text."""
        try:
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
                logger.debug(f"Created temporary file for audio bytes: {temp_file_path}")
            
            try:
                result = await self.transcribe_audio_file(temp_file_path, format)
                return result
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        logger.debug(f"Removed temporary file: {temp_file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove temporary file: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error transcribing audio bytes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def record_audio(self, duration: int = 10, save_file: bool = True) -> Dict[str, Any]:
        """Record audio from microphone and optionally save to file."""
        if not self._has_pyaudio:
            return {
                "success": False,
                "error": "Microphone functionality is not available. PyAudio is not installed."
            }
        
        audio_data = None
        file_path = None
        
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
                # Adjust for ambient noise
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info(f"Recording for {duration} seconds...")
                try:
                    audio_data = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
                    logger.debug("Audio captured successfully")
                except Exception as e:
                    logger.error(f"Error capturing audio: {e}")
                    return {
                        "success": False,
                        "error": f"Error capturing audio: {str(e)}"
                    }
                
                if save_file:
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
                        "file_path": file_path if save_file else None,
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
        """Record and transcribe audio from microphone in real-time."""
        try:
            # First record the audio
            record_result = await self.record_audio(duration=duration, save_file=True)
            
            if not record_result["success"]:
                return record_result
                
            audio_data = record_result["data"]["audio_data"]
            file_path = record_result["data"]["file_path"]
            
            try:
                logger.debug("Recognizing speech...")
                text = self.recognizer.recognize_google(audio_data)
                logger.info("Speech recognized successfully")
                
                # Get audio duration from the saved file
                with wave.open(file_path, 'rb') as wave_file:
                    duration = wave_file.getnframes() / wave_file.getframerate()
                
                # Create word timestamps
                words = text.split()
                word_count = len(words)
                timestamps = []
                
                if word_count > 0:
                    avg_word_duration = duration / word_count
                    current_time = 0
                    for i, word in enumerate(words):
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
                        "confidence": 0.9,
                        "word_count": word_count,
                        "duration": round(duration, 2),
                        "timestamps": timestamps,
                        "file_path": file_path
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
                    "wav", "mp3", "m4a", "flac", "ogg", "webm"
                ],
                "recommended_format": "wav",
                "max_file_size": "10MB",
                "recording_limits": {
                    "max_duration": 300,  # 5 minutes
                    "min_duration": 1,    # 1 second
                    "default_duration": 10 # 10 seconds
                }
            }
        }

    async def analyze_audio_content(self, transcription: str) -> Dict[str, Any]:
        """Analyze transcribed text for key points and sentiment."""
        try:
            from app.services.ai_service import AIService
            
            ai_service = AIService()
            
            prompt = f"""
            Analyze the following transcribed speech text and provide a structured analysis.
            Focus on key points, main ideas, and overall sentiment.
            
            Text to analyze:
            {transcription}
            
            Please provide the analysis in this JSON format:
            {{
                "summary": "A concise summary of the main points",
                "key_points": ["point 1", "point 2", "point 3"],
                "topics_discussed": ["topic 1", "topic 2"],
                "sentiment": "positive/negative/neutral",
                "sentiment_reasons": ["reason 1", "reason 2"],
                "clarity_score": 0-10,
                "suggested_improvements": ["suggestion 1", "suggestion 2"]
            }}
            
            Return only the JSON object, no additional text.
            """
            
            async with httpx.AsyncClient(timeout=ai_service.timeout) as client:
                response = await client.post(
                    f"{ai_service.api_base}/api/generate",
                    json={
                        "model": ai_service.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 2048
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API request failed: {response.text}")
                    
                response_data = response.json()
                response_text = response_data.get("response", "").strip()
                
                if not response_text:
                    raise ValueError("Empty response from Ollama")
                
                # Clean response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]  # Remove ```json and ``` markers
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]  # Remove ``` markers
                
                result = json.loads(response_text.strip())
                
                # Validate response structure
                required_fields = ["summary", "key_points", "topics_discussed", "sentiment", 
                                "sentiment_reasons", "clarity_score", "suggested_improvements"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field in response: {field}")
                
                # Validate array fields
                array_fields = ["key_points", "topics_discussed", "sentiment_reasons", "suggested_improvements"]
                for field in array_fields:
                    if not isinstance(result[field], list):
                        result[field] = []  # Default to empty list if invalid
                
                # Validate clarity score
                try:
                    result["clarity_score"] = int(result["clarity_score"])
                    if result["clarity_score"] < 0:
                        result["clarity_score"] = 0
                    elif result["clarity_score"] > 10:
                        result["clarity_score"] = 10
                except (ValueError, TypeError):
                    result["clarity_score"] = 5  # Default score
                
                return {
                    "success": True,
                    "data": result
                }
            
        except Exception as e:
            logger.error(f"Error analyzing audio content: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def summarize_audio(self, transcription: str, max_length: int = 200) -> Dict[str, Any]:
        """Generate a concise summary of the transcribed audio content."""
        try:
            from app.services.ai_service import AIService
            
            ai_service = AIService()
            
            prompt = f"""
            Create a concise summary of this transcribed speech, highlighting the most important points.
            Keep the summary within {max_length} words.
            
            Text to summarize:
            {transcription}
            
            Please provide the summary in this JSON format:
            {{
                "summary": "The concise summary",
                "main_points": ["point 1", "point 2", "point 3"],
                "word_count": number of words in summary,
                "key_phrases": ["phrase 1", "phrase 2"],
                "action_items": ["action 1", "action 2"] if any,
                "context": "brief description of the context/setting"
            }}
            
            Return only the JSON object, no additional text.
            """
            
            async with httpx.AsyncClient(timeout=ai_service.timeout) as client:
                response = await client.post(
                    f"{ai_service.api_base}/api/generate",
                    json={
                        "model": ai_service.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 2048
                        }
                    }
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama API request failed: {response.text}")
                    
                response_data = response.json()
                response_text = response_data.get("response", "").strip()
                
                if not response_text:
                    raise ValueError("Empty response from Ollama")
                
                # Clean response
                if response_text.startswith('```json'):
                    response_text = response_text[7:-3]  # Remove ```json and ``` markers
                elif response_text.startswith('```'):
                    response_text = response_text[3:-3]  # Remove ``` markers
                
                result = json.loads(response_text.strip())
                
                # Validate response structure
                required_fields = ["summary", "main_points", "word_count", "key_phrases", "action_items", "context"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"Missing required field in response: {field}")
                
                # Validate array fields
                array_fields = ["main_points", "key_phrases", "action_items"]
                for field in array_fields:
                    if not isinstance(result[field], list):
                        result[field] = []  # Default to empty list if invalid
                
                # Validate word count
                try:
                    result["word_count"] = int(result["word_count"])
                except (ValueError, TypeError):
                    result["word_count"] = len(result["summary"].split())
                
                return {
                    "success": True,
                    "data": result
                }
            
        except Exception as e:
            logger.error(f"Error summarizing audio content: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
voice_service = VoiceService()