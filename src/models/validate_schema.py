"""
Uses schema.py Pydantic models to validate raw model output.
Handles markdown fence stripping and JSON parsing failures gracefully.
"""

import json
import re
from pydantic import ValidationError
from .schema import DrawingAnalysis


def validate_output(raw_json_str: str) -> tuple[DrawingAnalysis | None, list[str]]:
    """
    Parse and validate a raw model response string against the DrawingAnalysis schema.
    Returns (validated_model, []) on success, or (None, [error_messages]) on failure.
    """
    cleaned = _strip_fences(raw_json_str)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, [f"JSON parse error: {e}"]

    try:
        model = DrawingAnalysis.model_validate(data)
        return model, []
    except ValidationError as e:
        errors = [f"{' -> '.join(str(x) for x in err['loc'])}: {err['msg']}" for err in e.errors()]
        return None, errors


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()
