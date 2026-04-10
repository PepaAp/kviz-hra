import base64
import hashlib
import re
import unicodedata
from typing import Optional


HINT_KEY = "kviz-secret-v1"


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encode_text(text: str) -> str:
    key = HINT_KEY.encode("utf-8")
    raw = text.encode("utf-8")
    return base64.b64encode(_xor_bytes(raw, key)).decode("ascii")


def decode_text(encoded: str) -> Optional[str]:
    if not encoded:
        return None
    try:
        key = HINT_KEY.encode("utf-8")
        raw = base64.b64decode(encoded.encode("ascii"))
        return _xor_bytes(raw, key).decode("utf-8")
    except Exception:
        return None


def encode_answer(text: str) -> str:
    return encode_text(text)


def decode_answer(encoded: str) -> Optional[str]:
    return decode_text(encoded)


def encode_value(text: str) -> str:
    return encode_text(text)


def decode_value(encoded: str) -> Optional[str]:
    return decode_text(encoded)


def normalize_answer(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = normalized.encode("ASCII", "ignore").decode("utf-8").lower()
    return re.sub(r"[^a-z0-9]", "", normalized)


def hash_answer(text: str) -> str:
    return hashlib.sha256(normalize_answer(text).encode("utf-8")).hexdigest()
