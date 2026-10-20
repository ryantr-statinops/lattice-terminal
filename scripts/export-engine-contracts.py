"""Generate/check internal API and canonical market schemas, without live calls."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/engine'))
from kestrel_engine.app import create_app  # noqa: E402
from kestrel_engine.models import Instrument, MarketSnapshot, DataQuality, SourceCapability  # noqa: E402

outputs = {
    'engine.openapi.json': create_app().openapi(),
    'market.schema.json': {name.__name__: name.model_json_schema() for name in [Instrument, MarketSnapshot, DataQuality, SourceCapability]},
}
for name, value in outputs.items():
    target = ROOT / 'contracts' / name
    text = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n'
    if '--check' in sys.argv:
        if not target.exists() or target.read_text(encoding='utf-8') != text:
            raise SystemExit(f'Contract drift: {target}; run scripts/export-engine-contracts.py')
    else:
        target.parent.mkdir(exist_ok=True)
        target.write_text(text, encoding='utf-8', newline='\n')
