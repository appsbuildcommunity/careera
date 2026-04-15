from typing import Any
import json
import re

def extract_json_payload(raw_response: str) -> dict[str, Any]:
    cleaned = raw_response.strip()

    fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        cleaned = fenced_match.group(1).strip()

    json_start = cleaned.find("{")
    json_end = cleaned.rfind("}")

    if json_start == -1 or json_end == -1:
        raise ValueError("No JSON object found")

    cleaned = cleaned[json_start : json_end + 1]

    return json.loads(cleaned)

