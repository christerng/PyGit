from pathlib import Path

GIT_DIR = ".pygit"


def init() -> None:
    Path(GIT_DIR).mkdir()
