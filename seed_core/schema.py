"""Validation and canonical encoding for SEED records."""

from datetime import date
from hashlib import sha256
import json
import re
from pathlib import PurePosixPath
import unicodedata
from urllib.parse import urlsplit
from uuid import UUID

VERSION = 1
MAX_BYTES = 16 * 1024 * 1024
LEVELS = ("public", "internal", "confidential", "restricted")
ORIGINS = {"verified_external", "founder", "assumption", "estimate",
           "hypothesis", "calculated", "unknown"}
VALIDATION = {"draft", "reviewed", "approved", "disputed"}
KINDS = {
    "venture": ("name", "currency", "jurisdiction"),
    "source": ("title", "publisher", "retrieved_on"),
    "evidence": ("excerpt", "assessment"),
    "claim": ("statement",),
    "assumption": ("label", "value", "unit", "rationale"),
    "calculation": ("label", "value", "unit", "method"),
    "market": ("name",),
    "competitor": ("name",),
    "financial_model": ("name", "currency"),
    "investor": ("name",),
    "investment_firm": ("name",),
    "contact": ("name",),
    "relationship": ("description",),
    "funding_opportunity": ("name", "programme_type"),
    "interaction": ("summary", "occurred_on"),
    "fundraising_opportunity": ("name", "stage"),
    "technical_milestone": ("name", "status"),
    "document": ("name", "document_type"),
    "decision": ("summary",),
    "legacy": ("filename", "sha256", "document"),
}
LINK_ROLES = {
    "source": {"source"}, "evidence": {"evidence"}, "contradicts": {"evidence", "claim"},
    "assumption": {"assumption"}, "calculation": {"calculation"},
    "dependency": set(KINDS),
}
EXPORT_SECRET = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:gh[pousr]_|github_pat_|sk-(?:proj-)?|xox[baprs]-)[A-Za-z0-9_-]{24,}"
)
SECRET_FIELDS = {"api_key", "access_token", "refresh_token", "password", "private_key", "client_secret"}


class SeedError(ValueError):
    """Invalid input, workspace state or requested operation."""


def require(condition, error):
    if not condition:
        raise SeedError(error)


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise SeedError("Data must be finite, serializable JSON") from error


def digest(value):
    return sha256(canonical(value)).hexdigest()


def parse_json(data):
    def pairs(entries):
        result = {}
        for key, value in entries:
            require(key not in result, "Duplicate JSON object key")
            result[key] = value
        return result

    def invalid(_value):
        raise SeedError("Non-finite JSON number")

    require(len(data) <= MAX_BYTES, "JSON exceeds the workspace transfer size limit")
    try:
        value = json.loads(data, object_pairs_hook=pairs, parse_constant=invalid)
        canonical(value)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise SeedError("Malformed JSON") from error


def string(value, name, limit=2000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, f"Invalid {name}")
    return value.strip()


def date_value(value, field):
    try:
        day = date.fromisoformat(value)
        if day.isoformat() == value:
            return day
    except (TypeError, ValueError):
        pass
    raise SeedError(f"Invalid {field}, expected YYYY-MM-DD")


def identifier(value):
    try:
        require(str(UUID(value)) == value, "Invalid identifier")
    except (ValueError, TypeError, AttributeError) as error:
        raise SeedError("Invalid identifier") from error
    return value


def key_value(value):
    raw = string(value, "record key", 150)
    normalized = unicodedata.normalize("NFKC", raw)
    forbid_secrets(raw)
    forbid_secrets(normalized)
    return " ".join(normalized.casefold().split())


def relative_document(value):
    raw = value
    value = string(value, "document reference")
    path = PurePosixPath(value)
    names = value.split("/")
    reserved = r"(?:CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])"
    require(raw == value and not path.is_absolute() and not any(x in value for x in ("\\", ":", "\x00"))
            and all(part not in {"", ".", ".."} and not part.endswith((".", " "))
                    and not re.fullmatch(reserved, part.split(".", 1)[0], re.I) for part in names),
            "Document reference must be a safe relative path")
    return value


