# tests/test_api_roundtrip.py
from __future__ import annotations
from pathlib import Path
from typing import Generator
import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient, None, None]:
    """
    Use a temp mapping file to avoid touching the developer's real mapping.txt.
    We monkeypatch api_server.MAP_PATH before creating the TestClient.
    """
    import api_server  # type: ignore

    # ZUERST reloaden, damit Modulkonstanten neu gesetzt werden …
    api_server = importlib.reload(api_server)  # type: ignore
    # … DANN MAP_PATH auf unseren Temp-Pfad patchen
    test_map = tmp_path / "mapping.txt"
    monkeypatch.setattr(api_server, "MAP_PATH", test_map, raising=True)
    with TestClient(api_server.app) as c:
        yield c


def _post_json(client: TestClient, path: str, payload: dict) -> dict:
    r = client.post(path, json=payload)
    assert (
        r.status_code == 200
    ), f"Unexpected {path} status={r.status_code} body={r.text}"
    return r.json()


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_roundtrip_simple(client: TestClient) -> None:
    # Encode then decode returns the original text
    original = "Hello [[Alice]] and [[Bob]]!"
    enc = _post_json(client, "/encode", {"text": original})
    assert "text" in enc and "mapping" in enc
    encoded_text = enc["text"]
    mapping = enc["mapping"]
    # Mapping must be ORIGINAL->TOKEN, tokens alnum and fixed length (8 by default)
    for orig, tok in mapping.items():
        assert isinstance(orig, str) and isinstance(tok, str)
        assert len(tok) == 8 and tok.isalnum()

    dec = _post_json(client, "/decode", {"text": encoded_text, "mapping": mapping})
    assert dec["text"] == original.replace("[[", "").replace("]]", "")


def test_phrases_umlauts_and_punctuation(client: TestClient) -> None:
    # Full-phrase replacement, umlauts, punctuation boundaries
    original = "Grüße an [[Müller AG]]; auch an [[Häßler]], bitte."
    enc = _post_json(client, "/encode", {"text": original})
    encoded_text = enc["text"]
    # Tokens should replace both marked and unmarked occurrences
    # Add an unmarked occurrence and re-encode to ensure global replacement
    followup = encoded_text + " Müller AG ist jetzt auch unmarkiert genannt."
    enc2 = _post_json(client, "/encode", {"text": followup, "mapping": enc["mapping"]})
    # Ensure the unmarked name is also tokenized (no literal 'Müller AG' left)
    assert "Müller AG" not in enc2["text"]
    # Decode back to expected plain text (without brackets)
    dec = _post_json(
        client, "/decode", {"text": enc2["text"], "mapping": enc2["mapping"]}
    )
    expected = (
        original.replace("[[", "").replace("]]", "")
        + " Müller AG ist jetzt auch unmarkiert genannt."
    )
    assert dec["text"] == expected


def test_duplicate_markers_and_empty_input(client: TestClient) -> None:
    original = "[[Eve]] meets [[Eve]] again.  "
    enc = _post_json(client, "/encode", {"text": original})
    # Only one token per ORIGINAL despite duplicates
    token_set = set(enc["mapping"].values())
    assert len(token_set) == 1
    # Empty input should be handled gracefully
    enc_empty = _post_json(client, "/encode", {"text": ""})
    assert enc_empty["text"] == ""
    dec_empty = _post_json(client, "/decode", {"text": ""})
    assert dec_empty["text"] == ""


def test_mapping_echo_is_consistent(client: TestClient) -> None:
    original = "Ping [[Alpha]] Pong [[Beta]]"
    enc = _post_json(client, "/encode", {"text": original})
    mapping = enc["mapping"]
    # Send mapping back; server should preserve (not overwrite) client-supplied tokens
    custom = {"Alpha": "AAAA1111", "Gamma": "GGGG2222"}
    enc2 = _post_json(client, "/encode", {"text": "Alpha + Gamma", "mapping": custom})
    # The endpoint contract in api_server.py merges client mapping via setdefault
    # so existing keys keep their tokens; new keys remain as provided.
    assert enc2["mapping"]["Gamma"] == "GGGG2222"
    assert enc2["mapping"]["Alpha"] in {"AAAA1111", mapping.get("Alpha")}
