from app.judge.hints import hint_for


def test_name_error_gives_typo_hint():
    h = hint_for("RE", "NameError: name 'prin' is not defined. "
                       "Did you mean: 'print'?")
    assert h is not None
    assert "오타" in h


def test_value_error_gives_parsing_hint():
    h = hint_for("RE", "ValueError: invalid literal for int() with base 10")
    assert "int" in h


def test_zero_division_hint():
    assert "0" in hint_for("RE", "ZeroDivisionError: division by zero")


def test_ce_syntax_error_hint():
    h = hint_for("CE", "SyntaxError: invalid syntax")
    assert h is not None
    assert "문법" in h


def test_indentation_error_hint():
    h = hint_for("CE", "IndentationError: expected an indented block")
    assert "들여쓰기" in h


def test_re_without_message_falls_back_to_generic():
    h = hint_for("RE", None)
    assert h is not None  # generic RE hint, not a crash


def test_wa_generic_hint():
    assert "경계값" in hint_for("WA", None)


def test_tle_generic_hint():
    assert "시간" in hint_for("TLE", None)


def test_ac_has_no_hint():
    assert hint_for("AC", None) is None


def test_pending_has_no_hint():
    assert hint_for("PENDING", None) is None
