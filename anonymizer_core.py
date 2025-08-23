#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pure core logic for anonymizer: no file I/O, reusable from CLI and HTTP API.
"""

from __future__ import annotations
import re
import secrets 
import string
from typing import Dict, Tuple

# Default configuration; callers may override hash_length
DEFAULT_HASH_LENGTH = 8
HASH_ALPHABET = string.ascii_letters + string.digits

# Accepts words/phrases (no nested [[..]]); allows spaces inside
ENCODE_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")

def anonymize(text: str, length: int = DEFAULT_HASH_LENGTH) -> str:
    """
    Erzeugt eine zufällige ID mit fester Länge (length Zeichen).
    Hex-Variante: garantiert exakte Länge und ist URL-/Datei-kompatibel.
    """
    # token_hex erzeugt 2 Hex-Zeichen pro Byte → Länge/2 Bytes nötig
    return secrets.token_hex(length // 2) if length % 2 == 0 else \
           secrets.token_hex(length // 2 + 1)[:length]


def generate_hash(existing_hashes: Dict[str, str], hash_length: int) -> str:
    """Generate a unique random hash not present in existing_hashes."""
    while True:
        candidate = "".join(secrets.choice(HASH_ALPHABET) for _ in range(hash_length))
        if candidate not in existing_hashes:
            return candidate

def build_mappings_from_lines(lines: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Parse mapping file content (text) into two dicts:
      - hash_to_orig: {hash -> original}
      - orig_to_hash: {original -> hash}
    Malformed lines are ignored.
    """
    hash_to_orig: Dict[str, str] = {}
    for line in lines.splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        left, right = line.split("=", 1)
        h = left.strip()
        orig = right.strip()
        if h and orig:
            hash_to_orig[h] = orig
    orig_to_hash = {orig: h for h, orig in hash_to_orig.items()}
    return hash_to_orig, orig_to_hash

def serialize_new_mappings(new_pairs: Dict[str, str]) -> str:
    """Serialize new mappings to append, format: '<HASH> = <Original>\\n'."""
    if not new_pairs:
        return ""
    return "".join(f"{h} = {orig}\n" for h, orig in new_pairs.items())

def _word_boundary_pattern(original: str) -> re.Pattern:
    """
    Compile a regex that matches the original as a full token/phrase:
    - Use \b on both ends: works for phrases with spaces; ensures 'whole token' match.
    - Escape original literally.
    """
    return re.compile(rf"\b{re.escape(original)}\b")

def encode_text(
    text: str,
    hash_to_orig: Dict[str, str],
    orig_to_hash: Dict[str, str],
    *,
    hash_length: int = DEFAULT_HASH_LENGTH,
) -> Tuple[str, Dict[str, str], Dict[str, str]]:
    """
    Encode behavior (updated to your latest spec):
      1) Detect marked tokens [[...]] in the input text.
      2) Ensure each marked token is present in mapping (create new hash if needed).
      3) Replace ALL occurrences (marked or not) of EVERY KNOWN original (from mapping)
         across the whole text with its hash (order: longest originals first).
      4) Strip any remaining brackets [[...]] -> plain word/phrase.

    Returns:
      new_text, hash_to_orig_updated, newly_created_pairs (hash -> original)
    """
    # Step 1: extract marked tokens
    marked = set(ENCODE_PATTERN.findall(text))

    newly_created: Dict[str, str] = {}

    # Step 2: ensure mapping entries for new marked tokens
    for original in marked:
        if original not in orig_to_hash:
            new_hash = generate_hash(hash_to_orig, hash_length)
            hash_to_orig[new_hash] = original
            orig_to_hash[original] = new_hash
            newly_created[new_hash] = original

    # Step 3: replace using full mapping (apply longest originals first to avoid partial overlaps)
    new_text = text
    for original in sorted(orig_to_hash.keys(), key=len, reverse=True):
        h = orig_to_hash[original]
        pat = _word_boundary_pattern(original)
        new_text = pat.sub(h, new_text)

    # Step 4: strip any remaining [[...]] -> inner text
    new_text = ENCODE_PATTERN.sub(lambda m: m.group(1), new_text)

    return new_text, hash_to_orig, newly_created

def decode_text(
    text: str,
    hash_to_orig: Dict[str, str],
    *,
    hash_length: int = DEFAULT_HASH_LENGTH,
) -> str:
    """
    Decode hashes back to originals for tokens that:
      - are exactly `hash_length` alphanumeric chars and
      - exist in the current mapping.
    """
    hash_regex = re.compile(rf"\b([A-Za-z0-9]{{{hash_length}}})\b")

    def repl(m: re.Match) -> str:
        token = m.group(1)
        return hash_to_orig.get(token, token)

    return hash_regex.sub(repl, text)
