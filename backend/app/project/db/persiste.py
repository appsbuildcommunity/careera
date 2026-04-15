import logging
from datetime import datetime, timezone

from app.database.connection import get_database
from app.project.model.project_generation import ProjectSeed

logger = logging.getLogger(__name__)

async def store_projects_generation_result(user_id: str, projects: list[ProjectSeed]) -> None:
    """Store the generated projects in MongoDB."""
    try:
        db = await get_database()
        coll = db["projects_generation_result"]
        await coll.insert_one({
            "user_id": user_id,
            "projects": [project.model_dump() for project in projects],
            "created_at": datetime.now(timezone.utc),
        })
    except Exception as e:
        logger.exception("Error storing project generation result")
        raise

