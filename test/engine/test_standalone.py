from pathlib import Path

import pytest

from kestrel_engine.__main__ import read_env


def test_read_env_supports_quotes_comments_and_utf8(tmp_path: Path):
    env = tmp_path / '.env'
    env.write_text("KESTREL_ENGINE_TOKEN='abc # 123'\nKESTREL_DATA_DIR=./data # relative to repo\nNAME=Tiếng Việt\n", encoding='utf-8')

    assert read_env(env) == {
        'KESTREL_ENGINE_TOKEN': 'abc # 123',
        'KESTREL_DATA_DIR': './data',
        'NAME': 'Tiếng Việt',
    }


def test_read_env_rejects_duplicate_without_echoing_value(tmp_path: Path):
    env = tmp_path / '.env'
    env.write_text('KESTREL_ENGINE_TOKEN=secret-value\nKESTREL_ENGINE_TOKEN=other-secret\n', encoding='utf-8')

    with pytest.raises(RuntimeError, match='Duplicate assignment') as error:
        read_env(env)
    assert 'secret-value' not in str(error.value)
