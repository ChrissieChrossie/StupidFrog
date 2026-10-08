import random

from frog.jokes import JOKE_SHARE, MAX_JOKE_CHARS, JokeSource, parse_jokes


class FixedList:
    def next_quip(self) -> str:
        return "from the list"


class AlwaysJoke(random.Random):
    def random(self) -> float:
        return 0.0


class NeverJoke(random.Random):
    def random(self) -> float:
        return 1.0


def make_source(fetch, rng=None, **kwargs):
    return JokeSource(
        FixedList(), rng=rng or AlwaysJoke(), fetch=fetch, in_background=False, **kwargs
    )


def test_parses_single_and_twopart_jokes():
    data = {
        "error": False,
        "amount": 2,
        "jokes": [
            {"type": "single", "joke": "Ein kurzer Witz."},
            {"type": "twopart", "setup": "Was ist grün?", "delivery": "Ein Frosch."},
        ],
    }
    assert parse_jokes(data) == ["Ein kurzer Witz.", "Was ist grün?\nEin Frosch."]


def test_parses_a_single_joke_without_list():
    assert parse_jokes({"error": False, "type": "single", "joke": "Quak."}) == ["Quak."]


def test_skips_jokes_that_do_not_fit_and_errors():
    assert parse_jokes({"error": False, "type": "single", "joke": "x" * (MAX_JOKE_CHARS + 1)}) == []
    assert parse_jokes({"error": True, "message": "No matching joke found"}) == []


def test_tells_jokes_and_falls_back():
    source = make_source(lambda: ["Witz 1"])
    assert source.next_quip() == "Witz 1"
    assert source.next_quip() == "from the list"  # The same joke is not told twice in a row


def test_built_in_quips_most_of_the_time():
    assert JOKE_SHARE < 0.5
    source = make_source(lambda: ["Witz 1"], rng=NeverJoke())
    assert source.next_quip() == "from the list"


def test_disabled_never_fetches():
    calls = []
    source = make_source(lambda: calls.append(1) or ["Witz"], enabled=False)
    source.prefetch()
    assert source.next_quip() == "from the list"
    assert calls == []


def test_no_internet_uses_list():
    def fetch():
        raise OSError("offline")

    source = make_source(fetch)
    assert source.next_quip() == "from the list"


def test_old_jokes_come_back_after_a_break():
    source = make_source(lambda: ["Witz 1"])
    assert source.next_quip() == "Witz 1"
    assert source.next_quip() == "from the list"  # Nothing new: break
    source._paused_until = 0.0  # Break is over
    assert source.next_quip() == "Witz 1"
