import {spawn, spawnSync} from 'node:child_process';
import {existsSync, mkdirSync, createWriteStream} from 'node:fs';
import {delimiter, dirname, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import net from 'node:net';
import {setTimeout as delay} from 'node:timers/promises';

export const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

export function findOmp(env = process.env, platform = process.platform) {
  for (const folder of (env.PATH ?? env.Path ?? '').split(delimiter)) {
    const candidate = resolve(folder.replace(/^"|"$/g, ''), platform === 'win32' ? 'omp.ps1' : 'omp');
    if (existsSync(candidate)) return platform === 'win32'
      ? {command: 'powershell.exe', args: ['-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', candidate]}
      : {command: candidate, args: []};
  }
  throw new Error('OMP not found on PATH. Install OMP, then restart your terminal.');
}

export async function assertPortFree(port) {
  await new Promise((ok, fail) => {
    const server = net.createServer();
    server.once('error', () => fail(new Error(`Port ${port} is occupied. Stop its owner yourself before dev:ai.`)));
    server.listen({port, host: 'localhost', exclusive: true}, () => server.close(ok));
  });
  // Vite binds IPv4 explicitly; check it too on dual-stack hosts.
  await new Promise((ok, fail) => {
    const server = net.createServer();
    server.once('error', () => fail(new Error(`Port ${port} on 127.0.0.1 is occupied.`)));
    server.listen({port, host: '127.0.0.1', exclusive: true}, () => server.close(ok));
  });
}

export async function waitReady(url, child, timeoutMs = 30000, signal) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (signal?.aborted) return;
    if (child.exitCode !== null || child.signalCode !== null) throw new Error('Vite exited before becoming ready.');
    try { if ((await fetch(url, {signal: AbortSignal.timeout(500)})).ok) return; } catch { /* retry until deadline */ }
    await delay(100);
  }
  throw new Error(`Vite readiness timed out after ${timeoutMs}ms.`);
}

export async function stopTree(child) {
  if (!child?.pid) return;
  if (process.platform === 'win32') {
    await new Promise(resolveStop => {
      const killer = spawn('taskkill.exe', ['/PID', String(child.pid), '/T', '/F'], {windowsHide: true, stdio: 'ignore'});
      killer.once('error', resolveStop);
      killer.once('exit', resolveStop);
    });
  } else {
    try { process.kill(-child.pid, 'SIGTERM'); } catch { return; }
    await delay(300);
    try { process.kill(-child.pid, 'SIGKILL'); } catch { /* already stopped */ }
  }
}

// Command injection points allow lifecycle tests without launching the user's OMP.
export async function runSession({cwd = root, vite, omp, url = 'http://127.0.0.1:5173', timeoutMs = 30000, logPath = resolve(cwd, '.cache/dev-ai/vite.log')} = {}) {
  mkdirSync(dirname(logPath), {recursive: true});
  const log = createWriteStream(logPath, {flags: 'a'});
  const children = [];
  const readiness = new AbortController();
  let finish;
  const ended = new Promise(resolveEnd => { finish = resolveEnd; });
  const launch = (spec, stdio) => {
    const child = spawn(spec.command, spec.args, {cwd, env: {...process.env, VITE_ENABLE_AGENTATION: 'true'}, stdio, detached: process.platform !== 'win32', windowsHide: true});
    children.push(child);
    child.once('error', error => finish({error}));
    return child;
  };
  const interrupt = () => finish({code: 130});
  process.once('SIGINT', interrupt);
  process.once('SIGTERM', interrupt);
  try {
    const web = launch(vite, ['ignore', 'pipe', 'pipe']);
    web.stdout.pipe(log, {end: false}); web.stderr.pipe(log, {end: false});
    web.once('exit', () => finish({error: new Error(`Vite exited. See ${logPath}`)}));
    const ready = await Promise.race([waitReady(url, web, timeoutMs, readiness.signal).then(() => ({ready: true})), ended]);
    if (!ready.ready) { if (ready.error) throw ready.error; return ready.code; }
    console.log(`Vite: ${url} | log: ${logPath}\nStarting OMP; it owns the three MCP servers.`);
    const agent = launch(omp, 'inherit');
    agent.once('exit', (code, signal) => finish({code: code ?? (signal ? 130 : 1)}));
    const result = await ended;
    if (result.error) throw result.error;
    return result.code;
  } finally {
    readiness.abort();
    process.removeListener('SIGINT', interrupt); process.removeListener('SIGTERM', interrupt);
    for (const child of children.reverse()) await stopTree(child);
    log.end();
  }
}

export async function main() {
  const omp = findOmp();
  const probe = spawnSync(omp.command, [...omp.args, '--version'], {cwd: root, encoding: 'utf8', timeout: 10000, windowsHide: true});
  if (probe.error || probe.status !== 0) throw new Error(`OMP installation is not runnable. Check omp --version before retrying. ${probe.error?.message ?? probe.stderr?.trim() ?? ''}`);
  for (const entry of ['vite/bin/vite.js', 'agentation-mcp/dist/cli.js', '@upstash/context7-mcp/dist/index.js', 'chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js']) {
    if (!existsSync(resolve(root, 'node_modules', entry))) throw new Error(`Missing ${entry}. Run npm ci first.`);
  }
  await assertPortFree(5173); await assertPortFree(4747);
  return runSession({vite: {command: process.execPath, args: [resolve(root, 'node_modules/vite/bin/vite.js'), resolve(root, 'apps/web')]}, omp});
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().then(code => { process.exitCode = code; }).catch(error => { console.error(`dev:ai: ${error.message}`); process.exitCode = 1; });
}
