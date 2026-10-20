"""Content version of the engine implementation, frozen alongside user code."""
import hashlib
from pathlib import Path

def engine_hash():
    root=Path(__file__).resolve().parent
    digest=hashlib.sha256()
    for path in sorted(root.rglob('*.py'),key=lambda p:p.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode()+b'\0')
        digest.update(path.read_bytes());digest.update(b'\0')
    return digest.hexdigest()
