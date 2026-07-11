from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    name: str
    image: str
    source_filename: str
    run_cmd: list[str]
    compile_cmd: list[str] | None = None


LANGUAGES: dict[str, Language] = {
    "python": Language(
        name="python",
        image="ktoj-python:latest",
        source_filename="main.py",
        run_cmd=["python", "-B", "/sandbox/main.py"],
        compile_cmd=None,
    ),
}


def get_language(name: str) -> Language:
    return LANGUAGES[name]
