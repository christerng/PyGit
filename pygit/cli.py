from argparse import ArgumentParser, Namespace
from pathlib import Path
from sys import base_prefix, stdout
from textwrap import indent

from . import base, data


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
    branch_parser.add_argument("name")
    branch_parser.add_argument("start", default="@", type=oid, nargs="?")

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
    for oid in base.iter_commits_and_parents({args.oid}):
        commit = base.get_commit(oid)
        print(f"commit {oid}")
        print(indent(commit.message, "    "), end="\n\n")


def checkout(args: Namespace) -> None:
    base.checkout(args.commit)


def tag(args: Namespace) -> None:
    base.create_tag(args.name, args.oid)


def branch(args: Namespace) -> None:
    base.create_branch(args.name, args.start)
    print(f"Branch {args.name} created at {args.start[:10]}")
