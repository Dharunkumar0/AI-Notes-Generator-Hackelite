import PyPDF2
import pdfplumber
import tempfile
import os
import logging
from typing import Dict, Any, List
import io

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        pass

    async def extract_text_pypdf2(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extract text from PDF using PyPDF2."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_content = []
            total_pages = len(pdf_reader.pages)
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append({
                        "page": page_num + 1,
                        "text": text.strip()
                    })
            
            full_text = "\n\n".join([page["text"] for page in text_content])
            
            return {
                "success": True,
                "data": {
                    "text": full_text,
                    "pages": text_content,
                    "total_pages": total_pages,
                    "word_count": len(full_text.split()),
                    "extraction_method": "PyPDF2"
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_text_pdfplumber(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extract text from PDF using pdfplumber (better for complex layouts)."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            
            text_content = []
            total_pages = 0
            
            with pdfplumber.open(pdf_file) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        text_content.append({
                            "page": page_num + 1,
                            "text": text.strip()
                        })
            
            full_text = "\n\n".join([page["text"] for page in text_content])
            
            return {
                "success": True,
                "data": {
                    "text": full_text,
                    "pages": text_content,
                    "total_pages": total_pages,
                    "word_count": len(full_text.split()),
                    "extraction_method": "pdfplumber"
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_text_combined(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Extract text using both methods and combine results."""
        try:
            # Try pdfplumber first (better for complex layouts)
            pdfplumber_result = await self.extract_text_pdfplumber(pdf_bytes)
            
            if pdfplumber_result["success"] and pdfplumber_result["data"]["word_count"] > 0:
                return pdfplumber_result
            
            # Fallback to PyPDF2
            pypdf2_result = await self.extract_text_pypdf2(pdf_bytes)
            
            if pypdf2_result["success"] and pypdf2_result["data"]["word_count"] > 0:
                return pypdf2_result
            
            # If both fail, return the better error message
            if pdfplumber_result["success"]:
                return pypdf2_result
            else:
                return pdfplumber_result
                
        except Exception as e:
            logger.error(f"Error in combined text extraction: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def extract_text_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF file on disk."""
        try:
            with open(file_path, 'rb') as file:
                pdf_bytes = file.read()
            
            return await self.extract_text_combined(pdf_bytes)
            
        except Exception as e:
            logger.error(f"Error reading PDF file: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_pdf_info(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Get basic information about the PDF."""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            info = pdf_reader.metadata
            
            return {
                "success": True,
                "data": {
                    "total_pages": len(pdf_reader.pages),
                    "title": info.get('/Title', 'Unknown'),
                    "author": info.get('/Author', 'Unknown'),
                    "subject": info.get('/Subject', 'Unknown'),
                    "creator": info.get('/Creator', 'Unknown'),
                    "producer": info.get('/Producer', 'Unknown'),
                    "creation_date": info.get('/CreationDate', 'Unknown'),
                    "modification_date": info.get('/ModDate', 'Unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get list of supported PDF features."""
        return {
            "success": True,
            "data": {
                "supported_formats": ["PDF"],
                "max_file_size": "10MB",
                "extraction_methods": ["PyPDF2", "pdfplumber"],
                "features": [
                    "Text extraction",
                    "Page-by-page extraction",
                    "PDF metadata extraction",
                    "Complex layout handling"
                ]
            }
        }

# Create a singleton instance
pdf_service = PDFService() 