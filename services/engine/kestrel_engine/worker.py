"""Trusted user programs run outside the API process. This is not a sandbox."""
import contextlib
import hashlib
import json
import math
import re
import runpy
import sys
import traceback
from datetime import date,datetime
from decimal import Decimal
from pathlib import Path
from .programs import inspect_source
from .version import engine_hash

def encode(value):
    if isinstance(value,(Decimal,datetime,date)):return str(value)
    if hasattr(value,'item'):return value.item()
    raise TypeError(f'unsupported output type {type(value).__name__}')

class Context:
    def __init__(self,config,manifest,sink):
        self.params=manifest['params'];self.data_root=Path(config['data_root']);self.run_id=config['id'];self.code_snapshot_id=config['snapshot'];self.engine_sha256=manifest['engine_sha256'];self.dependency_lock_sha256=hashlib.sha256(manifest['dependency_lock'].encode()).hexdigest();self._sink=sink;self._count=0
    def emit(self,kind,payload):
        self._count+=1
        if self._count>5000:raise RuntimeError('run output limit exceeded')
        text=json.dumps({'type':kind,'payload':payload},default=encode,allow_nan=False)
        if len(text)>1024*1024:raise ValueError('output event exceeds 1 MiB')
        self._sink.write(text+'\n');self._sink.flush()
    def log(self,message):self.emit('log',{'message':str(message)[:8000]})
    def table(self,name,columns,rows):
        if len(rows)>100000 or not columns or len(set(columns))!=len(columns):raise ValueError('invalid table dimensions')
        if any(len(row)!=len(columns) for row in rows):raise ValueError('table row width mismatch')
        import pyarrow as pa
        import pyarrow.parquet as pq
        directory=self.data_root/'artifacts'/self.run_id;directory.mkdir(parents=True,exist_ok=True)
        basename=re.sub('[^a-zA-Z0-9_-]','_',str(name))[:80] or 'table'
        path=directory/(basename+'.parquet');temp=path.with_suffix('.parquet.tmp')
        if path.exists():raise ValueError('artifact name already published; choose a unique table name')
        pq.write_table(pa.Table.from_pylist([dict(zip(columns,row)) for row in rows]),temp)
        temp.replace(path)
        self.emit('artifact',{'name':basename+'.parquet','path':str(path.relative_to(self.data_root).as_posix()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        self.emit('table',{'name':str(name),'columns':columns,'rows':rows[:500],'total_rows':len(rows)})
    def chart(self,name,x,y):
        if len(x)!=len(y) or len(x)>5000:raise ValueError('chart dimensions invalid')
        self.emit('chart',{'name':str(name),'x':list(x),'y':list(y)})
    def snapshot(self,key):
        from .market import MarketRepository
        return MarketRepository(self.data_root,Path(__file__).resolve().parents[3]/'data/fixtures').load(key)

class Writer:
    def __init__(self,context):self.context=context;self.buffer=''
    def write(self,text):
        self.buffer+=str(text)
        while '\n' in self.buffer:
            line,self.buffer=self.buffer.split('\n',1)
            if line:self.context.log(line)
        if len(self.buffer)>8000:self.context.log(self.buffer[:8000]);self.buffer=''
        return len(text)
    def flush(self):
        if self.buffer:self.context.log(self.buffer);self.buffer=''

def main():
    config=json.loads(sys.stdin.readline());sink=sys.stdout
    root=Path(config['data_root']);snapshot=config['snapshot']
    if not re.fullmatch('[a-f0-9]{64}',snapshot):raise ValueError('invalid code snapshot')
    directory=root/'code-snapshots'/snapshot
    raw=(directory/'manifest.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=snapshot:raise ValueError('code manifest checksum mismatch')
    manifest=json.loads(raw)
    if manifest['kind']!=config['kind']:raise ValueError('snapshot kind mismatch')
    if manifest.get('engine_sha256')!=engine_hash():raise ValueError('engine implementation differs from frozen run snapshot')
    for name,text in manifest['files'].items():
        path=directory/'files'/name
        if not path.resolve().is_relative_to((directory/'files').resolve()):raise ValueError('snapshot path escape')
        if path.read_text(encoding='utf-8')!=text:raise ValueError('code snapshot changed')
    current_lock=(Path(__file__).resolve().parents[1]/'uv.lock').read_text(encoding='utf-8')
    if current_lock!=manifest['dependency_lock']:raise ValueError('dependency lock differs from frozen run snapshot')
    entry=directory/'files'/manifest['entry']
    inspect_source(entry.read_text(encoding='utf-8-sig'),config['kind'],manifest['params'].get('kind_detection')=='selected')
    context=Context(config,manifest,sink);writer=Writer(context)
    sys.path.insert(0,str(directory/'files'))
    if manifest.get('mounted_root'):
        m_root=Path(manifest['mounted_root']).resolve()
        if m_root.is_dir() and str(m_root) not in sys.path:
            sys.path.insert(1,str(m_root))
    context.emit('state',{'status':'running'})
    try:
        with contextlib.redirect_stdout(writer),contextlib.redirect_stderr(writer):
            program=runpy.run_path(str(entry),run_name='kestrel_user_program')
            if config['kind']=='research':program['run'](context)
            elif config['kind']=='backtest':
                from .backtest import execute_program
                execute_program(program,context)
            else:
                from .strategy import execute_program
                execute_program(program,context)
            writer.flush()
        context.emit('state',{'status':'completed'})
    except BaseException as error:
        # User output is private run data, separate from redacted service diagnostics.
        context._count=0
        context.emit('error',{'message':''.join(traceback.format_exception_only(type(error),error)).strip()[:8000]})
        context.emit('state',{'status':'failed'})

if __name__=='__main__':main()
