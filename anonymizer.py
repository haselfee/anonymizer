#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
anonymizer.py — CLI tool to anonymize/de-anonymize marked tokens in a text file.

Usage:
  python anonymizer.py encode
  python anonymizer.py decode

Files (same directory as this script):
  - anonymizer-input.txt     # input AND output text file
  - anonymizer-mapping.txt   # mapping file: "<HASH> = <ORIGINAL>"

Rules:
  - Encode:
      * Detect tokens like [[word]].
      * Create/reuse a hash per distinct marked word.
      * Replace ALL occurrences of each marked word across the whole text
        (marked and unmarked) with the same hash.
      * Finally, strip any remaining [[word]] to plain "word".
  - Decode:
      * Replace tokens that look like a hash (exact hash length) back to original
        using the mapping; unmatched tokens remain unchanged.
"""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple
import secrets
import string

# -----------------------------
# Configuration (adjust here)
# -----------------------------
HASH_LENGTH = 10  # Default hash length; adjust if needed
INPUT_FILENAME = "anonymizer-input.txt"
MAPPING_FILENAME = "anonymizer-mapping.txt"

# Allowed alphabet for hashes (alphanumeric). Keep in sync with decode regex.
HASH_ALPHABET = string.ascii_letters + string.digits

# Regex to find [[token or phrase]] during encode
# Captures anything inside [[...]] except nested brackets
ENCODE_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")

def script_dir() -> Path:
    """Return the directory where this script resides."""
    return Path(__file__).resolve().parent

def file_paths() -> Tuple[Path, Path]:
    """Return absolute paths for input and mapping files."""
    base = script_dir()
    return base / INPUT_FILENAME, base / MAPPING_FILENAME

def load_mapping(mapping_path: Path) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Load mapping file.

    Returns:
      - hash_to_orig: {hash -> original}
      - orig_to_hash: {original -> hash} (built for quick lookup)
    Ignores malformed lines gracefully.
    """
    hash_to_orig: Dict[str, str] = {}
    if mapping_path.exists():
        with mapping_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                # Expected format: <HASH> = <Original>
                left, right = line.split("=", 1)
                h = left.strip()
                orig = right.strip()
                if h and orig:
                    hash_to_orig[h] = orig

    # Build reverse mapping (last one wins if duplicates exist)
    orig_to_hash = {orig: h for h, orig in hash_to_orig.items()}
    return hash_to_orig, orig_to_hash

def generate_hash(existing: Dict[str, str]) -> str:
    """Generate a unique random hash not present in 'existing' mapping keys."""
    while True:
        candidate = "".join(secrets.choice(HASH_ALPHABET) for _ in range(HASH_LENGTH))
        if candidate not in existing:
            return candidate

def read_text(input_path: Path) -> str:
    if not input_path.exists():
        # Create empty file if missing to keep behavior predictable
        input_path.write_text("", encoding="utf-8")
        return ""
    return input_path.read_text(encoding="utf-8")

def write_text(input_path: Path, text: str) -> None:
    input_path.write_text(text, encoding="utf-8")

def append_mappings(mapping_path: Path, new_pairs: Dict[str, str]) -> None:
    """Append new mappings (<HASH> = <Original>) to the mapping file."""
    if not new_pairs:
        return
    with mapping_path.open("a", encoding="utf-8") as f:
        for h, orig in new_pairs.items():
            f.write(f"{h} = {orig}\n")

def encode() -> None:
    input_path, mapping_path = file_paths()
    text = read_text(input_path)

    hash_to_orig, orig_to_hash = load_mapping(mapping_path)
    newly_created: Dict[str, str] = {}

    # Collect all unique tokens that were marked [[...]] in the ORIGINAL text
    marked = set(ENCODE_PATTERN.findall(text))

    # Prepare/extend mapping for each marked token
    for original in marked:
        if original not in orig_to_hash:
            new_hash = generate_hash(hash_to_orig)
            hash_to_orig[new_hash] = original
            orig_to_hash[original] = new_hash
            newly_created[new_hash] = original

    # Replace ALL occurrences (full-word matches) of each marked word with its hash
    new_text = text
    for original in marked:
        h = orig_to_hash[original]
        # \b ensures only full words are replaced; respects Unicode word chars
        pattern = re.compile(rf"\b{re.escape(original)}\b")
        new_text = pattern.sub(h, new_text)

    # Final cleanup: strip any remaining [[word]] to "word"
    # (in case some brackets remained for words we chose not to anonymize)
    new_text = ENCODE_PATTERN.sub(lambda m: m.group(1), new_text)

    # Persist results
    write_text(input_path, new_text)
    append_mappings(mapping_path, newly_created)

    print(f"Encoded. Processed {len(marked)} token type(s).")

def decode() -> None:
    input_path, mapping_path = file_paths()
    text = read_text(input_path)

    hash_to_orig, _ = load_mapping(mapping_path)
    if not hash_to_orig:
        print("No mappings found. Nothing to decode.")
        return

    # Match any token that *could* be a hash: exact length alphanumerics with word boundaries
    hash_regex = re.compile(rf"\b([A-Za-z0-9]{{{HASH_LENGTH}}})\b")

    replacements = 0

    def replace(match: re.Match) -> str:
        nonlocal replacements
        token = match.group(1)
        original = hash_to_orig.get(token)
        if original is not None:
            replacements += 1
            return original
        return token  # leave untouched if not in mapping

    new_text = hash_regex.sub(replace, text)
    write_text(input_path, new_text)
    print(f"Decoded. Restored {replacements} token(s).")

def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Anonymize [[tokens]] in anonymizer-input.txt using anonymizer-mapping.txt."
    )
    parser.add_argument(
        "mode",
        choices=["encode", "decode"],
        help="encode: [[word]] & all occurrences -> <HASH>; decode: <HASH> -> original (if mapping exists)",
    )
    return parser.parse_args(argv)

def main() -> None:
    args = parse_args()
    _, mapping_path = file_paths()
    if not mapping_path.exists():
        mapping_path.touch()

    if args.mode == "encode":
        encode()
    else:
        decode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
