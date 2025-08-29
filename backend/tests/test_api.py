import pytest


@pytest.mark.asyncio
async def test_healthcheck(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


@pytest.mark.asyncio
async def test_encode_and_decode_roundtrip(client):
    text_in = "[[Alice]] arbeitet am Projekt [[Super Nova]]."

    r = await client.post("/encode", json={"text": text_in})
    assert r.status_code == 200
    data = r.json()
    enc_text = data["text"]
    mapping = data["mapping"]

    assert "[[" not in enc_text and "]]" not in enc_text
    assert "Alice" not in enc_text and "Super Nova" not in enc_text
    assert any(len(tok) == 8 for tok in mapping.values())

    r2 = await client.post("/decode", json={"text": enc_text, "mapping": mapping})
    assert r2.status_code == 200
    assert r2.json()["text"] == "Alice arbeitet am Projekt Super Nova."


@pytest.mark.asyncio
async def test_encode_with_existing_mapping(client):
    text_in = "Alice und Super Nova treffen sich."
    # ORIGINAL -> TOKEN (API-Konvention)
    mapping = {"Alice": "A1b2C3d4", "Super Nova": "Z9y8X7w6"}

    r = await client.post("/encode", json={"text": text_in, "mapping": mapping})
    assert r.status_code == 200
    enc = r.json()["text"]
    # beide Begriffe sollten ersetzt sein
    assert "Alice" not in enc and "Super Nova" not in enc
