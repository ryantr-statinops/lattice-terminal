import {useEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
import {Appearance} from './appearance/Appearance';
import {PageHeader,Panel,PanelHeader} from './ui/layout';
import {DataTable,StatusLabel} from './ui/data';
import {ErrorState,LoadingState} from './ui/feedback';
type Source={id:string;documented:boolean;access_tested:boolean;rights_confirmed:boolean;approved:boolean;operating_state:string;reason:string};
export function Settings(){
 const query=useQuery({queryKey:['sources'],queryFn:()=>request<Source[]>('/engine/sources')});const {hash}=useLocation();
 useEffect(()=>{if(hash==='#appearance')document.getElementById('appearance')?.scrollIntoView({block:'start'})},[hash]);
 const local=useQuery({queryKey:['local-config'],queryFn:()=>request<{data_dir:string;account_source:string}>('/local/config')});
 return <section><PageHeader eyebrow="SETTINGS / LOCAL PROFILE" title="Settings"/><Appearance/><Panel><PanelHeader title="DATA SOURCES"/><div className="panel-content"><p className="muted">Configure credentials only through the CLI and Windows Credential Manager. Do not enter SSI secrets in the browser.</p>{query.isPending&&<LoadingState>Loading source evidence…</LoadingState>}<ErrorState error={query.error} onRetry={()=>void query.refetch()}/></div><DataTable loading={query.isPending} caption="Source evidence — each flag is independent" rows={query.data??[]} rowKey={v=>v.id} columns={[{key:'id',label:'Capability',render:v=>v.id},...(['documented','access_tested','rights_confirmed','approved'] as const).map(key=>({key,label:key,render:(v:Source)=><StatusLabel tone={v[key]?'positive':'warning'}>{v[key]?'yes':'pending'}</StatusLabel>})),{key:'state',label:'Mode',render:v=>v.operating_state},{key:'reason',label:'Reason',render:v=>v.reason}]}/></Panel><Panel><PanelHeader title="LOCAL PROFILE"/><div className="panel-content"><p>A single local account is loaded from .env at startup.</p><p className="muted">Data directory: <code>{local.data?.data_dir??'Loading…'}</code></p><p>Edit the username/password in the project .env file, then restart the Compose stack to apply the changes.</p><pre>go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials set<br/>go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials status</pre><p className="muted">The CLI only shows instructions for editing the account in .env; SSI credentials remain in Windows Credential Manager.</p></div></Panel></section>;
}
