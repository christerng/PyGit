from hashlib import sha1
from pathlib import Path

GIT_DIR = ".pygit"


def init() -> None:
    Path(GIT_DIR).mkdir()
    Path(GIT_DIR, "objects").mkdir()


def hash_object(data: bytes) -> str:
    oid = sha1(data).hexdigest()
    with open(Path(GIT_DIR, "objects", oid), "wb") as out:
        out.write(data)
    return oid


def get_object(oid: str) -> bytes:
    with open(Path(GIT_DIR, "objects", oid), "rb") as f:
        return f.read()
