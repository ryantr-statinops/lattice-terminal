import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
import {Workspace} from './Workspace';
type Tape={snapshot_id:string;source_id:string;granularity:string;event_count:number;start:string;end:string};
type Train={id:string;status:string;file:string;params:Record<string,unknown>};
export function BacktestWorkspace(){
 const tapes=useQuery({queryKey:['detailed-tapes'],queryFn:()=>request<Tape[]>('/engine/backtest/data')});
 const runs=useQuery({queryKey:['runs','backtest'],queryFn:()=>request<Train[]>('/runs?kind=backtest'),refetchInterval:3000});
 const [tape,setTape]=useState('');const [capital,setCapital]=useState('100000000');const [stage,setStage]=useState('train');const [train,setTrain]=useState('');
 const [dates,setDates]=useState({train_start:'2026-10-01T00:00',train_end:'2026-10-01T23:59',test_start:'2026-10-02T00:00',test_end:'2026-10-02T23:59'});
 const params={...Object.fromEntries(Object.entries(dates).map(([key,value])=>[key,value?new Date(value+'Z').toISOString():''])),capital,stage,train_run_id:train||null,event_snapshot:tape||tapes.data?.[0]?.snapshot_id||''};
 const choose=(id:string)=>{setTrain(id);const selected=runs.data?.find(v=>v.id===id);if(selected){setCapital(String(selected.params.capital));setTape(String(selected.params.event_snapshot));setDates(Object.fromEntries(Object.keys(dates).map(key=>[key,String(selected.params[key]).slice(0,16)])) as typeof dates)}};
 const controls=<div className="panel" style={{padding:16}}><p className="muted">Backtest dùng quote-events chi tiết, không dùng nến daily để giả định fill. Dữ liệu hiện là synthetic; production blocked.</p><div className="toolbar"><select aria-label="Detailed data snapshot" value={params.event_snapshot} onChange={e=>setTape(e.target.value)}>{tapes.data?.map(v=><option key={v.snapshot_id} value={v.snapshot_id}>{v.source_id} · {v.event_count} {v.granularity}</option>)}</select><label>Vốn VND <input aria-label="Backtest capital" value={capital} onChange={e=>setCapital(e.target.value)}/></label><select aria-label="Train or Test" value={stage} onChange={e=>setStage(e.target.value)}><option value="train">Train — nghiên cứu</option><option value="test">Test — config đóng băng</option></select>{stage==='test'&&<select aria-label="Frozen Train run" value={train} onChange={e=>choose(e.target.value)}><option value="">Chọn Train đã hoàn thành</option>{runs.data?.filter(v=>v.status==='completed'&&v.params.stage==='train').map(v=><option key={v.id} value={v.id}>{v.file} · {v.id.slice(0,8)}</option>)}</select>}</div><div className="toolbar">{Object.entries(dates).map(([key,value])=><label className="muted" key={key}>{key} UTC <input type="datetime-local" value={value} onChange={e=>setDates({...dates,[key]:e.target.value})}/></label>)}</div><p className="muted">Test yêu cầu giữ nguyên code, helpers, dữ liệu và tham số của Train đã chọn; sửa code cần Train mới.</p>{tapes.error&&<p className="error">{tapes.error.message}</p>}</div>;
 return <Workspace kind="backtest" title="Backtest" controls={controls} extraParams={params}/>;
}
