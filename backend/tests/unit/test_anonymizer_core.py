import re
from anonymizer_core import (
    anonymize, encode_text, decode_text,
    build_mappings_from_lines, serialize_new_mappings, DEFAULT_HASH_LENGTH
)

HEX_RE = re.compile(r"^[0-9a-f]+$")

def test_anonymize_hex_length_default():
    token = anonymize("ignored", length=DEFAULT_HASH_LENGTH)
    assert len(token) == DEFAULT_HASH_LENGTH
    assert HEX_RE.match(token)

def test_build_and_serialize_roundtrip():
    text = "ABCD1234 = Alice\nEFGH5678 = Bob\n"
    h2o, o2h = build_mappings_from_lines(text)
    assert o2h["Alice"] == "ABCD1234"
    assert h2o["EFGH5678"] == "Bob"
    out = serialize_new_mappings({"ZZZZ9999": "Charlie"})
    assert out.strip() == "ZZZZ9999 = Charlie"

def test_encode_decode_text():
    h2o, o2h = {}, {}
    src = "Hallo [[Alice]]. Alice trifft Bob."
    encoded, h2o_upd, _created = encode_text(src, h2o, o2h, hash_length=8)
    assert "Alice" not in encoded
    decoded = decode_text(encoded, h2o_upd, hash_length=8)
    assert "Alice" in decoded
