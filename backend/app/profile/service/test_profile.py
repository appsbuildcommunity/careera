import asyncio

from bson import ObjectId

from app.profile.service.profile import get_profile

USER_ID = str(ObjectId())


def test_get_profile_reads_users_document(fake_db):
    fake_db.users.docs.append(
        {
            "_id": ObjectId(USER_ID),
            "profile": {
                "cv_parsed_text": "Python backend",
                "linkedin_parsed_text": "API work",
                "interests": {"roles": ["Backend Engineer"], "focus_areas": ["AI"]},
            },
        }
    )

    profile = asyncio.run(get_profile(USER_ID))

    assert profile.cv_parsed_text == "Python backend"
    assert profile.linkedin_parsed_text == "API work"
    assert profile.interests == {"roles": ["Backend Engineer"], "focus_areas": ["AI"]}


def test_get_profile_missing_user_returns_empty(fake_db):
    profile = asyncio.run(get_profile(USER_ID))
    assert profile.cv_parsed_text is None
    assert profile.linkedin_parsed_text is None
    assert profile.interests is None


def test_get_profile_missing_profile_dict_returns_empty(fake_db):
    fake_db.users.docs.append({"_id": ObjectId(USER_ID)})
    profile = asyncio.run(get_profile(USER_ID))
    assert profile.cv_parsed_text is None
