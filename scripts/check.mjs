import {execFileSync} from 'node:child_process';
import {existsSync} from 'node:fs';
for(const p of ['LICENSE','apps/web/index.html','services/engine/pyproject.toml','services/gateway/go.mod'])if(!existsSync(p))throw Error(`Missing foundation: ${p}`);
execFileSync('git',['diff','--check'],{stdio:'inherit'});
console.log('Foundation and whitespace checks passed');
