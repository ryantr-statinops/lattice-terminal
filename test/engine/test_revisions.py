import pytest

from kestrel_engine.revisions import deduplicate_revisions


def test_revision_dedup_drops_only_identical_repeats_and_keeps_all_revisions():
    initial = {'symbol': 'ACME', 'date': '2026-01-01', 'revision': '1', 'close': '10'}
    corrected = initial | {'revision': '2', 'close': '11'}

    result = deduplicate_revisions(
        [initial, dict(initial), corrected],
        logical_key=lambda row: (row['symbol'], row['date']),
        revision=lambda row: row['revision'],
    )

    assert result == [initial, corrected]


def test_revision_dedup_rejects_conflicting_payload_for_same_revision():
    first = {'symbol': 'ACME', 'revision': '1', 'close': '10'}
    conflict = first | {'close': '12'}

    with pytest.raises(ValueError, match='conflicting duplicate'):
        deduplicate_revisions(
            [first, conflict],
            logical_key=lambda row: row['symbol'],
            revision=lambda row: row['revision'],
        )


def test_revision_dedup_rejects_missing_revision():
    with pytest.raises(ValueError, match='non-blank string'):
        deduplicate_revisions([{'symbol': 'ACME'}], logical_key=lambda row: row['symbol'], revision=lambda row: '')
