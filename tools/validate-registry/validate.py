#!/usr/bin/env python3
"""
KUEPER Ecosystem — Project-Registry-Validator

Prueft registry/projects.json gegen schemas/project-registry.schema.json.
Nur stdlib, kein jsonschema-Paket, kein Netzwerk (Projektprinzip, vgl.
tools/lint-external-tasks/lint.py). Exit 1 bei Verstoss (CI-tauglich).

Eine ungueltige Registry muss den Collector stoppen und darf keinen
gruenen Status erzeugen (registry/README.md, Abschnitt "Validierung").

Nutzung:
  python3 tools/validate-registry/validate.py [<registry.json>]

Der Auswerter implementiert genau die JSON-Schema-2020-12-Teilmenge, die
das Project-Registry-Schema verwendet: type, enum, const, required,
properties, additionalProperties, minLength, pattern, format (date, uri),
items, minItems, uniqueItems, $ref (innerhalb $defs), allOf, if/then/else.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = _HERE / ".." / ".." / "schemas" / "project-registry.schema.json"
DEFAULT_REGISTRY = _HERE / ".." / ".." / "registry" / "projects.json"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


def _type_name(value):
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _is_type(value, wanted):
    if wanted == "null":
        return value is None
    if wanted == "boolean":
        return isinstance(value, bool)
    if wanted == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if wanted == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if wanted == "string":
        return isinstance(value, str)
    if wanted == "array":
        return isinstance(value, list)
    if wanted == "object":
        return isinstance(value, dict)
    return False


def _deep_eq(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(_deep_eq(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(_deep_eq(x, y) for x, y in zip(a, b))
    return a == b


def _valid_date(value):
    m = _DATE_RE.match(value)
    if not m:
        return False
    try:
        date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
        return True
    except ValueError:
        return False


def _valid_uri(value):
    m = _URI_SCHEME_RE.match(value)
    return bool(m) and len(value) > m.end()


_FORMAT_CHECKS = {"date": _valid_date, "uri": _valid_uri}


def _errors(schema, instance, path, refs):
    """Rekursiver Auswerter; liefert Liste (pfad, meldung)."""
    errs = []
    if not isinstance(schema, dict):
        return errs

    ref = schema.get("$ref")
    if ref is not None:
        target = refs.get(ref)
        if target is None:
            errs.append((path, f"unaufgeloester $ref {ref}"))
        else:
            errs.extend(_errors(target, instance, path, refs))
        return errs  # 2020-12: $ref ersetzt Geschwister-Keys

    if "type" in schema:
        wanted = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(instance, t) for t in wanted):
            errs.append((path, f"Typ erwartet {schema['type']}, erhalten {_type_name(instance)}"))

    if "enum" in schema and instance not in schema["enum"]:
        errs.append((path, f"Wert {instance!r} nicht in enum {schema['enum']}"))
    if "const" in schema and instance != schema["const"]:
        errs.append((path, f"const {schema['const']!r} erwartet, erhalten {instance!r}"))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errs.append((path, f"kuerzer als minLength {schema['minLength']}"))
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errs.append((path, f"matcht pattern nicht: {schema['pattern']!r}"))
        if "format" in schema:
            check = _FORMAT_CHECKS.get(schema["format"])
            if check is not None and not check(instance):
                errs.append((path, f"kein gueltiges {schema['format']}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errs.append((path, f"weniger als minItems {schema['minItems']}"))
        if schema.get("uniqueItems"):
            for i, item in enumerate(instance):
                if any(_deep_eq(item, other) for other in instance[:i]):
                    errs.append((path, "Array-Elemente nicht eindeutig"))
                    break
        if "items" in schema:
            for i, item in enumerate(instance):
                errs.extend(_errors(schema["items"], item, f"{path}[{i}]", refs))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errs.append((path, f"Pflichtfeld fehlt: {key!r}"))
        props = schema.get("properties", {})
        for key, subschema in props.items():
            if key in instance:
                sub_path = f"{path}.{key}" if path else key
                errs.extend(_errors(subschema, instance[key], sub_path, refs))
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errs.append((path, f"unzulaessiges Zusatzfeld: {key!r}"))

    for i, sub in enumerate(schema.get("allOf", [])):
        errs.extend(_errors(sub, instance, f"{path} (allOf[{i}])", refs))
    if "anyOf" in schema and not any(not _errors(s, instance, path, refs) for s in schema["anyOf"]):
        errs.append((path, "erfuellt anyOf nicht"))
    if "oneOf" in schema:
        matched = sum(1 for s in schema["oneOf"] if not _errors(s, instance, path, refs))
        if matched != 1:
            errs.append((path, f"oneOf: {matched} Zweige erfuellt (erwartet 1)"))
    if "if" in schema:
        cond_errors = _errors(schema["if"], instance, path, refs)
        if not cond_errors:
            if "then" in schema:
                errs.extend(_errors(schema["then"], instance, path, refs))
        elif "else" in schema:
            errs.extend(_errors(schema["else"], instance, path, refs))

    return errs


def validate_document(document, schema_path):
    """Liefert Liste (pfad, meldung) fuer document gegen das Schema."""
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    refs = {f"#/$defs/{name}": sub for name, sub in schema.get("$defs", {}).items()}
    return _errors(schema, document, "$", refs)


def validate_file(registry_path, schema_path):
    with open(registry_path, encoding="utf-8") as f:
        document = json.load(f)
    return validate_document(document, schema_path)


def main(argv):
    registry_path = Path(argv[0]) if argv else DEFAULT_REGISTRY
    try:
        errors = validate_file(registry_path, DEFAULT_SCHEMA)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL {registry_path}: {e}")
        return 1
    if errors:
        print(f"FAIL {registry_path}")
        for path, msg in errors:
            print(f"     - {path}: {msg}")
        return 1
    print(f"OK   {registry_path} gegen {DEFAULT_SCHEMA}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
