"""Persistent quarantine metadata for records rejected by normalizers."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from threading import RLock

from .archive import RightsAwareRawArchive

_REASON = re.compile(r'^[a-z][a-z0-9_]{1,63}$')


class RecordQuarantine:
    def __init__(self, root: Path, raw_archive: RightsAwareRawArchive):
        self.root = Path(root)
        self.raw_archive = raw_archive
        self._lock = RLock()

    def store(self, capability_id: str, endpoint: str, dataset: str, reason_code: str, record: bytes) -> dict[str, str | int]:
        if not dataset.strip() or len(dataset) > 160:
            raise ValueError('quarantine dataset identity is invalid')
        if not _REASON.fullmatch(reason_code):
            raise ValueError('quarantine requires a bounded reason code')

        # The raw archive enforces endpoint, retention, expiry, and allowed fields.
        archived = self.raw_archive.store(capability_id, endpoint, record)
        record_hash = archived['sha256']
        identity = hashlib.sha256(f'{capability_id}\0{dataset}'.encode('utf-8')).hexdigest()
        directory = self.root / 'quarantine' / identity[:8] / identity[8:16] / record_hash[:16]
        manifest_path = directory / f'{record_hash[16:]}-{reason_code}.json'
        manifest = {
            'capability_id': capability_id,
            'dataset': dataset,
            'reason_code': reason_code,
            'record_sha256': record_hash,
            'raw_archive_path': archived['path'],
            'size_bytes': archived['size_bytes'],
            'terms_reference': archived['terms_reference'],
        }
        encoded = json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode('utf-8')
        with self._lock:
            if manifest_path.exists():
                if manifest_path.read_bytes() != encoded:
                    raise ValueError('quarantine metadata conflicts with existing record')
                return manifest
            directory.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(prefix='.pending-', dir=directory)
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, 'wb') as output:
                    output.write(encoded)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temporary, manifest_path)
            except Exception:
                try:
                    temporary.unlink(missing_ok=True)
                finally:
                    raise
        return manifest
