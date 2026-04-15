import logging
from datetime import datetime, timezone

from pydantic import ValidationError

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
    except Exception:
        logger.exception("Error storing project generation result")
        raise


async def get_generated_project_by_id(user_id: str, project_id: str) -> ProjectSeed | None:
    """Get one generated project seed by user and project id from latest matching generation result."""
    db = await get_database()
    coll = db["projects_generation_result"]

    doc = await coll.find_one(
        {"user_id": user_id, "projects.project_id": project_id},
        {"projects.$": 1},
        sort=[("created_at", -1)],
    )

    if not doc:
        return None

    projects = doc.get("projects", [])
    if not isinstance(projects, list) or not projects:
        return None

    project = projects[0]
    if not isinstance(project, dict):
        return None

    try:
        return ProjectSeed(**project)
    except ValidationError:
        return None


async def store_expanded_project(user_id: str, project: ProjectSeed) -> None:
    """Store the expanded project in MongoDB."""
    try:
        db = await get_database()
        coll = db["expanded_projects"]
        await coll.insert_one({
            "user_id": user_id,
            "project": project.model_dump(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })
    except Exception:
        logger.exception("Error storing expanded project")
        raise

async def update_expanded_project(user_id: str, project: ProjectSeed) -> None:
    """Update the expanded project in MongoDB."""
    try:
        db = await get_database()
        coll = db["expanded_projects"]
        await coll.update_one(
            {"user_id": user_id, "project.project_id": project.project_id},
            {"$set": {
                "project": project.model_dump(),
                "updated_at": datetime.now(timezone.utc),
            }},
            upsert=True
        )
    except Exception:
        logger.exception("Error updating expanded project")
        raise
