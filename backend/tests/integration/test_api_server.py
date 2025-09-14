from pathlib import Path
from fastapi.testclient import TestClient
import importlib

def test_encode_decode_endpoints(tmp_path: Path, monkeypatch):
    # Work in a temp CWD so mapping.txt is isolated
    monkeypatch.chdir(tmp_path)

    api_server = importlib.import_module("api_server")
    client = TestClient(api_server.app)

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True

    r2 = client.post("/encode", json={"text": "Hallo [[Alice]] und Bob."})
    assert r2.status_code == 200
    data = r2.json()
    assert "Alice" not in data["text"]

    r3 = client.post("/decode", json={"text": data["text"]})
    assert r3.status_code == 200
    assert "Alice" in r3.json()["text"]
