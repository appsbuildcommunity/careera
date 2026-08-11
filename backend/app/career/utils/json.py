from typing import Any, Optional

from bson import ObjectId


def to_object_id(value: str) -> ObjectId:
    """Convert a 24-hex Mongo id string to :class:`ObjectId`.

    Raises ``ValueError`` for invalid values so callers can return the
    documented not-found error.
    """
    try:
        return ObjectId(value)
    except Exception as exc:
        raise ValueError(f"Invalid ObjectId: {value}") from exc


def object_id_str(value: Any) -> Optional[str]:
    """Serialize an ``ObjectId`` (or ``None``) to ``str`` for API responses."""
    if value is None:
        return None
    return str(value)
