from pathlib import Path

from . import base


def write_tree(directory: Path = Path()) -> None:
    for child in directory.iterdir():
        if child.is_file() and not child.is_symlink():
            print(child)
        elif child.is_dir() and not child.is_symlink():
            write_tree(child)
