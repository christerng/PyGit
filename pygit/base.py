from pathlib import Path

from . import base
from . import data


def is_ignored(path: Path) -> bool:
    return str(data.GIT_DIR) in str(path)


def write_tree(directory: Path = Path()) -> str:
    paths = []
    for child in directory.iterdir():

        if is_ignored(child):
            continue

        if child.is_file() and not child.is_symlink():
            type_ = data.PyGitObj.BLOB
            with open(child, "rb") as f:
                oid = data.hash_object(f.read())
        elif child.is_dir() and not child.is_symlink():
            type_ = data.PyGitObj.TREE
            oid = write_tree(child)

        paths.append(
            (type_.value.decode(), oid, child.name)
        )

    tree = "\n".join(f"{t} {o} {n}" for t, o, n in sorted(paths, key=lambda x: x[-1])) + "\n"
    tree = tree.encode()

    return data.hash_object(tree, data.PyGitObj.TREE)
