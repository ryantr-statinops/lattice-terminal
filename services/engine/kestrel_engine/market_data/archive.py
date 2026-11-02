"""Raw provider payload archive guarded by the exact approved retention scope."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from threading import RLock

from .sources import SourceGate


class RightsAwareRawArchive:
    def __init__(self, root: Path, source_gate: SourceGate):
        self.root = Path(root)
        self.source_gate = source_gate
        self._lock = RLock()

    def store(self, capability_id: str, endpoint: str, payload: bytes) -> dict[str, str | int]:
        """Store bytes only when the active source policy allows retention."""
        if not isinstance(payload, bytes) or not payload:
            raise ValueError('raw archive payload must be non-empty bytes')
        if len(payload) > 64 * 1024 * 1024:
            raise ValueError('raw archive payload exceeds 64 MiB')

        scope = self.source_gate.authorize(capability_id, 'store', endpoint)
        try:
            document = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError('raw archive requires a parseable JSON payload for field-scope validation') from error
        permitted_fields = set(scope.fields)
        if not _field_names(document).issubset(permitted_fields):
            raise ValueError('raw payload contains fields outside the approved retention scope')
        digest = hashlib.sha256(payload).hexdigest()
        identity = hashlib.sha256(capability_id.encode('utf-8')).hexdigest()
        target_dir = self.root / 'raw' / identity[:2] / identity
        target = target_dir / f'{digest}.raw'
        with self._lock:
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                    raise ValueError('raw archive content hash mismatch')
                return {'sha256': digest, 'size_bytes': len(payload), 'path': str(target), 'terms_reference': scope.terms_reference}

            target_dir.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix='.pending-', dir=target_dir)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(payload)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, target)
            except Exception:
                try:
                    temporary.unlink(missing_ok=True)
                finally:
                    raise
        return {'sha256': digest, 'size_bytes': len(payload), 'path': str(target), 'terms_reference': scope.terms_reference}


def _field_names(value) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_field_names(child) for child in value.values()))
    if isinstance(value, list):
        return set().union(*(_field_names(child) for child in value)) if value else set()
    return set()
