import base64
import hashlib
import hmac
import secrets
import struct
from urllib.parse import quote, urlencode

SECRET_BYTES = 20
STEP_SECONDS = 30
DIGITS = 6
WINDOW = 1
ISSUER = "Центр ДПО"


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(SECRET_BYTES)).decode()


def decode(secret: str) -> bytes:
    cleaned = "".join(secret.split()).upper().rstrip("=")
    return base64.b32decode(cleaned + "=" * (-len(cleaned) % 8))


def code_at(secret: bytes, step: int) -> str:
    digest = hmac.new(secret, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % 10**DIGITS).zfill(DIGITS)


def current_step(now: float) -> int:
    return int(now // STEP_SECONDS)


def matching_step(secret: str, code: str, now: float, after_step: int) -> int | None:
    typed = "".join(code.split())
    if len(typed) != DIGITS or not typed.isdigit():
        return None
    key = decode(secret)
    step = current_step(now)
    for candidate in range(step - WINDOW, step + WINDOW + 1):
        if candidate > after_step and hmac.compare_digest(code_at(key, candidate), typed):
            return candidate
    return None


def provisioning_uri(secret: str, account: str) -> str:
    label = quote(f"{ISSUER}:{account}")
    query = urlencode({"secret": secret, "issuer": ISSUER, "digits": DIGITS, "period": STEP_SECONDS})
    return f"otpauth://totp/{label}?{query}"


def grouped(secret: str) -> str:
    return " ".join(secret[index : index + 4] for index in range(0, len(secret), 4))
