import re

from anonymizer_core import (
    DEFAULT_HASH_LENGTH,
    anonymize,
    build_mappings_from_lines,
    decode_text,
    encode_text,
    serialize_new_mappings,
)

HEX_RE = re.compile(r"^[0-9a-f]+$")


def test_anonymize_hex_length_default():
    token = anonymize("irrelevant", length=DEFAULT_HASH_LENGTH)
    assert len(token) == DEFAULT_HASH_LENGTH
    # anonymizer_core anonymize() nutzt token_hex -> hex-Zeichen
    assert HEX_RE.match(token)


def test_build_and_serialize_roundtrip():
    text = "ABCD1234 = Alice\nEFGH5678 = Bob\n"
    h2o, o2h = build_mappings_from_lines(text)
    assert o2h["Alice"] == "ABCD1234"
    assert h2o["EFGH5678"] == "Bob"
    out = serialize_new_mappings({"ZZZZ9999": "Charlie"})
    assert out.strip() == "ZZZZ9999 = Charlie"


def test_encode_decode_text():
    # Start ohne Mapping
    h2o = {}
    o2h = {}
    src = "Hallo [[Alice]]. Alice trifft Bob."
    encoded, h2o_upd, created = encode_text(src, h2o, o2h, hash_length=8)
    # Beide Namen sollten ersetzt sein, Alice sicher; Bob nur wenn in Mapping (hier: nein)
    # Da encode_text zuerst markierte Token ins Mapping übernimmt, Alice wird ersetzt.
    assert "Alice" not in encoded
    # known hashes -> zurückdecodierbar
    decoded = decode_text(encoded, h2o_upd, hash_length=8)
    assert "Alice" in decoded
