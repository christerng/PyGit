from collections import defaultdict
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
from typing import Any, Generator, Tuple, Optional

from . import data


def compare_trees(*trees: dict) -> Generator[Tuple[Any, ...], None, None]:
    entries = defaultdict(lambda: [None] * len(trees))

    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield path, *oids


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
