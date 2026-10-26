"""Deterministic de-duplication that never silently collapses revisions."""
import json
from collections.abc import Callable, Hashable, Iterable
from typing import TypeVar

T = TypeVar('T')


def deduplicate_revisions(
    records: Iterable[T],
    *,
    logical_key: Callable[[T], Hashable],
    revision: Callable[[T], str],
) -> list[T]:
    """Drop identical key+revision duplicates and reject conflicting duplicates.

    Distinct revisions for the same logical record remain separate in the result.
    This function does not decide which revision is authoritative.
    """
    seen: dict[tuple[Hashable, str], str] = {}
    result: list[T] = []
    for record in records:
        revision_id = revision(record)
        if not isinstance(revision_id, str) or not revision_id.strip():
            raise ValueError('record revision must be a non-blank string')
        key = (logical_key(record), revision_id)
        if hasattr(record, 'model_dump'):
            payload = record.model_dump(mode='json')
        elif isinstance(record, dict):
            payload = record
        else:
            raise TypeError('revision records must be mappings or Pydantic models')
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        previous = seen.get(key)
        if previous is None:
            seen[key] = canonical
            result.append(record)
        elif previous != canonical:
            raise ValueError('conflicting duplicate record for logical key and revision')
    return result
