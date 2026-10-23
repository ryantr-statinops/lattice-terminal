import {test} from 'node:test';
import assert from 'node:assert/strict';
import net from 'node:net';
import {mkdtempSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {assertPortFree, findOmp, runSession} from './dev-ai.mjs';

test('missing OMP fails without launching anything', () => {
  assert.throws(() => findOmp({PATH: join(tmpdir(), 'no-omp-here')}), /OMP not found/);
});

test('occupied port is reported and its owner is preserved', async () => {
  const server = net.createServer();
  await new Promise(ok => server.listen(0, '127.0.0.1', ok));
  try { await assert.rejects(assertPortFree(server.address().port), /occupied/); assert.equal(server.listening, true); }
  finally { await new Promise(ok => server.close(ok)); }
});

const node = code => ({command: process.execPath, args: ['-e', code]});
async function fixture(run) {
  const cwd = mkdtempSync(join(tmpdir(), 'lattice dev ai '));
  try { await run(cwd); } finally { rmSync(cwd, {recursive: true, force: true}); }
}
async function freePort() {
  const server = net.createServer();
  await new Promise(ok => server.listen(0, '127.0.0.1', ok));
  const port = server.address().port;
  await new Promise(ok => server.close(ok));
  return port;
}

test('OMP exit stops Vite and releases its port (paths with spaces)', async () => fixture(async cwd => {
  const port = await freePort();
  const code = await runSession({cwd, url: `http://127.0.0.1:${port}`, vite: node(`require('http').createServer((q,s)=>s.end(process.env.VITE_ENABLE_AGENTATION)).listen(${port},'127.0.0.1')`), omp: node('process.exit(7)')});
  assert.equal(code, 7);
  await assertPortFree(port);
}));

test('timeout stops an unready Vite process', async () => fixture(async cwd => {
  await assert.rejects(runSession({cwd, url: 'http://127.0.0.1:1', timeoutMs: 150, vite: node('setInterval(()=>{},1000)'), omp: node('process.exit(0)')}), /timed out/);
}));

test('Vite failure prevents OMP launch', async () => fixture(async cwd => {
  await assert.rejects(runSession({cwd, vite: node('process.exit(1)'), omp: node('process.exit(0)')}), /Vite exited/);
}));

test('Ctrl+C handler cleans up while waiting for Vite', async () => fixture(async cwd => {
  const timer = setTimeout(() => process.emit('SIGINT'), 150);
  try {
    const code = await runSession({cwd, url: 'http://127.0.0.1:1', vite: node('setInterval(()=>{},1000)'), omp: node('process.exit(0)')});
    assert.equal(code, 130);
  } finally { clearTimeout(timer); }
}));
