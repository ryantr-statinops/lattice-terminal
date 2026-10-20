import {readFileSync,writeFileSync,readdirSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
const update=process.argv.includes('--write');
const files=[];function walk(dir){for(const item of readdirSync(dir,{withFileTypes:true})){const p=join(dir,item.name);if(item.isDirectory())walk(p);else if(p.endsWith('.go')&&!p.endsWith('_test.go'))files.push(p)}}walk('services/gateway/internal/api');files.push('services/gateway/cmd/kestrel/main.go','services/gateway/internal/auth/auth.go');
const routes=[...new Set(files.flatMap(p=>[...readFileSync(p,'utf8').matchAll(/\.HandleFunc\("((?:GET|POST|PUT|DELETE) \/api\/v1\/[^"\n]+)"/g)].map(m=>m[1])))].sort();
const outputs={'contracts/gateway-routes.json':JSON.stringify({version:1,routes,engine_proxy:'Whitelisted market/quant/source/data GETs and program inspection POST only; see cmd/kestrel/main.go.'},null,2)+'\n'};
const go=process.env.KESTREL_GO||(existsSync('.cache/toolchains/go/bin/go.exe')?join(process.cwd(),'.cache/toolchains/go/bin/go.exe'):'go');
outputs['contracts/gateway.schema.json']=execFileSync(go,['-C','services/gateway','run','./cmd/contracts'],{encoding:'utf8'}).replaceAll('\r\n','\n');
for(const [path,text] of Object.entries(outputs)){if(update)writeFileSync(path,text);else if(!existsSync(path)||readFileSync(path,'utf8').replaceAll('\r\n','\n')!==text)throw Error(`Contract drift: ${path}; run node scripts/contracts.mjs --write`)}
console.log(`${update?'Wrote':'Checked'} gateway response schemas and ${routes.length} routes`);
