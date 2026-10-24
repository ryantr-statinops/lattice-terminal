import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
import {Toolbar} from './ui/layout';
import {Field,Select} from './ui/fields';
import {DataTable} from './ui/data';
import {ErrorState,LoadingState} from './ui/feedback';
type Report={run:{id:string;snapshot:string;params:Record<string,unknown>};report:Record<string,unknown>};
export function RunComparison({runs}:{runs:{id:string;file:string;status:string}[]}){
 const [left,setLeft]=useState(''),[right,setRight]=useState('');
 const a=useQuery({queryKey:['report',left],queryFn:()=>request<Report>(`/runs/${encodeURIComponent(left)}/report`),enabled:!!left});
 const b=useQuery({queryKey:['report',right],queryFn:()=>request<Report>(`/runs/${encodeURIComponent(right)}/report`),enabled:!!right});
 const cell=(value:unknown)=>value===null||value===undefined?'Unavailable':String(value);
 const rows=['stage','capital','final_nav','net_profit','max_drawdown','simulated_fill_count','sharpe','sharpe_reason','rule_pack','event_snapshot','Code snapshot'];
 const value=(report:Report|undefined,key:string)=>key==='Code snapshot'?report?.run.snapshot.slice(0,16):report?.report[key];
 return <details className="panel"><summary>Compare Backtest runs</summary><div className="panel-content"><Toolbar>{([['A',left,setLeft],['B',right,setRight]] as const).map(([label,id,set])=><Field key={label} label={'Compare run '+label}><Select value={id} onChange={e=>set(e.target.value)}><option value="">Select a completed Backtest</option>{runs.filter(v=>v.status==='completed').map(v=><option key={v.id} value={v.id}>{v.file} · {v.id.slice(0,8)}</option>)}</Select></Field>)}</Toolbar>{(a.isFetching||b.isFetching)&&<LoadingState>Loading report…</LoadingState>}<ErrorState error={a.error||b.error}/>{(a.data||b.data)&&<DataTable caption="Metrics and provenance" rows={rows} rowKey={key=>key} columns={[{key:'metric',label:'Metric / provenance',render:key=>key},{key:'a',label:'A',render:key=>cell(value(a.data,key))},{key:'b',label:'B',render:key=>cell(value(b.data,key))}]}/>}</div></details>;
}
