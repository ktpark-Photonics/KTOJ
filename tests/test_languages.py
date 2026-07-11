import pytest

from app.judge.languages import Language, get_language


def test_python_language_adapter():
    lang = get_language("python")
    assert isinstance(lang, Language)
    assert lang.image == "ktoj-python:latest"
    assert lang.source_filename == "main.py"
    assert lang.run_cmd == ["python", "-B", "/sandbox/main.py"]
    assert lang.compile_cmd is None


def test_unknown_language_raises():
    with pytest.raises(KeyError):
        get_language("brainfuck")
