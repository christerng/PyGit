from collections import defaultdict
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from typing import Any, Generator, Tuple, Optional

from . import data


def compare_trees(*trees: dict) -> Generator[Tuple[str, ...], None, None]:
    entries = defaultdict(lambda: [None] * len(trees))

    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield path, *oids


def iter_changed_files(
    tree_from: dict,
    tree_to: dict
) -> Generator[Tuple[str, str], None, None]:
    for path, oid_from, oid_to in compare_trees(tree_from, tree_to):
        if oid_from != oid_to:
            action = (
                "new file" if not oid_from else
                "deleted" if not oid_to else
                "modified"
            )
            yield path, action


def diff_trees(tree_from: dict, tree_to: dict) -> str:
    output = b""
    for path, oid_from, oid_to in compare_trees(tree_from, tree_to):
        if oid_from != oid_to:
            output += diff_blobs(oid_from, oid_to, path)
    return output


def diff_blobs(oid_from: Optional[str], oid_to: Optional[str], path: str = "blob") -> str:
    with NamedTemporaryFile() as file_from, NamedTemporaryFile() as file_to:

        if oid_from is not None:
            file_from.write(data.get_object(oid_from))
            file_from.flush()

        if oid_to is not None:
            file_to.write(data.get_object(oid_to))
            file_to.flush()

        with Popen(
            [
                "diff",
                "--unified",
                "--show-c-function",
                "--label", f"a/{path}", file_from.name,
                "--label", f"b/{path}", file_to.name,
            ], stdout=PIPE
        ) as proc:
            return proc.communicate()[0]


def merge_trees(tree_base: dict, tree_head: dict, tree_other: dict) -> dict:
    tree = {}
    for path, oid_base, oid_head, oid_other in compare_trees(tree_base, tree_head, tree_other):
        tree[path] = merge_blobs(oid_base, oid_head, oid_other)
    return tree


def merge_blobs(
    oid_base: Optional[str],
    oid_head: Optional[str],
    oid_other: Optional[str]
) -> str:
    with NamedTemporaryFile() as file_base, NamedTemporaryFile() as file_head, NamedTemporaryFile() as file_other:

        if oid_base is not None:
            file_base.write(data.get_object(oid_base))
            file_base.flush()

        if oid_head is not None:
            file_head.write(data.get_object(oid_head))
            file_head.flush()

        if oid_other is not None:
            file_other.write(data.get_object(oid_other))
            file_other.flush()

        with Popen(
            [
                "diff3", "-m",
                "-L", "HEAD", file_head.name,
                "-L", "BASE", file_base.name,
                "-L", "MERGE_HEAD", file_other.name
            ], stdout=PIPE
        ) as proc:
            return proc.communicate()[0]
