import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def test_encode_decode_endpoints(tmp_path: Path, monkeypatch):
    # Arbeite in temporärem Verzeichnis, damit api_server seine mapping.txt hier anlegt
    monkeypatch.chdir(tmp_path)

    # Import erst NACH chdir, damit MAP_PATH relativ hier landet
    api_server = importlib.import_module("api_server")
    client = TestClient(api_server.app)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True

    payload = {"text": "Hallo [[Alice]] und Bob."}
    r2 = client.post("/encode", json=payload)
    assert r2.status_code == 200
    data = r2.json()
    assert "text" in data and "mapping" in data
    assert "Alice" not in data["text"]  # sollte anonymisiert sein

    r3 = client.post("/decode", json={"text": data["text"]})
    assert r3.status_code == 200
    assert "Alice" in r3.json()["text"]
