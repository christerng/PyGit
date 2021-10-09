import argparse
from argparse import ArgumentParser, Namespace


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
    print("Hello, World")
