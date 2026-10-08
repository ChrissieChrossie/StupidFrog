# Stupid Frog 🐸

A cheeky pixel frog that hops across your Windows desktop.
He plays pranks and makes sarcastic comments.

> The frog speaks **German**. Menu entries and folder names he creates are German too.

## Getting started

**Quick:** double-click `start.bat`.

**Recommended:** set it up once, in PowerShell inside the `StupidFrog` folder:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -e ".[dev]"
```

Then start him with `start.bat`.
If `py` is not found, Python is missing: `winget install Python.Python.3.12`,
then reopen PowerShell.

## Single .exe (no installation)

`StupidFrog.exe` is one file with Python and everything else inside.
Copy it anywhere and double-click it. Nothing needs to be installed.

**Get it from GitHub:** every push to `main` builds it automatically.
Open the repository on GitHub, then "Actions" → "Build exe" → latest run → "Artifacts".
For a proper download page, push a tag such as `0.3.0`; the .exe is then attached to that release.

**Build it yourself:** double-click `build.bat`. The result is `dist\StupidFrog.exe`.

Notes:
- The .exe has no console window. Its log is written to `~/.frog/frog.log`.
- Windows SmartScreen may warn about an unknown app the first time: "More info" → "Run anyway".
- AI quips still need the `ANTHROPIC_API_KEY` environment variable (see below).

## Controls

| You do | What happens |
|---|---|
| Left-click the frog | He says something |
| Drag the frog | You pick him up; let go and he falls down (and complains) |
| Right-click the frog | Menu: AI quips, croak sound, mouse chasing, reminders, pranks, personality, quit |

He walks along the bottom of **all your monitors** and hops from one to the next.

## Mouse and reminders

- **Maus jagen** (chase the mouse): when your mouse pointer comes close, he snaps at it
  with his tongue or hops away in a huff.
- **Erinnerungen** (reminders): once an hour he reminds you to drink something,
  stretch or rest your eyes.

Both can be switched on and off in the right-click menu.

## Pranks

Now and then the frog messes with your desktop:

| Prank (menu entry) | What happens | How to undo |
|---|---|---|
| Minimierte Fenster öffnen | Brings a minimized window back to the front | Minimize it again |
| Fenster-Knöpfe mit der Zunge drücken | Licks the minimize or maximize button of a window | Restore or resize the window |
| Desktop-Symbole verstecken | Hides all desktop icons | They come back after 5 seconds |
| Desktop-Symbole verschieben | Shows the desktop, flicks an icon somewhere else with his tongue, then reopens your windows | Drag the icon back yourself |
| Dinge in Ordner packen | Tidies files into a "Froschkiste" (frog box) folder | He tips the box out again later |
| Ab und zu Pause machen | Hops off the screen and takes a break | He comes back after 45 to 90 seconds |

He comments on every prank.

**Turning pranks on and off:** right-click the frog, then "Streiche".
Every prank has its own checkbox. The frog remembers your choice.

**Safety:**
- He only touches files inside the `Frosch-Spielwiese` folder in your user folder.
- If that folder is empty, he puts a few fun files in it.
- He never deletes or overwrites anything.
- When you quit, hidden icons and minimized windows come back immediately.

## Quips from Claude (AI)

The frog can fetch fresh quips from Claude.
Without an API key or internet connection he simply uses his built-in list.

**1. Get a key**
- Sign in at [console.anthropic.com](https://console.anthropic.com).
- Add some credit (a few euros last a long time).
- Create a new key under "API Keys" and copy it.

**2. Store the key** (once, in PowerShell):

```powershell
setx ANTHROPIC_API_KEY "your-key"
```

Then **close and reopen** PowerShell.
Never put the key into the code and never share it.

**3. Turn it on or off**
- Right-click the frog, then "Sprüche von Claude".
- The frog remembers your choice (in `~/.frog/settings.json`).

**4. Describe his personality**
- Right-click the frog, then "Charakter beschreiben ...".
- Write a few sentences, for example: "A tired grandpa frog who complains about everything."
- Click "Speichern" (save). He remembers it after a restart.
- Cheeky-but-friendly rules always apply, whatever the personality.

Cost: he fetches 5 quips at a time from a small model.
That costs less than one cent.

The AI needs the `pip install -e ".[dev]"` setup from above.

## Project layout

```
src/frog/
  __main__.py      Entry point
  app.py           Main loop
  config.py        All tunable values (speed, size, pauses, playground)
  model.py         The frog as plain data (position, direction, state)
  pixel_art.py     The frog's pixel art (sitting and jumping)
  quips.py         Built-in quips
  reactions.py     Reactions to the mouse, being picked up, and reminders
  screens.py       Where the frog may walk (all monitors)
  ai_quips.py      Quips from Claude, fetched in the background
  storage.py       Remembers settings such as AI on/off
  sound.py         The croak sound
  windows.py       Helpers for windows and desktop icons (Windows only)
  safety.py        Guard: file actions only inside the playground
  actions/         What the frog can do (pranks.py = pranks)
  ui/              Window and drawing (tkinter)
src/sounds/        The croak sound
tests/             Tests
```

## Customizing

- **Redesign the frog:** change the letters in `pixel_art.py`.
- **New quip:** add it to the list in `quips.py`.
- **Prank lines:** listed at the top of each class in `actions/pranks.py`.
- **Pause between actions:** `action_pause_min_s` and `action_pause_max_s` in `config.py`.
- **Sit still more often:** the `rest_...` values in `config.py`.
- **Croak length:** `sound_duration_ms` in `config.py`.
- **Break length:** `break_min_s` and `break_max_s` in `config.py`.
- **Different playground:** `playground` in `config.py`.
- **Reminder interval:** `reminder_interval_min` in `config.py`.
- **Mouse chasing:** `chase_radius` and `chase_cooldown_s` in `config.py`.
- **Reminder lines and mouse reactions:** listed in `reactions.py`.
- **New action:** subclass `Action` in `actions/` and register it in `actions/registry.py`.

Every file action must go through `safety.py`, so the frog can never touch your real files.

## Tests

```powershell
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check .
```

On GitHub the tests run automatically on every push (`.github/workflows/tests.yml`).

## License

MIT, see `LICENSE`.
