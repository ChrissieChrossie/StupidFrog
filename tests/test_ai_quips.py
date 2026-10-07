import anthropic
import httpx2
import pytest

from frog.ai_quips import (
    BASE_RULES,
    DEFAULT_PERSONALITY,
    LEGACY_PERSONALITIES,
    MAX_PERSONALITY_CHARS,
    AiQuipSource,
    ai_available,
    build_system_prompt,
    normalize_personality,
    parse_quips,
)


class FixedList:
    def next_quip(self) -> str:
        return "from the list"


def always_available():
    return True, ""


def make_source(fetch, **kwargs):
    values = {
        "fallback": FixedList(),
        "model": "test",
        "fetch": fetch,
        "in_background": False,
        "availability": always_available,
    }
    values.update(kwargs)
    return AiQuipSource(**values)


def test_serves_ai_quips():
    source = make_source(lambda: ["Quak from Claude", "Another one"])
    source.prefetch()
    assert source.next_quip() == "Quak from Claude"
    assert source.next_quip() == "Another one"


def test_disabled_never_asks_claude():
    def fetch():
        raise AssertionError("must not be called")

    source = make_source(fetch, enabled=False)
    assert source.next_quip() == "from the list"


def test_without_key_uses_fallback():
    source = make_source(lambda: ["AI"], availability=lambda: (False, "no key"))
    assert source.next_quip() == "from the list"


def test_error_falls_back_and_pauses():
    calls = []

    def fetch():
        calls.append(1)
        raise RuntimeError("server gone")

    source = make_source(fetch)
    assert source.next_quip() == "from the list"
    assert source.next_quip() == "from the list"
    assert len(calls) == 1  # Pauses after an error


def test_invalid_key_blocks_ai():
    request = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
    response = httpx2.Response(401, request=request)

    def fetch():
        raise anthropic.AuthenticationError("invalid", response=response, body=None)

    source = make_source(fetch)
    assert source.next_quip() == "from the list"
    assert not source.active


def test_enabling_while_running():
    source = make_source(lambda: ["AI quip"], enabled=False)
    assert source.next_quip() == "from the list"
    source.enabled = True
    source.prefetch()
    assert source.next_quip() == "AI quip"


def test_reply_lines_are_cleaned_up():
    text = '1. "Quak!"\n- Du tippst zu laut.\n\n• Fliegen sind auch Essen.\n' + "x" * 200
    assert parse_quips(text) == ["Quak!", "Du tippst zu laut.", "Fliegen sind auch Essen."]


@pytest.mark.parametrize("key, expected", [("", False), ("sk-test", True)])
def test_availability_needs_a_key(monkeypatch, key, expected):
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    assert ai_available()[0] is expected


def test_system_prompt_contains_personality_and_rules():
    prompt = build_system_prompt("Ein müder Opa-Frosch, der immer jammert.")
    assert "müder Opa-Frosch" in prompt
    assert BASE_RULES in prompt


def test_empty_personality_uses_default():
    assert DEFAULT_PERSONALITY in build_system_prompt("   ")


def test_too_long_personality_is_truncated():
    source = make_source(lambda: [])
    source.set_personality("x" * 5000)
    assert len(source.personality) == MAX_PERSONALITY_CHARS


def test_new_personality_drops_old_quips():
    replies = iter([["old 1", "old 2", "old 3"], ["new 1", "new 2", "new 3"]])
    source = make_source(lambda: next(replies))
    source.prefetch()
    source.set_personality("Ein Pirat")
    assert source.personality == "Ein Pirat"
    assert source.next_quip() == "new 1"


def test_saved_default_personalities_become_empty():
    assert normalize_personality(LEGACY_PERSONALITIES[0]) == ""
    assert normalize_personality(DEFAULT_PERSONALITY) == ""
    assert normalize_personality(" Ein Pirat. ") == "Ein Pirat."


def test_default_personality_is_a_sarcastic_desktop_manager():
    assert "Desktop-Manager" in DEFAULT_PERSONALITY
    assert "sarkastisch" in DEFAULT_PERSONALITY
