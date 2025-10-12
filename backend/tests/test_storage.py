from __future__ import annotations

from pathlib import Path


import storage


def test_file_store_roundtrip(tmp_path: Path) -> None:
    txt = tmp_path / "mapping.txt"
    store = storage.FileMappingStore(txt)

    forward_in = {"Alice": "AAAA1111", "Müller AG": "BBBB2222"}
    store.save(forward_in)

    forward_out, reverse_out = store.load()
    assert forward_out == forward_in
    assert reverse_out == {v: k for k, v in forward_in.items()}

    # Ensure deterministic file format and sorting by ORIGINAL (case-insensitive)
    lines = txt.read_text(encoding="utf-8").splitlines()
    assert lines == ["AAAA1111 = Alice", "BBBB2222 = Müller AG"]


def test_sqlite_store_roundtrip(tmp_path: Path) -> None:
    db = tmp_path / "mapping.db"
    store = storage.SqliteMappingStore(db)

    forward_in = {"Alpha": "AXXX0001", "Beta": "BYYY0002"}
    store.save(forward_in)

    forward_out, reverse_out = store.load()
    assert forward_out == forward_in
    assert reverse_out == {v: k for k, v in forward_in.items()}

    # Update/Upsert should replace existing token for same original
    forward_update = {"Alpha": "A-NEW-9999"}
    store.save(forward_update)
    forward_out2, _ = store.load()
    assert forward_out2["Alpha"] == "A-NEW-9999"


def test_sqlite_migration_from_mapping_txt(tmp_path: Path) -> None:
    # Prepare legacy mapping.txt
    txt = tmp_path / "mapping.txt"
    txt.write_text("T1 = Alice\nT2 = Müller AG\n", encoding="utf-8")

    db = tmp_path / "mapping.db"
    store = storage.SqliteMappingStore(db)

    # DB is empty -> migrate
    imported = store.migrate_from_file(txt)
    assert imported == 2

    forward, reverse = store.load()
    assert forward == {"Alice": "T1", "Müller AG": "T2"}
    assert reverse == {"T1": "Alice", "T2": "Müller AG"}

    # Second run should NOT import again
    imported_again = store.migrate_from_file(txt)
    assert imported_again == 0
