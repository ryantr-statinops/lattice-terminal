"""Run as a supervised child or as a standalone local debug service."""
import argparse
import json
import os
import socket
import sys
from pathlib import Path
import uvicorn
from .app import create_app

def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding='utf-8-sig').splitlines()
    except OSError as exc:
        raise RuntimeError('Cannot read repository .env; copy .env.example and configure it first') from exc
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].lstrip()
        key, separator, value = line.partition('=')
        if not separator or not key.strip():
            raise RuntimeError('Invalid assignment in repository .env (values redacted)')
        key, value = key.strip(), value.strip()
        if key in values:
            raise RuntimeError('Duplicate assignment in repository .env (values redacted)')
        if value.startswith("'"):
            if len(value) < 2 or not value.endswith("'"):
                raise RuntimeError('Invalid quoted value in repository .env (values redacted)')
            value = value[1:-1]
        elif value.startswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as exc:
                raise RuntimeError('Invalid quoted value in repository .env (values redacted)') from exc
        else:
            value = value.split(' #', 1)[0].strip()
        values[key] = value
    return values

def standalone(args: argparse.Namespace) -> None:
    root = args.root.resolve()
    values = read_env(root / '.env')
    token = values.get('KESTREL_ENGINE_TOKEN', '')
    if not token:
        raise RuntimeError('Set KESTREL_ENGINE_TOKEN in repository .env before starting the standalone engine')
    if args.host not in {'127.0.0.1', 'localhost', '::1'}:
        raise RuntimeError('Standalone engine must bind to a loopback address')
    if not 1 <= args.port <= 65535:
        raise RuntimeError('Standalone engine port must be between 1 and 65535')
    data_root = Path(values.get('KESTREL_DATA_DIR') or './data')
    if not data_root.is_absolute():
        data_root = root / data_root
    data_root = data_root.resolve()
    app = create_app(token, str(data_root))
    app.state.internal_token = token
    app.state.data_root = str(data_root)
    try:
        sock = socket.create_server((args.host, args.port), backlog=128)
    except OSError as exc:
        raise RuntimeError(f'Cannot bind engine at {args.host}:{args.port}; check whether that port is already in use') from exc
    print(f'Kestrel engine ready at http://{args.host}:{args.port} (loopback only)', flush=True)
    try:
        uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False)).run(sockets=[sock])
    finally:
        sock.close()

def main():
    parser = argparse.ArgumentParser(description='Kestrel local engine')
    parser.add_argument('--standalone', action='store_true', help='Run fixed-port local debug engine')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2], help='Repository root')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8081)
    args = parser.parse_args()
    if args.standalone:
        standalone(args)
        return
    config = json.loads(sys.stdin.readline())
    app = create_app(config['token'], config['data_root'])
    app.state.internal_token = config['token']
    app.state.data_root = config['data_root']
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    print(json.dumps({'port': sock.getsockname()[1]}), flush=True)
    uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False)).run(sockets=[sock])

if __name__ == '__main__':
    main()
