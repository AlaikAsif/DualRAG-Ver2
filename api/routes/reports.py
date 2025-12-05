"""Report generation endpoints."""

from fastapi import APIRouter, HTTPException
import logging
from datetime import datetime

from src.schemas.report import ReportGenerationRequest, ReportGenerationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/reports", response_model=ReportGenerationResponse)
async def generate_report(request: ReportGenerationRequest) -> ReportGenerationResponse:
    """
    Generate a report based on query results.

    Args:
        request: ReportGenerationRequest with content and customization

    Returns:
        ReportGenerationResponse with generated report
    """
    try:
        if not request.content or not request.content.strip():
            raise ValueError("Report content cannot be empty")

        logger.info(f"Generating report: {request.title}")

        response = ReportGenerationResponse(
            report_id="rep_" + str(hash(request.title))[-10:],
            title=request.title,
            content=request.content,
            status="completed",
            generated_at=datetime.utcnow().isoformat(),
            format=request.format if hasattr(request, 'format') else "html"
        )

        logger.info(f"Report generated: {response.report_id}")
        return response

    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate report: {str(e)}"
        )


@router.get("/reports/{report_id}")
async def get_report(report_id: str):
    """Get a generated report by ID."""
    try:
        return {
            "report_id": report_id,
            "title": "Sample Report",
            "content": "Report content",
            "generated_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error retrieving report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve report: {str(e)}"
        )


@router.delete("/reports/{report_id}")
async def delete_report(report_id: str):
    """Delete a report."""
    try:
        return {
            "status": "success",
            "message": f"Report {report_id} deleted"
        }
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete report: {str(e)}"
        )
