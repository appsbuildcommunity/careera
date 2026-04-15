from .connection import get_database
from datetime import datetime
from app.profile.model.analyse_profile import ProfileAnalysisResponse

async def store_analysis_result(user_id: str, analysis: ProfileAnalysisResponse) -> None:
    """Store the analysis result in MongoDB."""
    try:
        db = await get_database()
        coll = db["profiles_analyse_resulte"]
        await coll.insert_one({
               "user_id": user_id,
               "profile_summary": analysis.profile.profile_summary,
               "hard_skills": analysis.profile.hard_skills,
               "soft_skills": analysis.profile.soft_skills,
               "recommendations": [rec.model_dump() for rec in analysis.recommendations],
               "created_at": datetime.now(),
                   })
    except Exception as e:
        print(f"Error storing analysis result: {e}")
        raise e
