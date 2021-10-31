from collections import namedtuple
from hashlib import sha1
from pathlib import Path
from enum import Enum
from typing import Optional, Tuple, Generator

GIT_DIR = Path(".pygit")
OBJ_DIR = GIT_DIR / "objects"
REF_DIR = GIT_DIR / "refs"
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


def update_ref(ref: str, value: RefValue, deref: bool = True) -> None:
    assert value.value is not None
    ref = get_ref_internal(ref, deref)[0]
    path = GIT_DIR / ref
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write(
            f"ref: {value.value}" if value.symbolic is True else value.value
        )


def get_ref(ref: str, deref: bool = True) -> RefValue:
    return get_ref_internal(ref, deref)[-1]


def delete_ref(ref: str, deref: bool = True) -> None:
    ref = get_ref_internal(ref, deref)[0]
    (GIT_DIR / ref).unlink()


def get_ref_internal(ref: str, deref: bool) -> Tuple[str, RefValue]:
    path = GIT_DIR / ref

    if not path.is_file():
        return ref, RefValue(symbolic=False, value=None)

    with open(path) as f:
        value = f.read().strip()
    symbolic = value.startswith("ref:")
    if symbolic is True:
        value = value.split(":", 1)[1].strip()
        if deref is True:
            return get_ref_internal(value, deref)

    return ref, RefValue(symbolic=symbolic, value=value)


def iter_refs(
    prefix: str = "",
    deref: bool = True
) -> Generator[Tuple[str, RefValue], None, None]:
    for ref in Path(REF_DIR).rglob("*"):
        refname = str(ref)
        if not refname.startswith(prefix):
            continue
        yield refname, get_ref(str(ref.relative_to(GIT_DIR)), deref=deref)


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
