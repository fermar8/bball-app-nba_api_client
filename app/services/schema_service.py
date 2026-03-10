import json
from pathlib import Path

from jsonschema import ValidationError, validate

_SCHEMA_CACHE: dict[str, dict] = {}


def get_json_schema(endpoint_name: str) -> dict:
    if endpoint_name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[endpoint_name]

    schema_path = Path(__file__).resolve().parents[2] / 'docs' / 'schemas' / f'{endpoint_name}.schema.json'
    if not schema_path.exists():
        raise ValueError(f'No schema file found for endpoint: {endpoint_name}')

    with schema_path.open('r', encoding='utf-8') as schema_file:
        schema = json.load(schema_file)
        _SCHEMA_CACHE[endpoint_name] = schema
        return schema


def validate_payload_for_endpoint(endpoint_name: str, payload: dict | list) -> None:
    schema = get_json_schema(endpoint_name)
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        raise ValueError(f'Invalid payload for {endpoint_name}: {exc.message}') from exc
