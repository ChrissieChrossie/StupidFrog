from frog.sound import Sound


class FakeMci:
    def __init__(self, result=0):
        self.commands = []
        self.result = result

    def __call__(self, command):
        self.commands.append(command)
        return self.result


def make_file(tmp_path):
    path = tmp_path / "croak.mp3"
    path.write_bytes(b"x")
    return path


def test_plays_only_the_beginning(tmp_path):
    mci = FakeMci()
    sound = Sound(make_file(tmp_path), 1000, mci=mci)
    sound.play()
    sound.play()
    assert sum(c.startswith("open") for c in mci.commands) == 1  # Loaded only once
    assert mci.commands[-1].endswith("from 0 to 1000")


def test_disabled_is_silent(tmp_path):
    mci = FakeMci()
    Sound(make_file(tmp_path), 1000, enabled=False, mci=mci).play()
    assert mci.commands == []


def test_missing_file_is_ignored(tmp_path):
    mci = FakeMci()
    sound = Sound(tmp_path / "missing.mp3", 1000, mci=mci)
    sound.play()
    sound.play()
    assert mci.commands == []


def test_failure_is_tried_only_once(tmp_path):
    mci = FakeMci(result=263)
    sound = Sound(make_file(tmp_path), 1000, mci=mci)
    sound.play()
    sound.play()
    assert len(mci.commands) == 1
