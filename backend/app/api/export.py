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
    config = pdfkit.configuration()
    logger.info("PDF generation service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PDF service: {str(e)}")
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
    """Generate a PDF from provided HTML using WeasyPrint and return it as a download."""
    try:
        if HTML is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="WeasyPrint is not installed on the server"
            )

        if not payload.html or not payload.html.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="HTML content is required"
            )

        filename = payload.filename or f"export-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf"
        title = payload.title or "Export"

        base_css = CSS(string="""
            @page { size: A4; margin: 24mm 18mm; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Liberation Sans', sans-serif; color: #1f2937; }
            h1, h2, h3, h4 { color: #111827; margin: 0 0 8px; }
            h1 { font-size: 22px; }
            h2 { font-size: 18px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
            h3 { font-size: 16px; }
            p, li, td, th { font-size: 12px; line-height: 1.5; }
            .meta { color: #6b7280; font-size: 10px; margin-bottom: 16px; }
            .section { margin: 14px 0; }
            .pill { display: inline-block; font-size: 10px; background: #eef2ff; color: #3730a3; padding: 2px 8px; border-radius: 9999px; }
            ul { padding-left: 18px; }
            table { width: 100%; border-collapse: collapse; margin: 8px 0; }
            th, td { border: 1px solid #e5e7eb; padding: 6px; text-align: left; }
            .muted { color: #6b7280; }
            .small { font-size: 10px; }
        """)

        # Sanitize HTML content
        sanitized_html = payload.html.strip().replace('\n', ' ').replace('\r', '')
        
        html_doc = f"""
        <!DOCTYPE html>
        <html lang="en">
          <head>
            <meta charset="utf-8" />
            <title>{title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1" />
          </head>
          <body>
            {sanitized_html}
          </body>
        </html>
        """
        
        logger.info("Attempting to generate PDF...")
        try:
            pdf_bytes = HTML(string=html_doc).write_pdf(stylesheets=[base_css])
            logger.info("PDF generated successfully")
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}")
            raise

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


