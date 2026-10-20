import {useEffect} from 'react';
import {Navigate,Route,Routes} from 'react-router-dom';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send} from './api';
import {Market} from './Market';
import {Quant} from './Quant';
import {Settings} from './Settings';
import {Workspace} from './Workspace';
import {BacktestWorkspace} from './BacktestWorkspace';
import {StrategiesWorkspace} from './StrategiesWorkspace';
import {Assets} from './Assets';
import {Portfolio} from './Portfolio';
import {AppShell} from './ui/AppShell';
import {Login} from './ui/Login';


export function App(){

 const client=useQueryClient();const status=useQuery({queryKey:['auth'],queryFn:()=>request<{initialized:boolean;authenticated:boolean}>('/auth/status'),refetchOnWindowFocus:true});
 useEffect(()=>{const locked=()=>{client.clear();void client.fetchQuery({queryKey:['auth'],queryFn:()=>request('/auth/status')})};window.addEventListener('kestrel:locked',locked);return()=>window.removeEventListener('kestrel:locked',locked)},[client]);
 if(!status.data?.authenticated)return <Login initialized={status.data?.initialized} loading={status.isPending} error={status.error} onRetry={()=>void status.refetch()} onSubmit={async password=>{if(!status.data?.initialized)await send('/auth/setup',{password});await send('/auth/login',{password});await client.invalidateQueries({queryKey:['auth']})}}/>;
 return <AppShell onLock={async()=>{await send('/auth/lock',{});window.dispatchEvent(new Event('kestrel:locked'))}}><Routes><Route path="/" element={<Navigate to="/market" replace/>}/><Route path="/market" element={<Market/>}/><Route path="/quant" element={<Quant/>}/><Route path="/quant/research" element={<Workspace key="research" kind="research" title="Quant Research"/>}/><Route path="/settings" element={<Settings/>}/><Route path="/assets" element={<Assets/>}/><Route path="/backtest" element={<BacktestWorkspace/>}/><Route path="/strategies" element={<StrategiesWorkspace/>}/><Route path="/portfolio" element={<Portfolio/>}/><Route path="*" element={<Navigate to="/market" replace/>}/></Routes></AppShell>
}
