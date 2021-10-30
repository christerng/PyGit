from collections import defaultdict
from typing import Generator, Tuple, Any


def compare_trees(*trees: dict) -> Generator[Tuple[Any, ...], None, None]:
    entries = defaultdict(lambda: [None] * len(trees))

    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield path, *oids


def diff_trees(tree_from: dict, tree_to: dict) -> str:
    output = ""
    for path, oid_from, oid_to in compare_trees(tree_from, tree_to):
        if oid_from != oid_to:
            output += f"changed: {path}\n"
    return output
