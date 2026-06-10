import pytest

from ledge_lang.confidence import (
    CanonicalSerializationError,
    hash_bytes,
    hash_dict,
    hash_text,
    sha256_text,
    stable_json_dumps,
)


def test_stable_json_dumps_sorts_keys_and_is_compact():
    assert stable_json_dumps({"b": 2, "a": 1}) == '{"a":1,"b":2}'


def test_stable_json_dumps_rejects_nan():
    with pytest.raises(CanonicalSerializationError):
        stable_json_dumps({"score": float("nan")})


def test_hash_helpers_are_stable_lowercase_sha256():
    assert sha256_text("x") == hash_text("x")
    assert hash_dict({"b": 2, "a": 1}) == hash_dict({"a": 1, "b": 2})
    assert hash_bytes(b"x") == hash_text("x")
    assert len(hash_text("x")) == 64
    assert hash_text("x") == hash_text("x").lower()
