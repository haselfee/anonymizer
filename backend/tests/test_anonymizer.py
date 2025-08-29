import re
import sys
import pytest
import subprocess
import importlib.util
from pathlib import Path

SCRIPT_NAME = "anonymizer.py"
INPUT_FILE = "input.txt"
MAP_FILE = "mapping.txt"


# load HASH_LENGTH from anonymizer.py
REPO_ROOT = Path(__file__).resolve().parents[2]  # geht 2 Ebenen hoch: repo-root
spec = importlib.util.spec_from_file_location(
    "anonymizer", REPO_ROOT / "backend" / "anonymizer.py"
)

anonymizer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anonymizer)

HASH_LENGTH = anonymizer.HASH_LENGTH


def hash_pattern():
    return re.compile(rf"\b[A-Za-z0-9]{{{HASH_LENGTH}}}\b")


def run_cli(cwd: Path, mode: str):
    """Run the CLI as a subprocess in the given working dir."""
    result = subprocess.run(
        [sys.executable, SCRIPT_NAME, mode],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"STDERR:\n{result.stderr}\nSTDOUT:\n{result.stdout}"
    return result


def write(cwd: Path, filename: str, content: str):
    (cwd / filename).write_text(content, encoding="utf-8")


def read(cwd: Path, filename: str) -> str:
    return (cwd / filename).read_text(encoding="utf-8")

def copy_script(src_dir: Path, dst_dir: Path):
    """Copy backend/anonymizer.py into the tmp test dir."""
    src = src_dir / "backend" / SCRIPT_NAME
    dst = dst_dir / SCRIPT_NAME
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

def parse_mapping(text: str):
    pairs = []
    for line in text.splitlines():
        if "=" in line:
            h, orig = line.split("=", 1)
            pairs.append((h.strip(), orig.strip()))
    return pairs


def is_hash(token: str, length: int) -> bool:
    return (
        len(token) == length
        and token.isalnum()
        and any(ch.isdigit() for ch in token)  # ≥1 Ziffer
        and any(ch.isupper() for ch in token)  # ≥1 Großbuchstabe
        and any(ch.islower() for ch in token)  # ≥1 Kleinbuchstabe
    )


def test_encode_replaces_marked_and_unmarked_words_and_strips_brackets(tmp_path: Path):
    # Arrange
    copy_script(REPO_ROOT, tmp_path)
    write(
        tmp_path,
        INPUT_FILE,
        "[[Alice]] arbeitet am Projekt Super Nova. Alice mag Kaffee.",
    )
    write(tmp_path, MAP_FILE, "")  # empty mapping

    # Act
    run_cli(tmp_path, "encode")

    # Assert
    out = read(tmp_path, INPUT_FILE)
    # Both "Alice" (marked and unmarked) must be replaced by the same hash
    hp = hash_pattern()
    hashes = hp.findall(out)
    assert len(hashes) >= 1
    # the word "Alice" should not appear anymore; brackets must be gone
    assert "[[" not in out and "]]" not in out
    assert "Alice" not in out


def test_encode_handles_phrases_with_spaces(tmp_path: Path):
    copy_script(REPO_ROOT, tmp_path)
    write(
        tmp_path, INPUT_FILE, "Heute arbeitet [[Super Nova]] mit Super Nova zusammen."
    )
    write(tmp_path, MAP_FILE, "")

    run_cli(tmp_path, "encode")
    out = read(tmp_path, INPUT_FILE)
    mapping = read(tmp_path, MAP_FILE)
    pairs = parse_mapping(mapping)

    # genau 1 neues Mapping (für "Super Nova") erwartet
    assert len(pairs) == 1
    h, orig = pairs[0]
    assert orig == "Super Nova"

    # der Hash aus dem Mapping muss 2x im Text auftauchen (beide Vorkommen ersetzt)
    assert out.count(h) == 2

    # Originalphrase darf nicht mehr im Text stehen, Klammern weg
    assert "Super Nova" not in out
    assert "[[" not in out and "]]" not in out


@pytest.mark.quarantine
@pytest.mark.xfail(strict=False, reason="Heuristic; flaky by design")
def test_encode_handles_phrases_with_spaces_test_with_hash(tmp_path: Path):
    repo_root = Path.cwd()
    copy_script(repo_root, tmp_path)
    write(
        tmp_path, INPUT_FILE, "Heute arbeitet [[Super Nova]] mit Super Nova zusammen."
    )
    write(tmp_path, MAP_FILE, "")

    run_cli(tmp_path, "encode")
    out = read(tmp_path, INPUT_FILE)

    # All occurrences of the phrase must be the same hash
    hp = hash_pattern()
    tokens = hp.findall(out)
    hashes = [t for t in tokens if is_hash(t, HASH_LENGTH)]
    assert len(set(hashes)) == 1
    # Phrase should be fully replaced; no brackets left
    assert "Super Nova" not in out
    assert "[[" not in out and "]]" not in out


def test_encode_applies_existing_mapping_without_marks(tmp_path: Path):
    copy_script(REPO_ROOT, tmp_path)
    # Pre-populate mapping with a known pair
    write(tmp_path, MAP_FILE, "AaBb22Cc = Alice\n")
    write(
        tmp_path,
        INPUT_FILE,
        "Heute spricht Alice mit Bob. (Keine Markierungen im Text)",
    )

    run_cli(tmp_path, "encode")
    out = read(tmp_path, INPUT_FILE)

    # Should replace Alice using existing mapping even without [[...]]
    assert "Alice" not in out
    assert "AaBb22Cc" in out
    # Unrelated words stay
    assert "Bob" in out


def test_decode_restores_using_mapping_and_leaves_unknown_hashes(tmp_path: Path):
    copy_script(REPO_ROOT, tmp_path)
    # Suppose two hashes exist; one is known, one is unknown
    write(tmp_path, MAP_FILE, "HhhhhhhH = Alice\n")
    write(tmp_path, INPUT_FILE, "HhhhhhhH und Zzzzzzzz treffen sich.")

    run_cli(tmp_path, "decode")
    out = read(tmp_path, INPUT_FILE)

    # Known mapping restored
    assert "Alice" in out
    # Unknown hash remains as-is (still looks like a hash)
    assert re.search(hash_pattern(), out), "Unknown hash should remain"


def test_word_boundaries_do_not_replace_substrings(tmp_path: Path):
    copy_script(REPO_ROOT, tmp_path)
    write(tmp_path, MAP_FILE, "")
    write(
        tmp_path,
        INPUT_FILE,
        "[[Al]] sitzt neben Al und im Wort 'Balkan' darf Al NICHT ersetzt werden.",
    )

    run_cli(tmp_path, "encode")
    out = read(tmp_path, INPUT_FILE)

    # 'Al' as a full word should be replaced, but 'Balkan' must stay unchanged
    assert "Balkan" in out
    # ' Al ' should now include a hash; but 'Balkan' still has 'Al' as substring
    assert " Al " not in out  # replaced by hash -> no literal " Al "
    # No brackets left
    assert "[[" not in out and "]]" not in out


def test_multiple_marked_tokens_get_distinct_hashes(tmp_path: Path):
    copy_script(REPO_ROOT, tmp_path)
    write(tmp_path, MAP_FILE, "")
    write(
        tmp_path,
        INPUT_FILE,
        "[[Alice]] trifft [[Bob]]. Alice und Bob arbeiten bei [[Super Nova]].",
    )

    run_cli(tmp_path, "encode")
    out = read(tmp_path, INPUT_FILE)

    hp = hash_pattern()
    hashes = hp.findall(out)
    # We expect at least 3 distinct hashes: Alice, Bob, Super Nova
    assert len(set(hashes)) >= 3
    # No originals left
    for original in ["Alice", "Bob", "Super Nova"]:
        assert original not in out
