from pathlib import Path

from . import base
from . import data


def is_ignored(path: Path) -> bool:
    return str(data.GIT_DIR) in str(path)


def write_tree(directory: Path = Path()) -> None:
    for child in directory.iterdir():
        if is_ignored(child):
            continue
        if child.is_file() and not child.is_symlink():
            with open(child, "rb") as f:
                print(data.hash_object(f.read()), child)
        elif child.is_dir() and not child.is_symlink():
            write_tree(child)
