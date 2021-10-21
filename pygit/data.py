from collections import namedtuple
from hashlib import sha1
from pathlib import Path
from enum import Enum
from typing import Optional, Tuple

GIT_DIR = Path(".pygit")
OBJ_DIR = GIT_DIR / "objects"
SEP_BYTE = b"\x00"


RefValue = namedtuple("RefValue", ["symbolic", "value"])


class PyGitObj(Enum):
    BLOB = b"blob"
    TREE = b"tree"
    COMMIT = b"commit"
    PARENT = b"parent"


def init() -> None:
    Path(GIT_DIR).mkdir()
    Path(OBJ_DIR).mkdir()


def update_ref(ref: str, value: RefValue) -> None:
    assert value.symbolic is False
    ref = get_ref_internal(ref)[0]
    path = GIT_DIR / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(value.value)


def get_ref(ref: str) -> Optional[RefValue]:
    return get_ref_internal(ref)[-1]


def get_ref_internal(ref: str) -> Tuple[str, RefValue]:
    path = GIT_DIR / ref
    if not path.is_file():
        return ref, RefValue(symbolic=False, value=None)
    with open(path) as f:
        value = f.read().strip()
    if value.startswith("ref:"):
        return get_ref_internal(value.split(":", 1)[-1])
    return ref, RefValue(symbolic=False, value=value)


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
