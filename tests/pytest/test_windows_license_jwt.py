"""JWT license verification logic (cross-platform; no Windows registry)."""

from __future__ import annotations

import jwt
import pytest
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from webserver import windows_license


def _rsa_pem_pair():
    priv = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend(),
    )
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def test_verify_license_accepts_matching_fp(tmp_path, monkeypatch):
    priv_pem, pub_pem = _rsa_pem_pair()
    fp = "a" * 64
    token = jwt.encode({"fp": fp}, priv_pem, algorithm="RS256")
    token_str = token if isinstance(token, str) else token.decode("ascii")

    lic_path = tmp_path / "openplc.license"
    pub_path = tmp_path / "license_public.pem"
    lic_path.write_text(token_str, encoding="utf-8")
    pub_path.write_bytes(pub_pem)

    monkeypatch.setenv("OPENPLC_LICENSE_FILE", str(lic_path))
    monkeypatch.setenv("OPENPLC_LICENSE_PUBLIC_KEY", str(pub_path))
    monkeypatch.setattr(windows_license, "compute_hardware_fingerprint", lambda: fp)

    ok, msg = windows_license.verify_license(tmp_path)
    assert ok is True
    assert "valid" in msg.lower()


def test_verify_license_rejects_wrong_fp(tmp_path, monkeypatch):
    priv_pem, pub_pem = _rsa_pem_pair()
    token = jwt.encode({"fp": "b" * 64}, priv_pem, algorithm="RS256")
    token_str = token if isinstance(token, str) else token.decode("ascii")

    lic_path = tmp_path / "openplc.license"
    pub_path = tmp_path / "license_public.pem"
    lic_path.write_text(token_str, encoding="utf-8")
    pub_path.write_bytes(pub_pem)

    monkeypatch.setenv("OPENPLC_LICENSE_FILE", str(lic_path))
    monkeypatch.setenv("OPENPLC_LICENSE_PUBLIC_KEY", str(pub_path))
    monkeypatch.setattr(windows_license, "compute_hardware_fingerprint", lambda: "c" * 64)

    ok, msg = windows_license.verify_license(tmp_path)
    assert ok is False
    assert "fingerprint" in msg.lower() or "match" in msg.lower()


@pytest.mark.parametrize(
    "plat",
    ["win32", "msys", "cygwin"],
)
def test_is_windows_runtime_positive(plat, monkeypatch):
    monkeypatch.setattr(windows_license.sys, "platform", plat)
    assert windows_license.is_windows_runtime() is True


def test_is_windows_runtime_linux(monkeypatch):
    monkeypatch.setattr(windows_license.sys, "platform", "linux")
    assert windows_license.is_windows_runtime() is False
