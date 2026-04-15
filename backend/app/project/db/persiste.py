from datetime import datetime, timezone
from app.database.connection import get_database
from app.project.model.project_generation import ProjectSeed

async def store_projects_generation_result(user_id: str, projects: list[ProjectSeed]) -> None:
    """Store the generated projects in MongoDB."""
    try:
        db = await get_database()
        coll = db["projects_generation_result"]
        await coll.insert_many({
               "user_id": user_id,
               "projects": [project.model_dump() for project in projects],
               "created_at": datetime.now(timezone.utc),
               })
    except Exception as e:
        print(f"Error storing project generation result: {e}")
        raise e

