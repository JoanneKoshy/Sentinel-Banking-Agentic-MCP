"""
PII Redaction utility.

Used to sanitize data before it hits logs/traces - account numbers,
phone numbers, addresses, and auth tokens should never sit in plaintext
logs, even though the customer sees their own real data in the actual
chat response. Logging is a separate concern from the response itself.
"""

import re

_TOKEN_PATTERN = re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")
_PHONE_PATTERN = re.compile(r"\b(\d{2})\d{6}(\d{2})\b")

# Keys that should always be fully redacted in logs, regardless of value shape.
_SENSITIVE_KEYS = {
    "auth_token",
    "token",
    "phone_number",
    "account_number",
    "new_address",
    "details",
}


def _redact_string(text: str) -> str:
    text = _TOKEN_PATTERN.sub("[REDACTED_TOKEN]", text)
    text = _PHONE_PATTERN.sub(r"\1XXXXXX\2", text)
    return text


def redact_for_log(data):
    """
    Recursively redact sensitive fields from a dict/list/str, returning a
    safe-to-log copy. Does NOT modify the original data - only used when
    writing to logs, never applied to the actual response sent to the user.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in _SENSITIVE_KEYS:
                result[key] = "[REDACTED]"
            else:
                result[key] = redact_for_log(value)
        return result

    if isinstance(data, list):
        return [redact_for_log(item) for item in data]

    if isinstance(data, str):
        return _redact_string(data)

    return data