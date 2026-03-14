import hashlib
import hmac
import uuid
from typing import Dict, Optional

from app.core.config import settings


_PUA_BASE = 0xE000
_PUA_MAX = 0xE0FF
_PLACEHOLDER_SECRETS = {
    "",
    "change-me",
    "change-me-32-char-min-key",
    "change-me-hash-pepper",
}
SENSITIVE_PII_FIELDS = (
    "full_name",
    "phone",
    "address_line1",
    "address_line2",
    "city",
    "district",
    "postal_code",
)


def _to_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _looks_like_ciphertext(value: str) -> bool:
    if not value:
        return False
    for char in value:
        codepoint = ord(char)
        if codepoint < _PUA_BASE or codepoint > _PUA_MAX:
            return False
    return True


class PIIProtector:
    def __init__(self, encryption_key: str, hash_pepper: str = ""):
        key = (encryption_key or "").strip()
        pepper = (hash_pepper or "").strip()

        self.enabled = key not in _PLACEHOLDER_SECRETS and len(key) >= 16
        if not self.enabled:
            self._master_key = b""
            return

        secret_material = f"{key}:{pepper}".encode("utf-8")
        self._master_key = hashlib.sha256(secret_material).digest()

    def _context(self, user_id: uuid.UUID, field_name: str) -> bytes:
        return f"{user_id}:{field_name}".encode("utf-8")

    def _keystream(self, context: bytes, length: int) -> bytes:
        chunks = []
        counter = 0
        generated = 0
        while generated < length:
            block = hmac.new(
                self._master_key,
                context + counter.to_bytes(4, byteorder="big"),
                hashlib.sha256,
            ).digest()
            chunks.append(block)
            generated += len(block)
            counter += 1
        return b"".join(chunks)[:length]

    def encrypt(self, value: Optional[str], user_id: uuid.UUID, field_name: str) -> Optional[str]:
        plain = _to_text(value)
        if plain is None or plain == "":
            return plain
        if not self.enabled:
            return plain

        raw = plain.encode("utf-8")
        keystream = self._keystream(self._context(user_id, field_name), len(raw))
        cipher_bytes = bytes(raw[i] ^ keystream[i] for i in range(len(raw)))
        return "".join(chr(_PUA_BASE + byte) for byte in cipher_bytes)

    def decrypt(self, value: Optional[str], user_id: uuid.UUID, field_name: str) -> Optional[str]:
        cipher = _to_text(value)
        if cipher is None or cipher == "":
            return cipher
        if not self.enabled:
            return cipher
        if not _looks_like_ciphertext(cipher):
            return cipher

        cipher_bytes = bytes(ord(char) - _PUA_BASE for char in cipher)
        keystream = self._keystream(self._context(user_id, field_name), len(cipher_bytes))
        plain_bytes = bytes(cipher_bytes[i] ^ keystream[i] for i in range(len(cipher_bytes)))
        try:
            return plain_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return cipher


pii_protector = PIIProtector(
    encryption_key=settings.kvkk_encryption_key,
    hash_pepper=settings.kvkk_hash_pepper,
)


def protect_user_pii_payload(user_id: uuid.UUID, payload: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    protected = dict(payload)
    for field_name in SENSITIVE_PII_FIELDS:
        protected[field_name] = pii_protector.encrypt(protected.get(field_name), user_id, field_name)
    return protected


def reveal_user_pii_payload(user_id: uuid.UUID, payload: Dict[str, Optional[str]]) -> Dict[str, Optional[str]]:
    revealed = dict(payload)
    for field_name in SENSITIVE_PII_FIELDS:
        revealed[field_name] = pii_protector.decrypt(revealed.get(field_name), user_id, field_name)
    return revealed

