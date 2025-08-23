# anonymizer.py
from __future__ import annotations
import sys, re, secrets, string
from pathlib import Path

# --- Public API expected by tests ---
HASH_LENGTH = 8  # tests import this

# --- Files (müssen zu den Tests passen) ---
INPUT_FILE = "anonymizer-input.txt"
MAP_FILE   = "anonymizer-mapping.txt"   # Format: <TOKEN> = <ORIGINAL>

# --- Token-Generator: 8 Zeichen [A-Za-z0-9] ---
_ALNUM = string.ascii_letters + string.digits
def _random_token(length: int = HASH_LENGTH) -> str:
    return "".join(secrets.choice(_ALNUM) for _ in range(length))

def anonymize(_: str) -> str:
    """Return a random 8-char alphanumeric token. Non-deterministic by design."""
    return _random_token(HASH_LENGTH)

# --- Mapping IO: Datei speichert "TOKEN = ORIGINAL" ---
def load_mapping(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """
    Returns:
      forward: ORIGINAL -> TOKEN
      reverse: TOKEN -> ORIGINAL
    """
    forward: dict[str, str] = {}
    reverse: dict[str, str] = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                token, original = map(str.strip, line.split("=", 1))
                if token and original:
                    reverse[token] = original
                    forward[original] = token
    return forward, reverse

def save_mapping(path: Path, forward: dict[str, str]) -> None:
    # Schreibe konsistent als "TOKEN = ORIGINAL", sortiert nach ORIGINAL für Stabilität
    items = sorted(((tok, orig) for orig, tok in forward.items()), key=lambda x: x[1].lower())
    with path.open("w", encoding="utf-8") as f:
        for tok, orig in items:
            f.write(f"{tok} = {orig}\n")

# --- Regex-Helfer ---
_MARKED = re.compile(r"\[\[(.+?)\]\]")  # [[...]] (auch Phrasen mit Leerzeichen)
def _word_boundary_pattern(term: str) -> re.Pattern:
    esc = re.escape(term)
    # \b nur, wenn term "wortartig" ist; sonst exakter Escape
    if re.fullmatch(r"[0-9A-Za-zÄÖÜäöüß_]+", term):
        return re.compile(rf"\b{esc}\b")
    return re.compile(esc)

# --- Encode / Decode auf INPUT_FILE in place ---
def encode_text(src: str, forward: dict[str, str]) -> tuple[str, dict[str, str]]:
    """
    forward: ORIGINAL -> TOKEN (wird ggf. ergänzt)
    """
    # 1) Markierte Begriffe sammeln, Tokens vergeben (neu oder aus Mapping)
    marked = _MARKED.findall(src)
    for term in marked:
        if term not in forward:
            forward[term] = anonymize(term)

    # 2) Markierte Stellen direkt ersetzen
    def _repl_marked(m: re.Match) -> str:
        term = m.group(1)
        tok = forward.setdefault(term, anonymize(term))
        return tok
    out = _MARKED.sub(_repl_marked, src)

    # 3) Unmarkierte Vorkommen bereits bekannter Begriffe ersetzen
    for term, tok in forward.items():
        pat = _word_boundary_pattern(term)
        out = pat.sub(tok, out)

    # 4) Restliche Klammern (falls übrig) strippen
    out = out.replace("[[", "").replace("]]", "")
    return out, forward

def decode_text(src: str, reverse: dict[str, str]) -> str:
    """
    reverse: TOKEN -> ORIGINAL
    """
    out = src
    for tok, term in reverse.items():
        pat = _word_boundary_pattern(tok)
        out = pat.sub(term, out)
    return out

# --- CLI ---
def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in {"encode", "decode"}:
        print("Usage: python anonymizer.py [encode|decode]")
        return 2

    mode = argv[1]
    cwd = Path.cwd()
    in_path  = cwd / INPUT_FILE
    map_path = cwd / MAP_FILE

    forward, reverse = load_mapping(map_path)

    if mode == "encode":
        if not in_path.exists():
            print(f"Input file not found: {INPUT_FILE}", file=sys.stderr)
            return 1
        src = in_path.read_text(encoding="utf-8")
        out, forward2 = encode_text(src, forward)
        in_path.write_text(out, encoding="utf-8")   # IN PLACE schreiben (Test erwartet das)
        save_mapping(map_path, forward2)
        return 0

    if mode == "decode":
        if not in_path.exists():
            print(f"Input file not found: {INPUT_FILE}", file=sys.stderr)
            return 1
        src = in_path.read_text(encoding="utf-8")
        out = decode_text(src, reverse)
        in_path.write_text(out, encoding="utf-8")   # IN PLACE zurückschreiben
        # Mapping bleibt unverändert
        return 0

    return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
