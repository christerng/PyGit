import abc
from hashlib import sha1
from pathlib import Path
from typing import Union
from enum import Enum

GIT_DIR = ".pygit"


class PyGitObj(Enum):
    BLOB = "blob"
    TREE = "tree"


def init() -> None:
    Path(GIT_DIR).mkdir()
    Path(GIT_DIR, "objects").mkdir()


def hash_object(data: bytes, type_: PyGitObj = PyGitObj.BLOB) -> str:
    obj = (type_.value + "\x00").encode() + data
    oid = sha1(data).hexdigest()
    with open(Path(GIT_DIR, "objects", oid), "wb") as out:
        out.write(obj)
    return oid


def get_object(oid: str, expected: PyGitObj = PyGitObj.BLOB) -> bytes:
    with open(Path(GIT_DIR, "objects", oid), "rb") as f:
        obj = f.read()
    type_,  content = obj.split("\x00".encode(), 1)
    type_ = type_.decode()
    if expected is not None:
        assert type_ == expected.value, f"Expected {expected}, got {type_}"
    return content
