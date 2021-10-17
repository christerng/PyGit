from collections import namedtuple
from pathlib import Path
from typing import Generator

from . import base, data

Commit = namedtuple("Commit", ["tree", "parent", "message"])


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

    tree = "\n".join(f"{t} {o} {n}" for t, o, n in sorted(
        paths, key=lambda x: x[-1]
    )) + "\n"
    tree = tree.encode()

    return data.hash_object(tree, data.PyGitObj.TREE)


def iter_tree_entries(oid: str) -> Generator[list, None, None]:
    if oid is None:
        return
    tree = data.get_object(oid, data.PyGitObj.TREE)
    for entry in tree.decode().splitlines():
        yield entry.split(maxsplit=2)


def flatten_tree(oid: str, base_path: Path = Path()) -> dict:
    result = {}
    for type_, oid, name in iter_tree_entries(oid):
        type_ = type_.encode()
        path = base_path / name
        if type_ == data.PyGitObj.BLOB.value:
            result[path] = oid
        elif type_ == data.PyGitObj.TREE.value:
            result = {**result, **flatten_tree(oid, path)}
        else:
            raise TypeError(f"Unknown tree entry {type_}")
    return result


def empty_current_directory() -> None:
    for child in Path().iterdir():
        if is_ignored(child):
            continue
        if child.is_file() and not child.is_symlink():
            child.unlink()
        elif child.is_dir() and not child.is_symlink():
            try:
                child.rmdir()
            except OSError:
                pass


def read_tree(oid: str) -> None:
    empty_current_directory()
    for path, oid in flatten_tree(oid).items():
        path.parent.mkdir(exist_ok=True)
        with open(path, "wb") as f:
            f.write(data.get_object(oid))


def commit(message: str) -> str:
    commit = f"tree {write_tree()}\n"

    head = data.get_HEAD()
    if head is not None:
        commit += f"parent {head}\n"

    commit += f"\n{message}\n"
    oid = data.hash_object(commit.encode(), data.PyGitObj.COMMIT)
    data.set_HEAD(oid)
    return oid


def checkout(oid: str) -> None:
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.set_HEAD(oid)


def create_tag(name: str, oid: str) -> None:
    pass


def get_commit(oid: str) -> Commit:
    parent = None
    commit = data.get_object(oid, data.PyGitObj.COMMIT).decode()
    for line in iter(commit.splitlines()):
        if len(line) == 0:
            continue
        key, value = line.split(maxsplit=1)
        if key == data.PyGitObj.TREE.value.decode():
            tree = value
        elif key == data.PyGitObj.PARENT.value.decode():
            parent = value
    return Commit(tree=tree, parent=parent, message=commit)


def is_ignored(path: Path) -> bool:
    return str(data.GIT_DIR) in str(path)