def forbid_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            require(key.casefold().replace("-", "_") not in SECRET_FIELDS or item in (None, ""),
                    "Secret-bearing fields cannot enter the venture store")
            forbid_secrets(item)
    elif isinstance(value, list):
        for item in value:
            forbid_secrets(item)
    elif isinstance(value, str):
        require(not EXPORT_SECRET.search(value), "Credential-like material cannot enter the venture store")


def validate_config(data):
    require(isinstance(data, dict), "Venture configuration must be an object")
    require(set(data) == {"name", "currency", "jurisdiction"}, "Invalid venture configuration fields")
    forbid_secrets(data)
    string(data["name"], "name", 150)
    string(data["jurisdiction"], "jurisdiction", 100)
    require(isinstance(data["currency"], str) and re.fullmatch(r"[A-Z]{3}", data["currency"]),
            "Currency must be a three-letter uppercase currency code")


def validate_record(kind, data, provenance, classification, status, links):
    require(isinstance(kind, str) and kind in KINDS and isinstance(data, dict), "Unknown record kind or invalid record data")
    require(all(isinstance(x, str) for x in (provenance, classification, status))
            and provenance in ORIGINS and classification in LEVELS and status in VALIDATION,
            "Invalid provenance, classification or validation status")
    require(isinstance(links, list), "Links must be an array")
    for field in KINDS[kind]:
        require(field in data, f"{kind} requires {field}")
        if field not in {"value", "document"}:
            string(data[field], field, 10_000 if field in {"excerpt", "statement"} else 2000)
    forbid_secrets(data)
    if kind == "venture":
        validate_config(data)
    if "currency" in data:
        require(isinstance(data["currency"], str) and re.fullmatch(r"[A-Z]{3}", data["currency"]),
                "Invalid currency")
    for field in ("retrieved_on", "published_on", "valid_until", "occurred_on", "deadline"):
        if data.get(field) is not None:
            date_value(data[field], field)
    if kind == "source":
        require(bool(data.get("url")) != bool(data.get("document_ref")),
                "Source requires one URL or local document reference")
        if data.get("url"):
            try:
                target = urlsplit(string(data["url"], "source URL"))
            except ValueError as error:
                raise SeedError("Invalid public source URL") from error
            require(target.scheme in {"http", "https"} and target.hostname and not target.username
                    and not target.password, "Invalid public source URL")
        if data.get("published_on"):
            require(data["published_on"] <= data["retrieved_on"], "Source published after retrieval")
    if "document_ref" in data:
        relative_document(data["document_ref"])
        require(classification != "public", "Local document references require a private classification")
    if "max_age_days" in data:
        require(type(data["max_age_days"]) is int and 0 <= data["max_age_days"] <= 36500,
                "Invalid source maximum age")
    if kind == "legacy":
        require(isinstance(data["document"], dict) and re.fullmatch(r"[a-f0-9]{64}", data["sha256"]),
                "Invalid legacy snapshot")
    if "confidence" in data:
        value = data["confidence"]
        require(type(value) in (int, float) and 0 <= value <= 1, "Confidence must be between 0 and 1")
    seen = set()
    for link in links:
        require(isinstance(link, dict) and set(link) == {"id", "revision", "role"}, "Invalid link fields")
        identifier(link["id"])
        require(type(link["revision"]) is int and link["revision"] > 0 and isinstance(link["role"], str) and link["role"] in LINK_ROLES,
                "Invalid link revision or role")
        fingerprint = (link["id"], link["revision"], link["role"])
        require(fingerprint not in seen, "Duplicate record link")
        seen.add(fingerprint)
    roles = {link["role"] for link in links}
    if kind == "evidence":
        require("source" in roles, "Evidence requires a pinned source")
    if kind == "claim" and provenance == "verified_external":
        require("evidence" in roles and status in {"reviewed", "approved", "disputed"},
                "Verified external claims require reviewed evidence")
    if provenance == "calculated":
        require(roles & {"assumption", "calculation", "dependency"},
                "Calculated records require a pinned input")
    canonical(data)
