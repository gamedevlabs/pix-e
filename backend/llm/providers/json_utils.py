"""
Shared JSON utilities for LLM providers.
"""

import json
from typing import Any, Dict, Optional


def get_schema(response_schema: type) -> Dict[str, Any]:
    if hasattr(response_schema, "model_json_schema"):
        return response_schema.model_json_schema()
    if hasattr(response_schema, "schema"):
        return response_schema.schema()
    return {"type": "object"}


def schema_to_string(schema: Dict[str, Any]) -> str:
    return json.dumps(schema, indent=2)


def format_json_prompt(prompt: str, schema_str: Optional[str]) -> str:
    if schema_str:
        return (
            f"{prompt}\n\n"
            "You must respond with valid JSON matching this schema:\n"
            f"{schema_str}\n\n"
            "Respond only with the JSON object, no additional text."
        )
    return f"{prompt}\n\n" "Respond with valid JSON only, no additional text."


def strip_markdown_json(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        start_idx = content.find("\n")
        if start_idx != -1:
            content = content[start_idx + 1 :]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
    return content


def parse_and_validate_json(content: str, response_schema: type) -> Any:
    parsed_data = json.loads(content)
    if hasattr(response_schema, "model_validate"):
        return response_schema.model_validate(parsed_data)
    if callable(response_schema):
        return response_schema(**parsed_data)
    return parsed_data
