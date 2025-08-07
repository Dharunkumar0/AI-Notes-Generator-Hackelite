import os
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
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
        # Configure Gemini
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Configure Tesseract path for Windows if available
        if TESSERACT_AVAILABLE and os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using OCR."""
        if not TESSERACT_AVAILABLE:
            raise Exception("OCR functionality not available. Please install pytesseract: pip install pytesseract")
        
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_data))
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(image)
            
            # Clean up the extracted text
            text = text.strip()
            
            if not text:
                raise ValueError("No text could be extracted from the image")
            
            logger.info(f"Successfully extracted {len(text)} characters from image")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise Exception(f"Failed to extract text from image: {str(e)}")
    
    async def summarize_text(self, text: str) -> Dict[str, Any]:
        """Summarize text using Gemini 2.5 Pro."""
        try:
            prompt = f"""
            Please provide a comprehensive summary of the following text. 
            Include key points, main ideas, and important details.
            
            Text to summarize:
            {text}
            
            Please structure your response as:
            1. Main Summary (2-3 sentences)
            2. Key Points (bullet points)
            3. Important Details
            """
            
            response = self.model.generate_content(prompt)
            
            if not response.text:
                raise ValueError("No summary generated")
            
            # Parse the response into structured format
            summary_parts = response.text.split('\n')
            
            summary_data = {
                "full_summary": response.text,
                "main_summary": "",
                "key_points": [],
                "important_details": []
            }
            
            current_section = "main_summary"
            for line in summary_parts:
                line = line.strip()
                if not line:
                    continue
                    
                if "1. Main Summary" in line or "Main Summary" in line:
                    current_section = "main_summary"
                elif "2. Key Points" in line or "Key Points" in line:
                    current_section = "key_points"
                elif "3. Important Details" in line or "Important Details" in line:
                    current_section = "important_details"
                elif line.startswith("•") or line.startswith("-"):
                    if current_section == "key_points":
                        summary_data["key_points"].append(line[1:].strip())
                else:
                    if current_section == "main_summary":
                        summary_data["main_summary"] += line + " "
                    elif current_section == "important_details":
                        summary_data["important_details"].append(line)
            
            # Clean up main summary
            summary_data["main_summary"] = summary_data["main_summary"].strip()
            
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
