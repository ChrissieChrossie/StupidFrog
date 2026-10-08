import pytest

from frog import api_key


@pytest.fixture
def stored(monkeypatch):
    """Record what would be written to the Windows registry."""
    writes = []
    monkeypatch.setattr(api_key, "_write_user_env", lambda value: writes.append(value) or True)
    monkeypatch.delenv(api_key.ENV_NAME, raising=False)
    return writes


def test_save_sets_key_for_running_frog_and_next_start(stored):
    assert api_key.save("sk-ant-abc123")
    assert api_key.current() == "sk-ant-abc123"
    assert stored == ["sk-ant-abc123"]


def test_remove_forgets_key(stored):
    api_key.save("sk-ant-abc123")
    assert api_key.remove()
    assert api_key.current() == ""
    assert stored[-1] is None


def test_looks_valid():
    assert api_key.looks_valid("sk-ant-api03-xyz")
    assert not api_key.looks_valid("hello")
    assert not api_key.looks_valid("sk-ant-with space")
    assert not api_key.looks_valid("")


def test_masked_shows_only_the_end():
    assert api_key.masked("sk-ant-api03-secretx7Qa") == "sk-ant-...x7Qa"
    assert api_key.masked("") == ""


def test_not_remembered_outside_windows(monkeypatch):
    monkeypatch.setattr(api_key.sys, "platform", "linux")
    monkeypatch.delenv(api_key.ENV_NAME, raising=False)
    assert not api_key.save("sk-ant-abc123")
    assert api_key.current() == "sk-ant-abc123"
    monkeypatch.delenv(api_key.ENV_NAME, raising=False)
