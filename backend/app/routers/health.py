import time
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db

router = APIRouter(tags=["Health"])

START_TIME = time.time()

@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint for ALB, Route 53, or CloudWatch uptime probes.
    Verifies that the FastAPI process is responsive and can query the database.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    uptime_seconds = round(time.time() - START_TIME, 2)
    
    return {
        "status": "UP" if db_status == "healthy" else "DEGRADED",
        "service": "Cloud-Based Product Delivery & Real-Time Tracking System",
        "environment": "cloud",
        "uptime_seconds": uptime_seconds,
        "database": db_status
    }
