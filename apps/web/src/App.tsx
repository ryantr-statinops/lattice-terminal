import {useEffect,useState} from 'react';
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


export function App(){

 const client=useQueryClient();const status=useQuery({queryKey:['auth'],queryFn:()=>request<{initialized:boolean;authenticated:boolean}>('/auth/status'),refetchOnWindowFocus:true});
 const [password,setPassword]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 useEffect(()=>{const locked=()=>{client.clear();void client.fetchQuery({queryKey:['auth'],queryFn:()=>request('/auth/status')})};window.addEventListener('kestrel:locked',locked);return()=>window.removeEventListener('kestrel:locked',locked)},[client]);
 const login=async()=>{setBusy(true);setError('');try{if(!status.data?.initialized)await send('/auth/setup',{password});await send('/auth/login',{password});setPassword('');await client.invalidateQueries({queryKey:['auth']})}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 if(!status.data?.authenticated)return <main className="login"><form className="panel login-box" onSubmit={e=>{e.preventDefault();void login()}}><small>LOCAL RESEARCH TERMINAL</small><h1>Kestrel Terminal</h1><p>{status.data?.initialized?'Mở khóa phiên cục bộ':'Tạo mật khẩu local đầu tiên'}</p><label>Mật khẩu<input type="password" minLength={6} maxLength={1024} autoComplete={status.data?.initialized?'current-password':'new-password'} value={password} onChange={e=>setPassword(e.target.value)} required/></label><button disabled={busy||status.isPending||!!status.error}>{busy?'Đang xử lý…':status.data?.initialized?'Mở khóa':'Tạo profile'}</button>{(error||status.error)&&<p role="alert" className="error">{error||'Không kết nối được Go gateway. Hãy khởi chạy local services.'}</p>}<p className="muted">Mật khẩu khóa phiên. Dữ liệu trên đĩa chưa được mã hóa toàn bộ.</p></form></main>;
 return <AppShell onLock={async()=>{await send('/auth/lock',{});window.dispatchEvent(new Event('kestrel:locked'))}}><Routes><Route path="/" element={<Navigate to="/market" replace/>}/><Route path="/market" element={<Market/>}/><Route path="/quant" element={<Quant/>}/><Route path="/quant/research" element={<Workspace key="research" kind="research" title="Quant Research"/>}/><Route path="/settings" element={<Settings/>}/><Route path="/assets" element={<Assets/>}/><Route path="/backtest" element={<BacktestWorkspace/>}/><Route path="/strategies" element={<StrategiesWorkspace/>}/><Route path="/portfolio" element={<Portfolio/>}/><Route path="*" element={<Navigate to="/market" replace/>}/></Routes></AppShell>
}
