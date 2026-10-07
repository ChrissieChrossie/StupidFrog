import pytest

from frog.safety import OutsidePlayground, safe_path


def test_path_inside_playground_is_ok(tmp_path):
    assert safe_path(tmp_path, "box/file.txt") == (tmp_path / "box/file.txt").resolve()


def test_playground_itself_is_ok(tmp_path):
    assert safe_path(tmp_path, tmp_path) == tmp_path.resolve()


def test_dot_dot_escape_is_blocked(tmp_path):
    with pytest.raises(OutsidePlayground):
        safe_path(tmp_path / "playground", "../secret.txt")


def test_absolute_path_outside_is_blocked(tmp_path):
    with pytest.raises(OutsidePlayground):
        safe_path(tmp_path / "playground", tmp_path / "other" / "file.txt")


def test_similar_name_is_blocked(tmp_path):
    # "playground-2" starts like "playground" but is not inside it.
    with pytest.raises(OutsidePlayground):
        safe_path(tmp_path / "playground", tmp_path / "playground-2" / "file.txt")
