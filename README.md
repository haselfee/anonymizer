# Anonymizer


Kommandozeilen-Tool in Python zum Anonymisieren und Deanonymisieren von Namen, Phrasen oder Produkten in Textdateien.  
Gedacht, um sensible Inhalte vor der Weitergabe an externe KI-Dienste zu schützen.

---

## Funktionsweise

- **Markierung**: Alle Wörter oder Phrasen, die anonymisiert werden sollen, werden im Eingabetext mit `[[...]]` gekennzeichnet, z. B.  
  ```
  [[Alice]] arbeitet am Projekt [[Super Nova]].
  ```

- **Encoding** (`python anonymizer.py encode`):  
  - Erstellt für jedes markierte Wort/Phrase einen zufälligen Hash (Standard: 8 Zeichen alphanumerisch).  
  - Ersetzt **alle Vorkommen** dieses Wortes/Phrase im Text (auch unmarkierte) durch denselben Hash.  
  - Schreibt neue Mappings in `anonymizer-mapping.txt` im Format:  
    ```
    <HASH> = <ORIGINAL>
    ```
  - Entfernt nach der Anonymisierung die Klammern `[[...]]` (falls noch vorhanden).  
  - Überschreibt die Datei `anonymizer-input.txt` mit dem anonymisierten Text.

- **Decoding** (`python anonymizer.py decode`):  
  - Liest die Mapping-Datei.  
  - Sucht im Text nach Tokens, die exakt der Hash-Länge entsprechen.  
  - Ersetzt bekannte Hashes wieder durch die Originalwörter.  
  - Schreibt den decodierten Text zurück nach `anonymizer-input.txt`.

---

## Dateien

Alle Dateien liegen im selben Verzeichnis wie das Skript:

- `anonymizer.py` — Hauptskript  
- `anonymizer-input.txt` — Eingabe- und Ausgabedatei  
- `anonymizer-mapping.txt` — Mapping-Datei (`<HASH> = <Original>`)

---

## Installation

1. Python 3 installieren (ab Version 3.8).  
2. Dieses Repository/Script herunterladen.  
3. Abhängigkeiten: keine externen Libraries erforderlich (nur Standardbibliothek).

---

## Nutzung

```bash
# Encode: markierte Wörter/Phrasen anonymisieren
python anonymizer.py encode

# Decode: Hashes zurückwandeln
python anonymizer.py decode
```

---

## Beispiel

**anonymizer-input.txt (vorher):**
```
[[Alice]] arbeitet am Projekt [[Super Nova]].
Später erwähnt Alice noch einmal Super Nova.
```

**Befehl:**
```bash
python anonymizer.py encode
```

**anonymizer-input.txt (nachher):**
```
hQ9wLm3TxA arbeitet am Projekt Gt82Kd9LmP.
Später erwähnt hQ9wLm3TxA noch einmal Gt82Kd9LmP.
```

**anonymizer-mapping.txt:**
```
hQ9wLm3TxA = Alice
Gt82Kd9LmP = Super Nova
```

**Befehl:**
```bash
python anonymizer.py decode
```

**anonymizer-input.txt (decodiert):**
```
Alice arbeitet am Projekt Super Nova.
Später erwähnt Alice noch einmal Super Nova.
```

---

## Konfiguration

- **Hash-Länge**: Im Skript konfigurierbar (`HASH_LENGTH = 8`).  
- **Zeichensatz**: Alphanumerisch (`A–Za–z0–9`).  
- **Mapping-Datei**: bleibt dauerhaft bestehen und wächst bei jedem neuen Token.  

---

## Hinweise

- Nur Wörter/Phrasen, die einmal in `[[...]]` markiert wurden, werden auch in unmarkierter Form ersetzt.  
- Hashes werden zufällig erzeugt (mit `secrets` für kryptografische Sicherheit).  
- Die Mapping-Datei ist textbasiert und kann bei Bedarf manuell bearbeitet oder gelöscht werden.  
