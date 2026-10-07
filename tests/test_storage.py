import json

from frog import storage


def test_save_and_load(tmp_path):
    path = tmp_path / "sub" / "settings.json"
    storage.save({"ai_quips": False}, path)
    assert storage.load(path, tmp_path / "none.json") == {"ai_quips": False}


def test_missing_file_gives_empty_settings(tmp_path):
    assert storage.load(tmp_path / "missing.json", tmp_path / "none.json") == {}


def test_broken_file_gives_empty_settings(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    assert storage.load(path, tmp_path / "none.json") == {}


def test_update_keeps_other_values(tmp_path):
    path = tmp_path / "settings.json"
    storage.save({"sound": True}, path)
    storage.update(path, ai_quips=False)
    assert json.loads(path.read_text(encoding="utf-8")) == {"sound": True, "ai_quips": False}


def test_legacy_german_settings_are_migrated(tmp_path):
    legacy = tmp_path / "einstellungen.json"
    legacy.write_text(
        json.dumps(
            {
                "ki_sprueche": False,
                "charakter": "Ein Pirat",
                "ton": True,
                "streiche": {"symbole_verstecken": False, "unbekannt": True},
            }
        ),
        encoding="utf-8",
    )
    assert storage.load(tmp_path / "settings.json", legacy) == {
        "ai_quips": False,
        "personality": "Ein Pirat",
        "sound": True,
        "pranks": {"hide_icons": False},
    }
