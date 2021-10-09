from argparse import ArgumentParser, Namespace
from pathlib import Path

from . import  data


def main() -> None:
    args = parse_args()
    args.func(args)


def parse_args() -> Namespace:
    parser = ArgumentParser()

    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser("init")
    init_parser.set_defaults(func=init)

    return parser.parse_args()


def init(args:  Namespace) -> None:
	data.init()
	print(f"Initialized empty pygit repository in {Path.cwd() / data.GIT_DIR}")
