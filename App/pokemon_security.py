"""Application-level administrator PIN protection for Pokémon-Manager."""

from __future__ import annotations

import base64
import ctypes
import hashlib
import hmac
import json
import os
import time
from ctypes import POINTER, Structure, c_bool, c_uint32, c_void_p, c_wchar_p, cast
from pathlib import Path


POLICY_VERSION = 1
PIN_LENGTH = 4
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 60


class _DataBlob(Structure):
    _fields_ = [("cbData", c_uint32), ("pbData", POINTER(ctypes.c_ubyte))]


def _dpapi_available() -> bool:
    return os.name == "nt"


def _dpapi_protect(data: bytes) -> bytes:
    if not _dpapi_available():
        return data
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    input_buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(len(data), cast(input_buffer, POINTER(ctypes.c_ubyte)))
    output_blob = _DataBlob()
    crypt32.CryptProtectData.argtypes = [
        POINTER(_DataBlob),
        c_wchar_p,
        POINTER(_DataBlob),
        c_void_p,
        c_void_p,
        c_uint32,
        POINTER(_DataBlob),
    ]
    crypt32.CryptProtectData.restype = c_bool
    if not crypt32.CryptProtectData(
        ctypes.byref(input_blob), None, None, None, None, 0, ctypes.byref(output_blob)
    ):
        raise OSError("Windows-DPAPI konnte die PIN-Richtlinie nicht schützen.")
    try:
        return bytes(output_blob.pbData[: output_blob.cbData])
    finally:
        kernel32.LocalFree.argtypes = [c_void_p]
        kernel32.LocalFree.restype = c_void_p
        kernel32.LocalFree(output_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    if not _dpapi_available():
        return data
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    input_buffer = ctypes.create_string_buffer(data)
    input_blob = _DataBlob(len(data), cast(input_buffer, POINTER(ctypes.c_ubyte)))
    output_blob = _DataBlob()
    crypt32.CryptUnprotectData.argtypes = [
        POINTER(_DataBlob),
        POINTER(c_wchar_p),
        POINTER(_DataBlob),
        c_void_p,
        c_void_p,
        c_uint32,
        POINTER(_DataBlob),
    ]
    crypt32.CryptUnprotectData.restype = c_bool
    description = c_wchar_p()
    if not crypt32.CryptUnprotectData(
        ctypes.byref(input_blob),
        ctypes.byref(description),
        None,
        None,
        None,
        0,
        ctypes.byref(output_blob),
    ):
        raise OSError("Windows-DPAPI konnte die PIN-Richtlinie nicht lesen.")
    try:
        return bytes(output_blob.pbData[: output_blob.cbData])
    finally:
        kernel32.LocalFree.argtypes = [c_void_p]
        kernel32.LocalFree.restype = c_void_p
        kernel32.LocalFree(output_blob.pbData)
        if description:
            kernel32.LocalFree(description)


def _derive_pin(pin: str, salt: bytes, algorithm: str = "scrypt") -> bytes:
    encoded = pin.encode("utf-8")
    if algorithm == "scrypt" and hasattr(hashlib, "scrypt"):
        return hashlib.scrypt(encoded, salt=salt, n=2**14, r=8, p=1, dklen=32)
    return hashlib.pbkdf2_hmac("sha256", encoded, salt, 600_000, dklen=32)


class AdminPinManager:
    """Store and verify a four-digit app PIN without storing the PIN itself."""

    def __init__(self, policy_path: Path) -> None:
        self.policy_path = policy_path
        self.failed_attempts = 0
        self.locked_until = 0.0

    @property
    def configured(self) -> bool:
        return self.policy_path.is_file()

    @staticmethod
    def validate_pin(pin: str) -> bool:
        return len(pin) == PIN_LENGTH and pin.isascii() and pin.isdecimal()

    def set_pin(self, pin: str) -> None:
        if not self.validate_pin(pin):
            raise ValueError("Der Administrator-PIN muss genau vier Ziffern enthalten.")
        salt = os.urandom(16)
        algorithm = "scrypt" if hasattr(hashlib, "scrypt") else "pbkdf2-sha256"
        verifier = _derive_pin(pin, salt, algorithm)
        payload = {
            "policy_version": POLICY_VERSION,
            "algorithm": algorithm,
            "salt": base64.b64encode(salt).decode("ascii"),
            "verifier": base64.b64encode(verifier).decode("ascii"),
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        protected = _dpapi_protect(raw)
        record = {
            "policy_version": POLICY_VERSION,
            "protection": "windows-dpapi" if _dpapi_available() else "salted-kdf",
            "payload": base64.b64encode(protected).decode("ascii"),
        }
        self.policy_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.policy_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.policy_path)
        self.failed_attempts = 0
        self.locked_until = 0.0

    def _load_payload(self) -> dict:
        record = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if record.get("policy_version") != POLICY_VERSION:
            raise ValueError("Nicht unterstützte Administrator-Richtlinie.")
        protected = base64.b64decode(record["payload"])
        payload = json.loads(_dpapi_unprotect(protected).decode("utf-8"))
        if payload.get("policy_version") != POLICY_VERSION:
            raise ValueError("Nicht unterstützte Administrator-Richtlinie.")
        return payload

    def verify(self, pin: str) -> tuple[bool, str]:
        now = time.monotonic()
        if now < self.locked_until:
            remaining = max(1, int(self.locked_until - now))
            return False, f"Zu viele Fehlversuche. Bitte {remaining} Sekunden warten."
        if not self.validate_pin(pin):
            return False, "Der Administrator-PIN muss genau vier Ziffern enthalten."
        try:
            payload = self._load_payload()
            salt = base64.b64decode(payload["salt"])
            expected = base64.b64decode(payload["verifier"])
            actual = _derive_pin(pin, salt, payload.get("algorithm", "scrypt"))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return False, "Die Administrator-Richtlinie ist beschädigt oder nicht lesbar."
        if hmac.compare_digest(actual, expected):
            self.failed_attempts = 0
            return True, ""
        self.failed_attempts += 1
        if self.failed_attempts >= MAX_FAILED_ATTEMPTS:
            self.locked_until = time.monotonic() + LOCKOUT_SECONDS
            self.failed_attempts = 0
        return False, "Falscher Administrator-PIN."
