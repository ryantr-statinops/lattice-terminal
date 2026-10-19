"""Boot configuration travels over stdin, never command-line secrets."""
import json
import socket
import sys
import uvicorn
from .app import create_app

def main():
    config = json.loads(sys.stdin.readline())
    app = create_app()
    app.state.internal_token = config['token']
    app.state.data_root = config['data_root']
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    sock.listen(128)
    print(json.dumps({'port': sock.getsockname()[1]}), flush=True)
    uvicorn.Server(uvicorn.Config(app, log_level='warning', access_log=False)).run(sockets=[sock])

if __name__ == '__main__':
    main()
