import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("secret")
        assert hashed != "secret"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # bcrypt uses random salt


class TestJWT:
    def test_encode_decode_roundtrip(self):
        token = create_access_token(subject=42)
        result = decode_access_token(token)
        assert result == "42"

    def test_decode_invalid_token_returns_none(self):
        assert decode_access_token("not.a.real.token") is None

    def test_decode_tampered_token_returns_none(self):
        token = create_access_token(subject=1)
        tampered = token[:-4] + "XXXX"
        assert decode_access_token(tampered) is None

    def test_string_subject(self):
        token = create_access_token(subject="user_abc")
        result = decode_access_token(token)
        assert result == "user_abc"
