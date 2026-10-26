"""Generate/check internal API and canonical market schemas, without live calls."""
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'services/engine'))
from kestrel_engine.app import create_app  # noqa: E402
from kestrel_engine.models import (  # noqa: E402
    Candle,
    CorporateAction,
    DataQuality,
    DatasetEnvelope,
    FinancialStatement,
    Instrument,
    MarketSnapshot,
    OrderBookDepth,
    Quote,
    SourceCapability,
    Trade,
    ValueSeriesPoint,
)

MODELS = {
    model.__name__: model
    for model in [
        Instrument, Candle, Trade, Quote, OrderBookDepth, DatasetEnvelope,
        CorporateAction, FinancialStatement, ValueSeriesPoint, MarketSnapshot,
        DataQuality, SourceCapability,
    ]
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true')
parser.add_argument('--only', choices=['engine.openapi.json', 'market.schema.json', *MODELS])
args = parser.parse_args()

targets = [args.only] if args.only else ['engine.openapi.json', 'market.schema.json']
for name in targets:
    target = ROOT / 'contracts' / name
    if name == 'engine.openapi.json':
        value = create_app().openapi()
    elif name == 'market.schema.json':
        value = {key: model.model_json_schema() for key, model in MODELS.items()}
    else:
        value = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
        schema = MODELS[name].model_json_schema()
        def replace_schema(node):
            if isinstance(node, dict):
                if node.get('title') == name:
                    return schema
                return {key: replace_schema(child) for key, child in node.items()}
            if isinstance(node, list):
                return [replace_schema(child) for child in node]
            return node
        value = replace_schema(value)
        value[name] = schema

    text = json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != text:
            raise SystemExit(f'Contract drift: {target}; run scripts/export-engine-contracts.py --only {name}')
    else:
        target.parent.mkdir(exist_ok=True)
        target.write_text(text, encoding='utf-8', newline='\n')
