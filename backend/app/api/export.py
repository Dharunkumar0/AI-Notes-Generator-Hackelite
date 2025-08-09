from fastapi import APIRouter, HTTPException, Depends, status, Response
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime
import pdfkit
import os
import tempfile

from app.api.auth import get_current_user
from app.models.user import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Check if wkhtmltopdf is installed and configure pdfkit
try:
    # Try to find wkhtmltopdf in common installation paths
    wkhtmltopdf_paths = [
        'wkhtmltopdf',  # If in PATH
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files (x86)\wkhtmltopdf\bin\wkhtmltopdf.exe',
        r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'
    ]
    
    config = None
    for path in wkhtmltopdf_paths:
        try:
            config = pdfkit.configuration(wkhtmltopdf=path)
            logger.info(f"Found wkhtmltopdf at: {path}")
            break
        except Exception:
            continue
    
    if config is None:
        raise Exception("wkhtmltopdf not found in common paths")
    
    logger.info("PDF generation service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PDF service: {str(e)}")
    logger.error("Please ensure wkhtmltopdf is installed. Download from: https://wkhtmltopdf.org/downloads.html")
    config = None

logger = logging.getLogger(__name__)
router = APIRouter()


class PDFExportRequest(BaseModel):
    html: str
    filename: Optional[str] = None
    title: Optional[str] = None


@router.post("/pdf")
async def export_pdf(
    payload: PDFExportRequest,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate a PDF from provided HTML using pdfkit and return it as a download."""
    try:
        if config is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PDF generation service is not configured"
            )

        if not payload.html or not payload.html.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HTML content is required"
            )

        filename = payload.filename or f"export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf"
        title = payload.title or "Export"

        # Define CSS styles
        css = """
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; color: #1f2937; }
            h1, h2, h3, h4 { color: #111827; margin: 0 0 8px; }
            h1 { font-size: 22px; }
            h2 { font-size: 18px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
            h3 { font-size: 16px; }
            p, li, td, th { font-size: 12px; line-height: 1.5; }
            .meta { color: #6b7280; font-size: 10px; margin-bottom: 16px; }
            .section { margin: 14px 0; }
            ul { padding-left: 18px; }
            table { width: 100%; border-collapse: collapse; margin: 8px 0; }
            th, td { border: 1px solid #e5e7eb; padding: 6px; text-align: left; }
        """

        # Sanitize HTML content
        sanitized_html = payload.html.strip().replace('\n', ' ').replace('\r', '')
        
        html_doc = f"""
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
            <style>{css}</style>
          </head>
          <body>
            {sanitized_html}
          </body>
        </html>
        """
        
        logger.info("Attempting to generate PDF...")
        html_path = None
        try:
            # Create a temporary file to store the HTML
            with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as html_file:
                html_file.write(html_doc)
                html_path = html_file.name

            # Convert HTML to PDF using pdfkit
            options = {
                'page-size': 'A4',
                'margin-top': '24mm',
                'margin-right': '18mm',
                'margin-bottom': '24mm',
                'margin-left': '18mm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'quiet': ''
            }
            
            pdf_bytes = pdfkit.from_file(html_path, False, options=options, configuration=config)
            if not pdf_bytes:
                raise Exception("PDF generation returned empty result")
            logger.info("PDF generated successfully")
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate PDF: {str(e)}"
            )
        finally:
            # Clean up the temporary file
            if html_path and os.path.exists(html_path):
                try:
                    os.unlink(html_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file {html_path}: {str(e)}")

        headers = {
            "Content-Disposition": f"attachment; filename={filename}"
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.exception(f"Failed to export PDF: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {error_msg}"
        )


