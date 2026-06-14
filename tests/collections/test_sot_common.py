import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "wordpress-theme/skyyrose-flagship/data"
SCHEMA = DATA / "collections/identity.schema.json"


def test_schema_is_valid_jsonschema():
    import jsonschema

    schema = json.loads(SCHEMA.read_text())
    jsonschema.Draft202012Validator.check_schema(schema)  # raises if schema itself is malformed
    assert schema["required"]  # has required keys
