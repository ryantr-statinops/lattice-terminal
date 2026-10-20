import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
type Report={run:{id:string;snapshot:string;params:Record<string,unknown>};report:Record<string,unknown>};
export function RunComparison({runs}:{runs:{id:string;file:string;status:string}[]}){
 const [left,setLeft]=useState(''),[right,setRight]=useState('');
 const a=useQuery({queryKey:['report',left],queryFn:()=>request<Report>(`/runs/${left}/report`),enabled:!!left});
 const b=useQuery({queryKey:['report',right],queryFn:()=>request<Report>(`/runs/${right}/report`),enabled:!!right});
 const cell=(value:unknown)=>value===null||value===undefined?'Unavailable':String(value);
 return <details className="panel" style={{padding:16}}><summary>So sánh báo cáo Backtest / Compare runs</summary><p className="muted">Kết quả mô phỏng synthetic, không cam kết lợi nhuận. Khác code/data/config có thể làm báo cáo không tương đương.</p><div className="toolbar">{([['A',left,setLeft],['B',right,setRight]] as const).map(([label,id,set])=><label key={label}>Run {label}<select aria-label={'Compare run '+label} value={id} onChange={e=>set(e.target.value)}><option value="">Chọn completed Backtest</option>{runs.filter(v=>v.status==='completed').map(v=><option key={v.id} value={v.id}>{v.file} · {v.id.slice(0,8)}</option>)}</select></label>)}</div>{(a.error||b.error)&&<p className="error" role="alert">{a.error?.message||b.error?.message}</p>}{(a.data||b.data)&&<table><thead><tr><th>Metric / provenance</th><th>A</th><th>B</th></tr></thead><tbody>{['stage','capital','final_nav','net_profit','max_drawdown','simulated_fill_count','sharpe','sharpe_reason','rule_pack','event_snapshot'].map(key=><tr key={key}><td>{key}</td><td>{cell(a.data?.report[key])}</td><td>{cell(b.data?.report[key])}</td></tr>)}<tr><td>Code snapshot</td><td>{a.data?.run.snapshot.slice(0,16)||'Unavailable'}</td><td>{b.data?.run.snapshot.slice(0,16)||'Unavailable'}</td></tr></tbody></table>}</details>
}
