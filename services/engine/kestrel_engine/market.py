"""Immutable, checksummed fixture snapshots. No provider network calls."""
import hashlib
import json
import os
import re
import tempfile
from decimal import Decimal
from pathlib import Path
from threading import RLock
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from .models import Candle,DataQuality,Instrument,MarketSnapshot

SCHEMA=pa.schema([
    ('instrument_id',pa.string()),('interval',pa.string()),('open_time',pa.timestamp('us',tz='UTC')),
    ('close_time',pa.timestamp('us',tz='UTC')),('available_at',pa.timestamp('us',tz='UTC')),
    *[(field,pa.decimal128(38,8)) for field in ['open','high','low','close','volume']],
    ('is_closed',pa.bool_()),('revision',pa.string()),('session',pa.string()),('source_id',pa.string())
])

class MarketRepository:
    def __init__(self,root:Path,fixtures:Path):
        self.root=root/'market'
        self.fixtures=fixtures
        self.lock=RLock()

    def instruments(self)->list[Instrument]:
        return [Instrument.model_validate(v) for v in json.loads((self.fixtures/'instruments.json').read_text(encoding='utf-8'))]

    def ingest_fixture(self,path:Path)->str:
        payload=json.loads(path.read_text(encoding='utf-8'))
        if payload.get('is_synthetic') is not True: raise ValueError('fixture ingestion requires synthetic data')
        instrument=Instrument.model_validate(payload['instrument'])
        rows=[Candle.model_validate(v) for v in payload['candles']]
        seen={}
        for row in rows:
            if row.instrument_id!=instrument.id: raise ValueError('instrument mismatch')
            key=(row.interval,row.open_time,row.revision)
            if key in seen and seen[key]!=row: raise ValueError('conflicting duplicate revision')
            seen[key]=row
        rows=sorted(seen.values(),key=lambda v:(v.open_time,v.revision))
        # Multiple revisions are retained as distinct snapshots, not silently merged.
        if len({(v.interval,v.open_time) for v in rows})!=len(rows): raise ValueError('select an explicit revision before publishing')
        if any(not v.is_closed for v in rows): raise ValueError('provisional bars cannot enter historical snapshots')
        content={'schema_version':'1','parser_version':'fixture-normalizer-1','instrument':instrument.model_dump(mode='json'),'candles':[v.model_dump(mode='json') for v in rows]}
        snapshot_id=hashlib.sha256(json.dumps(content,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        target=self.root/'snapshots'/snapshot_id
        with self.lock:
            if target.exists():
                self.load(snapshot_id)
                return snapshot_id
            target.parent.mkdir(parents=True,exist_ok=True)
            temp=Path(tempfile.mkdtemp(prefix='pending-',dir=target.parent))
            data=[]
            for row in rows:
                item=row.model_dump()
                for field in ['open','high','low','close','volume']:
                    item[field]=Decimal(item[field]) if item[field] is not None else None
                data.append(item)
            pq.write_table(pa.Table.from_pylist(data,schema=SCHEMA),temp/'candles.parquet',compression='zstd')
            digest=hashlib.sha256((temp/'candles.parquet').read_bytes()).hexdigest()
            manifest={'schema_version':'1','snapshot_id':snapshot_id,'instrument':instrument.model_dump(mode='json'),'quality':DataQuality(state='fixture').model_dump(),'source_id':'SYNTHETIC-FIXTURE','is_synthetic':True,'parser_version':'fixture-normalizer-1','raw_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'parquet_sha256':digest,'row_count':len(rows),'retention_policy':'synthetic-only','coverage':{'start':rows[0].open_time.isoformat() if rows else None,'end':rows[-1].close_time.isoformat() if rows else None}}
            with (temp/'manifest.json').open('w',encoding='utf-8',newline='\n') as out:
                json.dump(manifest,out,sort_keys=True,indent=2);out.flush();os.fsync(out.fileno())
            with (temp/'candles.parquet').open('r+b') as out: os.fsync(out.fileno())
            temp.rename(target)
        return snapshot_id

    def seed(self):
        with self.lock:
            return [self.ingest_fixture(self.fixtures/(v.native_symbol+'.json')) for v in self.instruments()]

    def manifests(self):
        ids=self.seed()
        return [json.loads((self.root/'snapshots'/key/'manifest.json').read_text()) for key in ids]

    def load(self,key:str)->MarketSnapshot:
        if not re.fullmatch('[0-9a-f]{64}',key): raise ValueError('invalid snapshot identity')
        path=self.root/'snapshots'/key
        manifest=json.loads((path/'manifest.json').read_text())
        if manifest['snapshot_id']!=key: raise ValueError('manifest identity mismatch')
        parquet=path/'candles.parquet'
        if hashlib.sha256(parquet.read_bytes()).hexdigest()!=manifest['parquet_sha256']: raise ValueError('snapshot checksum mismatch')
        with duckdb.connect(':memory:') as connection:
            table=connection.execute('SELECT * FROM read_parquet(?) ORDER BY open_time',[str(parquet)]).to_arrow_table()
        rows=[]
        for row in table.to_pylist():
            for field in ['open','high','low','close','volume']:
                row[field]=str(row[field]) if row[field] is not None else None
            rows.append(Candle.model_validate(row))
        if len(rows)!=manifest['row_count']: raise ValueError('snapshot row count mismatch')
        return MarketSnapshot(snapshot_id=key,instrument=manifest['instrument'],quality=manifest['quality'],candles=rows)

    def latest_fixture(self,instrument_id:str):
        for manifest in self.manifests():
            if manifest['instrument']['id']==instrument_id: return self.load(manifest['snapshot_id'])
        raise ValueError('instrument not found')
