# tests/test_roundtrip.py
from pathlib import Path
from anonymizer import anonymize, deanonymize, save_mapping, load_mapping


def test_roundtrip():
    data_dir = Path(__file__).parent / "data"
    original = (data_dir / "input-example.txt").read_text(encoding="utf-8")

    anonymized, mapping = anonymize(original)
    # Sanity checks
    assert anonymized != original
    for needle in ["Julia", "Solaris", "Keller", "Tom"]:
        assert needle not in anonymized

    # persist & restore
    map_file = data_dir / "mapping.json"
    save_mapping(mapping, map_file.as_posix())

    restored = deanonymize(anonymized, load_mapping(map_file.as_posix()))
    assert restored == original
