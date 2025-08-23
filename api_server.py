# api_server.py
from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
import anonymizer  # nutzt deine encode_text/decode_text + Mapping-IO

app = FastAPI(title="Anonymizer API")

# Wir definieren die API-Richtung klar: mapping == ORIGINAL -> TOKEN
class TextIn(BaseModel):
    text: str
    mapping: Optional[Dict[str, str]] = None  # ORIGINAL -> TOKEN (optional)

class TextOut(BaseModel):
    text: str
    mapping: Dict[str, str]  # ORIGINAL -> TOKEN

MAP_PATH = Path("anonymizer-mapping.txt")

@app.get("/health")
def health() -> dict:
    return {"ok": True}

@app.post("/encode", response_model=TextOut)
def encode(req: TextIn) -> TextOut:
    forward, _ = anonymizer.load_mapping(MAP_PATH)  # ORIGINAL->TOKEN, TOKEN->ORIGINAL
    # optionales Mapping des Clients übernehmen (ORIGINAL->TOKEN)
    if req.mapping:
        for orig, tok in req.mapping.items():
            forward.setdefault(orig, tok)

    out_text, forward2 = anonymizer.encode_text(req.text, forward)
    anonymizer.save_mapping(MAP_PATH, forward2)  # speichert als "TOKEN = ORIGINAL"
    return TextOut(text=out_text, mapping=forward2)

@app.post("/decode", response_model=TextOut)
def decode(req: TextIn) -> TextOut:
    forward, reverse = anonymizer.load_mapping(MAP_PATH)  # ORIGINAL->TOKEN, TOKEN->ORIGINAL
    # optionales Mapping des Clients mergen (ORIGINAL->TOKEN)
    if req.mapping:
        for orig, tok in req.mapping.items():
            forward.setdefault(orig, tok)
            reverse.setdefault(tok, orig)

    out_text = anonymizer.decode_text(req.text, reverse)
    # Rückgabe wieder konsistent als ORIGINAL->TOKEN
    return TextOut(text=out_text, mapping=forward)
