from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = REPO_ROOT / 'services' / 'engine'
FIXTURE_ROOT = REPO_ROOT / 'data' / 'fixtures'

@pytest.fixture(scope='session')
def repository_paths():
    return {'root': REPO_ROOT, 'engine': ENGINE_ROOT, 'fixtures': FIXTURE_ROOT}
