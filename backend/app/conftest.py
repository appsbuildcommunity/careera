from datetime import datetime
from typing import Any

import pytest
from bson import ObjectId


class FakeInsertResult:
    def __init__(self, inserted_id: ObjectId) -> None:
        self.inserted_id = inserted_id


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = docs

    def sort(self, key: str, direction: int) -> "FakeCursor":
        reverse = direction < 0
        self._docs = sorted(
            self._docs, key=lambda d: d.get(key) or datetime.min, reverse=reverse
        )
        return self

    async def __aiter__(self):
        for doc in self._docs:
            yield dict(doc)


class FakeCollection:
    def __init__(self, docs: list[dict[str, Any]] | None = None) -> None:
        self.docs = docs or []

    async def insert_one(self, doc: dict[str, Any]) -> FakeInsertResult:
        stored = dict(doc)
        stored["_id"] = ObjectId()
        self.docs.append(stored)
        return FakeInsertResult(stored["_id"])

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def find(self, query: dict[str, Any]) -> FakeCursor:
        matches = [
            d for d in self.docs if all(d.get(k) == v for k, v in query.items())
        ]
        return FakeCursor(matches)

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    doc.update(update["$set"])
                return


class FakeDB:
    def __init__(self) -> None:
        self.users = FakeCollection()
        self.analyses = FakeCollection()
        self.career_paths = FakeCollection()


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()

    async def _get_database() -> FakeDB:
        return db

    monkeypatch.setattr("app.database.connection.get_database", _get_database)
    monkeypatch.setattr("app.career.service.analysis.get_database", _get_database)
    monkeypatch.setattr("app.profile.service.profile.get_database", _get_database)
    return db
