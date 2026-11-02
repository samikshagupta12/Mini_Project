"""Unit tests for secure authentication and password hashing."""
import pytest
from utils.auth import hash_password, verify_password


def test_password_hashing_and_verification():
    pw = "SuperSecureP@ss123"
    hashed = hash_password(pw)

    # Must contain salt and digest separated by $
    assert "$" in hashed
    salt, digest = hashed.split("$", 1)
    assert len(salt) == 32  # 16 bytes in hex
    assert len(digest) == 64  # sha256 hex is 64 chars

    # Correct password verification
    assert verify_password(pw, hashed) is True

    # Incorrect password verification
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_password_salt_uniqueness():
    pw = "SamePassword123"
    hash1 = hash_password(pw)
    hash2 = hash_password(pw)

    # Different salts must result in different hashes
    assert hash1 != hash2
    assert verify_password(pw, hash1) is True
    assert verify_password(pw, hash2) is True


def test_verify_password_malformed_input():
    assert verify_password("test", "") is False
    assert verify_password("test", "no_dollar_sign") is False
    assert verify_password("test", None) is False

