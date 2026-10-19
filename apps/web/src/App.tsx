import {useEffect,useState} from 'react';
import {NavLink,Navigate,Route,Routes} from 'react-router-dom';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send} from './api';
import {Market} from './Market';
import {Quant} from './Quant';
import {Settings} from './Settings';
import {Workspace} from './Workspace';
import {BacktestWorkspace} from './BacktestWorkspace';
import {StrategiesWorkspace} from './StrategiesWorkspace';
import {Assets} from './Assets';

const navigation=[['/market','Market'],['/quant','Quant'],['/backtest','Backtest'],['/strategies','Strategies'],['/assets','Assets / Quỹ'],['/portfolio','Portfolio'],['/settings','Settings']];
function Pending({name}:{name:string}){return <section><h1>{name}</h1><p className="muted">Đang triển khai trong milestone riêng. Chưa có capability vận hành ở màn hình này.</p></section>}
export function App(){
 const client=useQueryClient();const status=useQuery({queryKey:['auth'],queryFn:()=>request<{initialized:boolean;authenticated:boolean}>('/auth/status'),refetchOnWindowFocus:true});
 const [password,setPassword]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 useEffect(()=>{const locked=()=>{client.clear();void client.fetchQuery({queryKey:['auth'],queryFn:()=>request('/auth/status')})};window.addEventListener('kestrel:locked',locked);return()=>window.removeEventListener('kestrel:locked',locked)},[client]);
 const login=async()=>{setBusy(true);setError('');try{if(!status.data?.initialized)await send('/auth/setup',{password});await send('/auth/login',{password});setPassword('');await client.invalidateQueries({queryKey:['auth']})}catch(e){setError((e as Error).message)}finally{setBusy(false)}};
 if(!status.data?.authenticated)return <main className="login"><form className="panel login-box" onSubmit={e=>{e.preventDefault();void login()}}><small>LOCAL RESEARCH TERMINAL</small><h1>Kestrel Terminal</h1><p>{status.data?.initialized?'Mở khóa phiên cục bộ':'Tạo mật khẩu local đầu tiên'}</p><label>Mật khẩu<input type="password" minLength={12} maxLength={1024} autoComplete={status.data?.initialized?'current-password':'new-password'} value={password} onChange={e=>setPassword(e.target.value)} required/></label><button disabled={busy||status.isPending||!!status.error}>{busy?'Đang xử lý…':status.data?.initialized?'Mở khóa':'Tạo profile'}</button>{(error||status.error)&&<p role="alert" className="error">{error||'Không kết nối được Go gateway. Hãy khởi chạy local services.'}</p>}<p className="muted">Mật khẩu khóa phiên. Dữ liệu trên đĩa chưa được mã hóa toàn bộ.</p></form></main>;
 return <div className="app-shell"><aside className="app-nav"><div className="wordmark">K<span>KESTREL<small>TERMINAL</small></span></div><nav>{navigation.map(([to,label])=><NavLink key={to} to={to}>{label}</NavLink>)}</nav><div className="nav-bottom"><span className="badge">LOCAL · FIXTURE</span><button onClick={async()=>{await send('/auth/lock',{});window.dispatchEvent(new Event('kestrel:locked'))}}>Khóa phiên</button></div></aside><div className="app-body"><header><span>Research workspace</span><span className="muted">SSI production blocked · VND</span></header><main><Routes><Route path="/" element={<Navigate to="/market" replace/>}/><Route path="/market" element={<Market/>}/><Route path="/quant" element={<Quant/>}/><Route path="/quant/research" element={<Workspace key="research" kind="research" title="Quant Research"/>}/><Route path="/settings" element={<Settings/>}/><Route path="/assets" element={<Assets/>}/><Route path="/backtest" element={<BacktestWorkspace/>}/><Route path="/strategies" element={<StrategiesWorkspace/>}/>{navigation.slice(5,6).map(([path,name])=><Route key={path} path={path} element={<Pending name={name}/>}/>)}<Route path="*" element={<Navigate to="/market" replace/>}/></Routes></main></div></div>
}
