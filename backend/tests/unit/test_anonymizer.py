from pathlib import Path

from anonymizer import decode_text, encode_text, load_mapping, save_mapping


def test_mapping_io_roundtrip(tmp_path: Path):
    map_path = tmp_path / "mapping.txt"
    # empty mapping
    fwd, rev = load_mapping(map_path)
    assert fwd == {} and rev == {}

    # simulate forward mapping and save
    forward = {"Alice": "AAAA0000", "Bob": "BBBB1111"}
    save_mapping(map_path, forward)

    fwd2, rev2 = load_mapping(map_path)
    assert fwd2["Alice"] == "AAAA0000"
    assert rev2["BBBB1111"] == "Bob"


def test_encode_then_decode_simple():
    src = "Hi [[Alice]] and Bob."
    forward = {}
    out, fwd2 = encode_text(src, forward)
    # Alice ersetzt, Bob ggf. als unmarkiert erst durch Schritt 3
    assert "Alice" not in out
    back = decode_text(out, {v: k for k, v in fwd2.items()})
    assert "Alice" in back
