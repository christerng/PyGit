from hashlib import sha1
from pathlib import Path
from enum import Enum
from typing import Optional

GIT_DIR = Path(".pygit")
OBJ_DIR = GIT_DIR / "objects"
SEP_BYTE = b"\x00"


class PyGitObj(Enum):
    BLOB = b"blob"
    TREE = b"tree"
    COMMIT = b"commit"
    PARENT = b"parent"


def init() -> None:
    Path(GIT_DIR).mkdir()
    Path(OBJ_DIR).mkdir()


def set_HEAD(oid: str) -> None:
    with open(GIT_DIR / "HEAD", "w") as f:
        f.write(oid)


def get_HEAD() -> Optional[str]:
    path = GIT_DIR / "HEAD"
    if not path.is_file():
        return
    with open(path) as f:
        return f.read()


def hash_object(data: bytes, type_: PyGitObj = PyGitObj.BLOB) -> str:
    oid = sha1(data).hexdigest()
    with open(OBJ_DIR / oid, "wb") as f:
        f.write(type_.value + SEP_BYTE + data)
    return oid


def get_object(oid: str, expected: Optional[PyGitObj] = PyGitObj.BLOB) -> bytes:
    with open(OBJ_DIR / oid, "rb") as f:
        type_, content = f.read().split(SEP_BYTE, maxsplit=1)
    if expected is not None:
        assert type_ == expected.value, f"Expected {expected}, got {type_.decode()}"
    return content
