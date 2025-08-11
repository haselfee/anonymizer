import base64
import hashlib
import itertools
import re
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------
# Config
# ----------------------------
DEFAULT_BASE_KEY = "c4nice"  # <- set your default key here
TOKEN_PREFIX = "ENC"                  # marker used in anonymized tokens

# Patterns:
#   [[Some Name]]           -> will be anonymized
#   [[ENC#12:abcd...]]      -> will be de-anonymized
PAT_BRACKETED = re.compile(r"\[\[(.+?)\]\]", re.DOTALL)
PAT_ENC_TOKEN = re.compile(rf"\[\[(?:{TOKEN_PREFIX}|{TOKEN_PREFIX.lower()})#(\d+):([A-Za-z0-9_-]+)\]\]")

# ----------------------------
# Core logic
# ----------------------------

def kdf_stream(base_key: str, index: int, nbytes: int) -> bytes:
    """
    Derive a pseudo keystream of length nbytes from base_key and index using SHA-256 blocks.
    Not cryptographically strong; sufficient for lightweight obfuscation.
    """
    out = bytearray()
    counter = 0
    # seed = base_key || ":" || index
    seed = f"{base_key}:{index}".encode("utf-8")
    while len(out) < nbytes:
        h = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        out.extend(h)
        counter += 1
    return bytes(out[:nbytes])

def xor_bytes(data: bytes, keystream: bytes) -> bytes:
    return bytes((db ^ kb) for db, kb in zip(data, keystream))

def b64_urlsafe_encode(b: bytes) -> str:
    s = base64.urlsafe_b64encode(b).decode("ascii")
    return s.rstrip("=")  # shorter, token-friendly

def b64_urlsafe_decode(s: str) -> bytes:
    # restore padding
    pad = (-len(s)) % 4
    s_padded = s + ("=" * pad)
    return base64.urlsafe_b64decode(s_padded.encode("ascii"))

def encrypt_fragment(plain: str, base_key: str, index: int) -> str:
    data = plain.encode("utf-8")
    ks = kdf_stream(base_key, index, len(data))
    obf = xor_bytes(data, ks)
    return b64_urlsafe_encode(obf)

def decrypt_fragment(token_b64: str, base_key: str, index: int) -> str:
    obf = b64_urlsafe_decode(token_b64)
    ks = kdf_stream(base_key, index, len(obf))
    data = xor_bytes(obf, ks)
    return data.decode("utf-8", errors="strict")

def anonymize_text(src: str, base_key: str) -> str:
    """
    Replace any [[...]] that is NOT already an ENC token with [[ENC#i:payload]]
    where i is the 1-based occurrence index among all [[...]] blocks in the text.
    """
    occurrences = list(PAT_BRACKETED.finditer(src))
    if not occurrences:
        return src

    result_parts = []
    last_end = 0
    enc_index = 0

    for m in occurrences:
        inner = m.group(1)
        # If it's already an ENC token, keep as-is
        if PAT_ENC_TOKEN.fullmatch(m.group(0)):
            continue

        enc_index += 1
        # write text up to this match
        result_parts.append(src[last_end:m.start()])

        payload = encrypt_fragment(inner, base_key, enc_index)
        token = f"[[{TOKEN_PREFIX}#{enc_index}:{payload}]]"
        result_parts.append(token)
        last_end = m.end()

    result_parts.append(src[last_end:])
    return "".join(result_parts)

def deanonymize_text(src: str, base_key: str) -> str:
    """
    Replace [[ENC#i:payload]] blocks back to their plaintext using the same key and index.
    """
    def repl(m: re.Match) -> str:
        idx = int(m.group(1))
        payload = m.group(2)
        try:
            plain = decrypt_fragment(payload, base_key, idx)
        except Exception:
            # If anything fails, keep the token unchanged to avoid data loss
            return m.group(0)
        return f"[[{plain}]]"

    return PAT_ENC_TOKEN.sub(repl, src)

# ----------------------------
# GUI
# ----------------------------

class AnonymizerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Text-Anonymisierung (reversibel)")

        # Key row
        key_frame = ttk.Frame(root)
        key_frame.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(key_frame, text="Basisschlüssel:").pack(side="left")
        self.key_var = tk.StringVar(value=DEFAULT_BASE_KEY)
        self.key_entry = ttk.Entry(key_frame, textvariable=self.key_var, show="•")
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(8, 8))
        self.show_key = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            key_frame, text="Key anzeigen",
            variable=self.show_key,
            command=self.toggle_key_visibility
        ).pack(side="left")

        # Paned window for text areas
        paned = ttk.Panedwindow(root, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=6)

        # Left frame (input)
        left = ttk.Frame(paned)
        self.txt_in = tk.Text(left, wrap="word", undo=True, height=24)
        self.txt_in.pack(fill="both", expand=True)
        ttk.Label(left, text="Eingabe (Original ODER anonymisiert)").pack(anchor="w", pady=(4, 0))
        paned.add(left, weight=1)

        # Right frame (output)
        right = ttk.Frame(paned)
        self.txt_out = tk.Text(right, wrap="word", undo=True, height=24, state="normal")
        self.txt_out.pack(fill="both", expand=True)
        ttk.Label(right, text="Ausgabe").pack(anchor="w", pady=(4, 0))
        paned.add(right, weight=1)

        # Buttons
        btn_row = ttk.Frame(root)
        btn_row.pack(fill="x", padx=10, pady=(6, 10))

        self.btn_anon = ttk.Button(btn_row, text="Anonymisieren →", command=self.on_anonymize)
        self.btn_anon.pack(side="left")

        self.btn_deanon = ttk.Button(btn_row, text="← De‑Anonymisieren", command=self.on_deanonymize)
        self.btn_deanon.pack(side="left", padx=(8, 0))

        ttk.Button(btn_row, text="Ausgabe kopieren", command=self.copy_output).pack(side="right")
        ttk.Button(btn_row, text="Ausgabe leeren", command=self.clear_output).pack(side="right", padx=(8, 8))

        # Status bar
        self.status_var = tk.StringVar(value="Bereit.")
        status = ttk.Label(root, textvariable=self.status_var, anchor="w", relief="sunken")
        status.pack(fill="x", padx=0, pady=0, ipady=2)

    def toggle_key_visibility(self):
        self.key_entry.configure(show="" if self.show_key.get() else "•")

    def get_key(self) -> str:
        key = self.key_var.get()
        if not key:
            raise ValueError("Basisschlüssel darf nicht leer sein.")
        return key

    def on_anonymize(self):
        try:
            key = self.get_key()
            src = self.txt_in.get("1.0", "end-1c")
            if not src.strip():
                self.set_status("Keine Eingabe gefunden.")
                return
            out = anonymize_text(src, key)
            self.set_output(out)
            self.set_status("Anonymisierung abgeschlossen.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            self.set_status("Fehler bei der Anonymisierung.")

    def on_deanonymize(self):
        try:
            key = self.get_key()
            src = self.txt_in.get("1.0", "end-1c")
            if not src.strip():
                self.set_status("Keine Eingabe gefunden.")
                return
            out = deanonymize_text(src, key)
            self.set_output(out)
            self.set_status("De‑Anonymisierung abgeschlossen.")
        except Exception as e:
            messagebox.showerror("Fehler", str(e))
            self.set_status("Fehler bei der De‑Anonymisierung.")

    def set_output(self, text: str):
        self.txt_out.config(state="normal")
        self.txt_out.delete("1.0", "end")
        self.txt_out.insert("1.0", text)
        self.txt_out.config(state="normal")

    def clear_output(self):
        self.txt_out.config(state="normal")
        self.txt_out.delete("1.0", "end")
        self.txt_out.config(state="normal")
        self.set_status("Ausgabe geleert.")

    def copy_output(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.txt_out.get("1.0", "end-1c"))
        self.set_status("Ausgabe in die Zwischenablage kopiert.")

    def set_status(self, msg: str):
        self.status_var.set(msg)


def main():
    root = tk.Tk()
    # Optional: nicer default padding/theme
    try:
        root.tk.call("tk", "scaling", 1.2)
    except Exception:
        pass
    AnonymizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
