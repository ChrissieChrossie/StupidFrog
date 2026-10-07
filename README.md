# Frosch 🐸

Ein frecher Frosch läuft über deinen Bildschirm.
Er macht Quatsch und sagt doofe Sachen.

## Starten

**Einfach:** Doppelklick auf `start.bat`.

**Richtig (empfohlen):** Einmal einrichten, in PowerShell im Ordner `StupidFrog`:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

Danach startest du ihn mit `start.bat`.
Wird `py` nicht gefunden, fehlt Python: `winget install Python.Python.3.12`,
dann PowerShell neu öffnen.

## Bedienen

| Was du machst       | Was passiert            |
|---------------------|-------------------------|
| Linksklick auf Frosch  | Er sagt einen Spruch |
| Rechtsklick auf Frosch | Menü: KI, Quak-Ton, Streiche, Charakter, Beenden |

## Streiche

Der Frosch kann ab und zu Quatsch auf deinem Desktop machen:

| Streich | Was passiert | Rückgängig |
|---|---|---|
| Minimierte Fenster öffnen | Er holt ein verstecktes Fenster nach vorne | Einfach wieder minimieren |
| Fenster-Knöpfe mit der Zunge drücken | Er leckt an Minimieren oder Maximieren | Fenster wieder öffnen oder verkleinern |
| Desktop-Symbole verstecken | Alle Symbole sind kurz weg | Nach 5 Sekunden sind sie wieder da |
| Desktop-Symbole verschieben | Er zeigt kurz den Desktop, schubst ein Symbol mit der Zunge woanders hin und öffnet dann die Fenster wieder | Symbol selbst zurückziehen |
| Dinge in Ordner packen | Er räumt Dateien in die "Froschkiste" | Er kippt sie später wieder aus |
| Ab und zu Pause machen | Er hüpft aus dem Bild und ist kurz weg | Er kommt nach 45 bis 90 Sekunden von selbst zurück |

Bei jedem Streich sagt er etwas dazu.

**An- und ausschalten:** Rechtsklick auf den Frosch, dann "Streiche".
Jeder Streich hat einen eigenen Haken. Der Frosch merkt sich deine Wahl.

**Sicherheit:**
- Dateien fasst er **nur** im Ordner `Frosch-Spielwiese` in deinem Benutzer-Ordner an.
- Ist der Ordner leer, legt er selbst ein paar Spaß-Dateien hinein.
- Er löscht und überschreibt nie etwas.
- Beim Beenden holt er versteckte Symbole sofort zurück.

## Sprüche von Claude (KI)

Der Frosch kann sich neue Sprüche von Claude holen.
Ohne Schlüssel oder ohne Internet nimmt er einfach seine feste Liste.

**1. Schlüssel holen**
- Auf [console.anthropic.com](https://console.anthropic.com) anmelden.
- Etwas Guthaben aufladen (ein paar Euro reichen sehr lange).
- Unter "API Keys" einen neuen Schlüssel erstellen und kopieren.

**2. Schlüssel speichern** (einmal, in PowerShell):

```powershell
setx ANTHROPIC_API_KEY "dein-schluessel"
```

Danach PowerShell **schließen und neu öffnen**.
Den Schlüssel nie in den Code schreiben und nie weitergeben.

**3. An- und ausschalten**
- Rechtsklick auf den Frosch, dann "Sprüche von Claude".
- Der Frosch merkt sich deine Wahl (in `~/.frog/settings.json`).

**4. Charakter beschreiben**
- Rechtsklick auf den Frosch, dann "Charakter beschreiben ...".
- Schreib ein paar Sätze, zum Beispiel: "Ein müder Opa-Frosch, der über alles jammert."
- Auf "Speichern" klicken. Er merkt sich das auch nach einem Neustart.
- Freche, aber nette Regeln gelten immer, egal welcher Charakter.

Kosten: Er holt immer 5 Sprüche auf einmal mit einem kleinen Modell.
Das kostet weniger als einen Cent.

Wichtig: Die KI braucht die Einrichtung mit `pip install -e ".[dev]"` von oben.

## Tests

```powershell
pytest
ruff check .
```

## Ordner

Code und Kommentare sind auf Englisch. Was der Frosch sagt, bleibt Deutsch.

```
src/frog/
  __main__.py      Startpunkt
  app.py           Die Spielschleife
  config.py        Alle Zahlen zum Drehen (Tempo, Größe, Pausen, Spielwiese)
  model.py         Der Frosch als Daten (Position, Richtung)
  pixel_art.py     Das Pixelbild vom Frosch (Sitzen und Springen)
  quips.py         Die festen Sprüche
  ai_quips.py      Sprüche von Claude, im Hintergrund
  storage.py       Merkt sich Schalter wie KI an/aus
  sound.py         Der Quak-Ton
  windows.py       Helfer für Fenster und Desktop-Symbole (nur Windows)
  safety.py        Schutz: Dateien nur in der Spielwiese
  actions/         Was der Frosch tun kann (pranks.py = Streiche)
  ui/              Fenster und Zeichnung (tkinter)
src/sounds/        Der Quak-Ton
tests/             Tests
```

## Erweitern

- **Frosch umgestalten:** In `pixel_art.py` die Buchstaben ändern.
- **Neuer Spruch:** In `quips.py` in die Liste schreiben.
- **Streich-Sprüche:** Stehen oben in jeder Klasse in `actions/pranks.py`.
- **Pausen zwischen Sprüchen:** In `config.py` die Werte `action_pause_min_s` und `action_pause_max_s`.
- **Öfter still sitzen:** In `config.py` die Werte `rest_...` ändern.
- **Länge vom Quak-Ton:** In `config.py` der Wert `sound_duration_ms`.
- **Länge der Pause:** In `config.py` die Werte `break_min_s` und `break_max_s`.
- **Andere Spielwiese:** In `config.py` der Wert `playground`.
- **Neue Aktion:** Klasse in `actions/` bauen, in `actions/registry.py` eintragen.

## Sicherheit

Der Frosch darf Dateien **nur** im Ordner `Frosch-Spielwiese`
in deinem Benutzer-Ordner anfassen. Nie deine echten Dateien.
Dafür gibt es `safety.py`. Jede Datei-Aktion muss das benutzen.

## Tests

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check .
```

Auf GitHub laufen die Tests bei jedem Push von selbst (`.github/workflows/tests.yml`).

## Lizenz

MIT, siehe `LICENSE`.
