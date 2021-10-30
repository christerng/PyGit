from collections import deque, namedtuple
from pathlib import Path
from string import hexdigits
from typing import Generator, Set, Optional

from . import base, data

Commit = namedtuple("Commit", ["tree", "parent", "message"])


def init() -> None:
    data.init()
    data.update_ref(
        "HEAD", data.RefValue(symbolic=True, value="refs/heads/master")
    )


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

    head = data.get_ref("HEAD").value
    if head is not None:
        commit += f"parent {head}\n"

    commit += f"\n{message}\n"
    oid = data.hash_object(commit.encode(), data.PyGitObj.COMMIT)
    data.update_ref("HEAD", data.RefValue(symbolic=False, value=oid))
    return oid


def checkout(name: str) -> None:
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree)

    if is_branch(name):
        head = data.RefValue(symbolic=True, value=f"refs/heads/{name}")
    else:
        head = data.RefValue(symbolic=False, value=oid)
    data.update_ref("HEAD", head, deref=False)


def create_tag(name: str, oid: str) -> None:
    data.update_ref(
        Path("refs", "tags", name), data.RefValue(symbolic=False, value=oid)
    )


def create_branch(name: str, oid: str) -> None:
    data.update_ref(
        Path("refs", "heads", name), data.RefValue(symbolic=False, value=oid)
    )


def get_branch_name() -> Optional[str]:
    head = data.get_ref("HEAD", deref=False)
    if head.symbolic is False:
        return
    assert head.value.startswith("refs/heads/")
    return Path.relative_to(Path(head.value), Path("refs/heads"))


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


def iter_commits_and_parents(oids: Set[str]) -> Generator[str, None, None]:
    oids = deque(oids)
    visited = set()

    while len(oids) > 0:
        oid = oids.popleft()
        if oid is None or oid in visited:
            continue
        visited.add(oid)
        yield oid

        commit = get_commit(oid)
        oids.appendleft(commit.parent)


def iter_branch_names() -> Generator[str, None, None]:
    for refname, _ in data.iter_refs(".pygit/refs/heads/"):
        yield Path.relative_to(Path(refname), Path(".pygit/refs/heads/"))


def get_oid(name: str) -> str:
    if name == "@":
        name = "HEAD"

    refs = [
        f"{name}",
        f"refs/{name}",
        f"refs/tags/{name}",
        f"refs/heads/{name}"
    ]
    for ref in refs:
        if data.get_ref(ref, deref=False).value is not None:
            return data.get_ref(ref).value

    is_hex = all(char in hexdigits for char in name)
    if is_hex is True and len(name) == 40:
        return name

    raise Exception(f"Unknown name {name}")


def is_ignored(path: Path) -> bool:
    return str(data.GIT_DIR) in str(path)


def is_branch(branch: str) -> bool:
    return data.get_ref(Path("refs", "heads", branch)).value is not None
