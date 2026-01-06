import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


def validate_json_response(
    content: str, model: Type[T], raise_on_error: bool = True
) -> T | None:
    """
    Validate JSON content against a Pydantic model.

    Args:
        content: JSON string to validate
        model: Pydantic model class to validate against
        raise_on_error: Whether to raise an exception on validation failure

    Returns:
        Validated model instance or None if validation fails and raise_on_error is False
    """
    try:
        data = json.loads(content)
        return model.model_validate(data)
    except json.JSONDecodeError as e:
        if raise_on_error:
            raise ValueError(f"Invalid JSON: {e}")
        return None
    except ValidationError as e:
        if raise_on_error:
            raise ValueError(f"Schema validation failed: {e}")
        return None


def extract_json_from_text(text: str) -> str | None:
    """
    Extract JSON from text that may contain markdown code blocks.

    Args:
        text: Text that may contain JSON in code blocks

    Returns:
        Extracted JSON string or None if not found
    """
    # Check for markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    # Try to find raw JSON
    for start_char, end_char in [("{", "}"), ("[", "]")]:
        start = text.find(start_char)
        if start >= 0:
            depth = 0
            for i, char in enumerate(text[start:], start):
                if char == start_char:
                    depth += 1
                elif char == end_char:
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]

    return None
