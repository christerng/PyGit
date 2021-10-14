from argparse import ArgumentParser, Namespace
from os import waitpid
from pathlib import Path
from sys import stdout

from . import data
from . import base


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
