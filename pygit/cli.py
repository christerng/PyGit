from argparse import ArgumentParser, Namespace
from collections import defaultdict
from pathlib import Path
from sys import stdout
from textwrap import indent
from typing import Optional, List

from . import base, data, diff


def main() -> None:
    args = parse_args()
    args.func(args)


def parse_args() -> Namespace:
    parser = ArgumentParser()

    commands = parser.add_subparsers(dest="command", required=True)

    oid = base.get_oid

    init_parser = commands.add_parser(name="init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser(name="hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser(name="cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object", type=oid)

    write_tree_parser = commands.add_parser(name="write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser(name="read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree", type=oid)

    commit_parser = commands.add_parser(name="commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser(name="log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", default="@", type=oid, nargs="?")

    checkout_parser = commands.add_parser(name="checkout")
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument("commit")

    tag_parser = commands.add_parser(name="tag")
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument("name")
    tag_parser.add_argument("oid", default="@", type=oid, nargs="?")

    branch_parser = commands.add_parser(name="branch")
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument("name", nargs="?")
    branch_parser.add_argument("start", default="@", type=oid, nargs="?")

    status_parser = commands.add_parser(name="status")
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser(name="reset")
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument("commit", type=oid)

    show_parser = commands.add_parser(name="show")
    show_parser.set_defaults(func=show)
    show_parser.add_argument("oid", default="@", type=oid, nargs="?")

    diff_parser = commands.add_parser(name="diff")
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument("commit", default="@", type=oid, nargs="?")

    merge_parser = commands.add_parser(name="merge")
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument("commit", type=oid)

    return parser.parse_args()


def init(args: Namespace) -> None:
    base.init()
    print(f"Initialized empty pygit repository in {Path.cwd() / data.GIT_DIR}")


def hash_object(args: Namespace) -> None:
    with open(args.file, "rb") as f:
        print(data.hash_object(f.read()))


def cat_file(args: Namespace) -> None:
    stdout.flush()
    stdout.buffer.write(data.get_object(args.object, expected=None))


def write_tree(args: Namespace) -> None:
    print(base.write_tree())


def read_tree(args: Namespace) -> None:
    base.read_tree(args.tree)


def commit(args: Namespace) -> None:
    print(base.commit(args.message))


def log(args: Namespace) -> None:
    refs = defaultdict(list)
    for refname, ref in data.iter_refs():
        refs[ref.value].append(refname)

    for oid in base.iter_commits_and_parents({args.oid}):
        commit = base.get_commit(oid)
        print_commit(oid, commit, refs.get(oid))


def checkout(args: Namespace) -> None:
    base.checkout(args.commit)


def tag(args: Namespace) -> None:
    base.create_tag(args.name, args.oid)


def branch(args: Namespace) -> None:
    if args.name is None:
        current = base.get_branch_name()
        for branch in base.iter_branch_names():
            prefix = "*" if branch == current else " "
            print(f"{prefix} {branch}")
    else:
        base.create_branch(args.name, args.start_point)
        print(f"Branch {args.name} created at {args.start_point[:10]}")


def status(args: Namespace) -> None:
    head = base.get_oid("@")
    branch = base.get_branch_name()
    if branch is None:
        print(f"HEAD detached at {head[:10]}")
    else:
        print(f"On branch {branch}")
    print("\nChanges to be committed:\n")
    head_tree = head and base.get_commit(head).tree
    for path, action in diff.iter_changed_files(
        base.flatten_tree(head_tree),
        base.get_working_tree()
    ):
        print(f"{action:>12}: {path}")


def reset(args: Namespace) -> None:
    base.reset(args.commit)


def show(args: Namespace) -> None:
    commit = base.get_commit(args.oid)
    print_commit(args.oid, commit)

    if commit.parents is None:
        return
    parent_tree = base.get_commit(commit.parents[0]).tree
    stdout.flush()
    stdout.buffer.write(
        diff.diff_trees(
            base.flatten_tree(parent_tree),
            base.flatten_tree(commit.tree)
        )
    )


def print_commit(
    oid: str,
    commit: base.Commit,
    refs: Optional[List[str]] = None
) -> None:
    refs_str = f" ({', '.join(refs)})" if refs else ""
    print(f"commit {oid}{refs_str}", end="\n\n")
    print(indent(commit.message, "    "), end="\n\n")


def _diff(args: Namespace) -> None:
    tree = args.commit and base.get_commit(args.commit).tree
    stdout.flush()
    stdout.buffer.write(
        diff.diff_trees(
            base.flatten_tree(tree),
            base.get_working_tree()
        )
    )


def merge(args: Namespace) -> None:
    base.merge(args.commit)
