from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel

from app.database.connection import get_database


class ProfileData(BaseModel):
    """Parsed profile fields read from the ``users`` document."""

    cv_parsed_text: Optional[str] = None
    linkedin_parsed_text: Optional[str] = None
    interests: Optional[dict[str, Any]] = None


async def get_profile(user_id: str) -> ProfileData:
    """Return the user's parsed profile fields.

    A missing user document yields an empty :class:`ProfileData`; callers such
    as career analysis surface the documented ``PROFILE_INCOMPLETE`` error.
    """
    db = await get_database()
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        return ProfileData()
    profile = user.get("profile") or {}
    return ProfileData(
        cv_parsed_text=profile.get("cv_parsed_text"),
        linkedin_parsed_text=profile.get("linkedin_parsed_text"),
        interests=profile.get("interests"),
    )
