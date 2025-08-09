import os
import logging
from typing import Dict, Any, Optional
import httpx
import base64
from app.core.config import settings

logger = logging.getLogger(__name__)

# Try to import pytesseract, but make it optional
try:
    import pytesseract
    from PIL import Image
    import io
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed. OCR functionality will be disabled.")

class ImageService:
    def __init__(self):
        # Configure Ollama API endpoint
        self.api_base = settings.ollama_url
        self.model_name = settings.ollama_model  # Using the configured model
        
        # Configure timeouts and limits
        self.timeout = httpx.Timeout(
            connect=5.0,    # connection timeout
            read=600.0,     # read timeout (10 minutes for large images)
            write=60.0,     # write timeout
            pool=60.0       # pool timeout
        )
        
        # Configure chunking for large texts
        self.max_chunk_size = 4000  # Maximum characters per chunk
        
        # Check Tesseract availability
        self.tesseract_available = False
        if TESSERACT_AVAILABLE:
            if os.name == 'nt':  # Windows
                # Try multiple common installation paths
                tesseract_paths = [
                    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                    os.environ.get('TESSERACT_PATH', '')
                ]
                
                for tesseract_path in tesseract_paths:
                    if os.path.exists(tesseract_path):
                        pytesseract.pytesseract.tesseract_cmd = tesseract_path
                        try:
                            pytesseract.get_tesseract_version()
                            self.tesseract_available = True
                            logger.info(f"Tesseract OCR is properly installed and configured at: {tesseract_path}")
                            break
                        except Exception as e:
                            logger.warning(f"Tesseract installation found at {tesseract_path} but not working: {e}")
                
                if not self.tesseract_available:
                    logger.warning("Tesseract executable not found in any standard location")
            else:
                try:
                    pytesseract.get_tesseract_version()
                    self.tesseract_available = True
                    logger.info("Tesseract OCR is properly installed and configured.")
                except Exception as e:
                    logger.warning(f"Error verifying Tesseract installation: {e}")
        
        if not self.tesseract_available:
            logger.warning("Tesseract OCR is not available. Text extraction from images will use alternative methods.")
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR or alternative methods."""
        try:
            # Open and validate image
            try:
                image = Image.open(io.BytesIO(image_data))
                image.verify()  # Verify image integrity
                image = Image.open(io.BytesIO(image_data))  # Reopen after verify
            except Exception as e:
                raise ValueError(f"Invalid or corrupted image file: {str(e)}")
            
            # Preprocess image for better OCR
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            if self.tesseract_available:
                # Extract text using pytesseract with improved settings
                text = pytesseract.image_to_string(
                    image,
                    lang='eng',  # English language
                    config='--psm 3'  # Fully automatic page segmentation
                )
            else:
                # For demonstration, return a message when Tesseract is not available
                # In a production environment, you might want to implement alternative OCR methods
                text = "Image text extraction is currently unavailable. Please install Tesseract OCR for full functionality."
            
            # Clean up the extracted text
            text = text.strip()
            text = ' '.join(text.split())  # Normalize whitespace
            
            if not text:
                raise ValueError("No text could be extracted from the image. Please ensure the image contains clear, readable text.")
            
            logger.info(f"Successfully processed image with {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    async def summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text using Ollama."""
        try:
            # Split long text into chunks if needed
            if len(text) > self.max_chunk_size:
                chunks = [text[i:i + self.max_chunk_size] 
                         for i in range(0, len(text), self.max_chunk_size)]
                logger.info(f"Splitting text into {len(chunks)} chunks")
            else:
                chunks = [text]
            
            all_summaries = []
            
            for i, chunk in enumerate(chunks):
                prompt = f"""
                {'Continuing summary - Part ' + str(i+1) if len(chunks) > 1 else 'Please'} provide a comprehensive summary of the following text. 
                Include key points, main ideas, and important details.
                
                Text to summarize:
                {chunk}
                
                Please structure your response as:
                1. Main Summary (2-3 sentences)
                2. Key Points (bullet points)
                3. Important Details
                
                Keep your response focused and concise.
                """
                
                try:
                    for attempt in range(3):  # Try up to 3 times
                        try:
                            async with httpx.AsyncClient(timeout=self.timeout) as client:
                                response = await client.post(
                                    f"{self.api_base}/api/generate",
                                    json={
                                        "model": self.model_name,
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
                                    
                                all_summaries.append(response_text)
                                break  # Success, exit retry loop
                                
                        except (httpx.ReadTimeout, httpx.ConnectTimeout) as e:
                            if attempt == 2:  # Last attempt
                                raise Exception(f"Timeout error after 3 attempts: {str(e)}")
                            logger.warning(f"Attempt {attempt + 1} failed with timeout, retrying...")
                            await httpx.AsyncClient.aclose()  # Close any hanging connections
                            continue
                            
                except Exception as chunk_error:
                    logger.error(f"Error processing chunk {i+1}: {chunk_error}")
                    raise
            
            # Combine all summaries
            combined_text = "\n\n".join(all_summaries)
            
            # Parse all responses into structured format
            all_parts = combined_text.split('\n')
            
            summary_data = {
                "full_summary": combined_text,
                "main_summary": "",
                "key_points": [],
                "important_details": []
            }
            
            current_section = "main_summary"
            for line in all_parts:
                line = line.strip()
                if not line:
                    continue
                    
                # Handle section headers with or without numbers
                lower_line = line.lower()
                if any(x in lower_line for x in ["main summary", "summary:", "overview:"]):
                    current_section = "main_summary"
                    continue
                elif any(x in lower_line for x in ["key points", "points:", "key findings:"]):
                    current_section = "key_points"
                    continue
                elif any(x in lower_line for x in ["important details", "details:", "additional info"]):
                    current_section = "important_details"
                    continue
                    
                # Handle bullet points and numbered lists
                if line.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
                    line = line.lstrip('•-*123456789. ')
                    if current_section == "key_points":
                        if line not in summary_data["key_points"]:  # Avoid duplicates
                            summary_data["key_points"].append(line)
                    elif current_section == "important_details":
                        if line not in summary_data["important_details"]:  # Avoid duplicates
                            summary_data["important_details"].append(line)
                else:
                    if current_section == "main_summary":
                        summary_data["main_summary"] += line + " "
            
            # Clean up main summary
            summary_data["main_summary"] = summary_data["main_summary"].strip()
            
            # Ensure we have content in each section
            if not summary_data["main_summary"]:
                summary_data["main_summary"] = "Summary could not be generated."
            if not summary_data["key_points"]:
                summary_data["key_points"] = ["No key points identified."]
            if not summary_data["important_details"]:
                summary_data["important_details"] = ["No additional details extracted."]
            
            logger.info(f"Successfully generated summary with {len(summary_data['key_points'])} key points")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error summarizing text: {e}")
            raise Exception(f"Failed to summarize text: {str(e)}")
    
    async def process_image(self, image_data: bytes, filename: str) -> Dict[str, Any]:
        """Process image: extract text and generate summary."""
        try:
            # Extract text from image
            extracted_text = await self.extract_text_from_image(image_data)
            
            # Generate summary
            summary_data = await self.summarize_text(extracted_text)
            
            return {
                "extracted_text": extracted_text,
                "summary": summary_data,
                "filename": filename,
                "word_count": len(extracted_text.split()),
                "character_count": len(extracted_text)
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            raise Exception(f"Failed to process image: {str(e)}")
