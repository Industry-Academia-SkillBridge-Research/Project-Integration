"""
Admin routes for database management and seeding.
Uses flat skill structure.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..services.seed_service import seed_course_catalog, seed_course_skill_map
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/seed-mapping")
def seed_mapping(db: Session = Depends(get_db)):
    """
    Seed course catalog and course-skill mapping data from CSV files (flat skills).
    
    Returns:
        Dictionary with seeding status and detailed row counts
    """
    try:
        logger.info("Starting mapping data seeding (flat skills)")
        
        # Seed course catalog
        catalog_result = seed_course_catalog(db)
        logger.info(f"Course catalog seeded: {catalog_result['inserted']} inserted, {catalog_result['updated']} updated")
        
        # Seed course skill map (flat skills)
        skill_map_result = seed_course_skill_map(db)
        logger.info(f"Course skill map seeded: {skill_map_result['inserted']} inserted, {skill_map_result['updated']} updated")
        
        return {
            "status": "ok",
            "course_catalog": {
                "inserted": catalog_result["inserted"],
                "updated": catalog_result["updated"]
            },
            "course_skill_map": {
                "inserted": skill_map_result["inserted"],
                "updated": skill_map_result["updated"]
            }
        }
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Seeding failed: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")
