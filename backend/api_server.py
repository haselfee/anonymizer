# api_server.py
from __future__ import annotations

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import anonymizer  # package-relative import aus backend.anonymizer

# NEW: lightweight environment logging (no behavior change)
import logging
from detect_env import running_in_container, running_under_uvicorn

app = FastAPI(title="Anonymizer API")
logger = logging.getLogger("anonymizer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Wir definieren die API-Richtung klar: mapping == ORIGINAL -> TOKEN
class TextIn(BaseModel):
    text: str
    mapping: dict[str, str] | None = None  # ORIGINAL -> TOKEN (optional)


class TextOut(BaseModel):
    text: str
    mapping: dict[str, str]  # ORIGINAL -> TOKEN


MAP_PATH = Path("mapping.txt")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


# Log detection at startup – mapping remains file-based
@app.on_event("startup")
def _log_environment() -> None:
    try:
        mode = "container" if running_in_container() else "host"
        server = "uvicorn" if running_under_uvicorn() else "other"
        logger.info(f"[env] mode={mode} server={server} mapping=file:{MAP_PATH}")
    except Exception as exc:
        logger.warning(f"[env] detection failed: {exc!r}")


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
    forward, reverse = anonymizer.load_mapping(
        MAP_PATH
    )  # ORIGINAL->TOKEN, TOKEN->ORIGINAL
    # optionales Mapping des Clients mergen (ORIGINAL->TOKEN)
    if req.mapping:
        for orig, tok in req.mapping.items():
            forward.setdefault(orig, tok)
            reverse.setdefault(tok, orig)

    out_text = anonymizer.decode_text(req.text, reverse)
    # Rückgabe wieder konsistent als ORIGINAL->TOKEN
    return TextOut(text=out_text, mapping=forward)
