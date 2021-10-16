from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import stdout
from textwrap import indent

from . import base, data


def main() -> None:
    args = parse_args()
    args.func(args)


def parse_args() -> Namespace:
    parser = ArgumentParser()

    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser(name="init")
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser(name="hash-object")
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument("file")

    cat_file_parser = commands.add_parser(name="cat-file")
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument("object")

    write_tree_parser = commands.add_parser(name="write-tree")
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser(name="read-tree")
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument("tree")

    commit_parser = commands.add_parser(name="commit")
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument("-m", "--message", required=True)

    log_parser = commands.add_parser(name="log")
    log_parser.set_defaults(func=log)
    log_parser.add_argument("oid", nargs="?")

    return parser.parse_args()


def init(args: Namespace) -> None:
    data.init()
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
    oid = args.oid or data.get_HEAD()
    while oid is not None:
        commit = base.get_commit(oid)
        print(f"commit {oid}")
        print(indent(commit.message, "    "), end="\n\n")
        oid = commit.parent
