from app.judge.grader import normalize, outputs_match


def test_exact_match():
    assert outputs_match("3\n", "3\n") is True


def test_trailing_whitespace_ignored():
    assert outputs_match("3 \n", "3\n") is True


def test_trailing_newlines_ignored():
    assert outputs_match("3\n\n\n", "3") is True


def test_wrong_answer():
    assert outputs_match("4\n", "3\n") is False


def test_multiline_match():
    assert outputs_match("1\n2\n3\n", "1\n2\n3") is True


def test_normalize_strips_line_trailing_and_end_blanks():
    assert normalize("a  \nb\t\n\n") == "a\nb"
