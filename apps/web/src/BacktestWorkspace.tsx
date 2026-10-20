import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
import {Workspace} from './Workspace';
import {RunComparison} from './RunComparison';
import {Panel,PanelHeader} from './ui/layout';
import {Field,Select,TextInput} from './ui/fields';
import {ErrorState,LoadingState} from './ui/feedback';
type Tape={snapshot_id:string;source_id:string;granularity:string;event_count:number;start:string;end:string};
type Train={id:string;status:string;file:string;params:Record<string,unknown>};
const dateLabels={train_start:'Train start',train_end:'Train end',test_start:'Test start',test_end:'Test end'};
export function BacktestWorkspace(){
 const tapes=useQuery({queryKey:['detailed-tapes'],queryFn:()=>request<Tape[]>('/engine/backtest/data')});
 const runs=useQuery({queryKey:['runs','backtest'],queryFn:()=>request<Train[]>('/runs?kind=backtest'),refetchInterval:3000});
 const [tape,setTape]=useState(''),[capital,setCapital]=useState('100000000'),[stage,setStage]=useState('train'),[train,setTrain]=useState('');
 const [dates,setDates]=useState({train_start:'2026-10-01T00:00',train_end:'2026-10-01T23:59',test_start:'2026-10-02T00:00',test_end:'2026-10-02T23:59'});
 const iso=(value:string)=>{const parsed=new Date(value+'Z');return value&&!Number.isNaN(parsed.getTime())?parsed.toISOString():''};
 const selectedTrain=runs.data?.find(v=>v.id===train&&v.status==='completed'&&v.params.stage==='train');
 const params={...(stage==='test'&&selectedTrain?selectedTrain.params:{}),...Object.fromEntries(Object.entries(dates).map(([key,value])=>[key,iso(value)])),capital,stage,train_run_id:stage==='test'?train||null:null,event_snapshot:tape||tapes.data?.[0]?.snapshot_id||''};
 const validCapital=/^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(capital)&&!/^0(?:\.0+)?$/.test(capital);
 const dateError=Object.values(dates).some(value=>!iso(value))?'Enter all valid date and time values.':dates.train_start>=dates.train_end||dates.test_start>=dates.test_end?'Each start time must be before its end time.':dates.train_end>=dates.test_start?'The Train period must end before Test begins.':'';
 const blocked=tapes.isPending||runs.isPending?'Loading configuration…':tapes.error||runs.error?'Could not load data or configuration.':!params.event_snapshot?'No detailed data snapshot is available.':!validCapital?'Enter a positive VND capital amount.':dateError?dateError:stage==='test'&&!selectedTrain?'Select a completed Train run.':'';
 const choose=(id:string)=>{setTrain(id);const selected=runs.data?.find(v=>v.id===id);if(selected){setCapital(String(selected.params.capital));setTape(String(selected.params.event_snapshot));setDates(Object.fromEntries(Object.keys(dates).map(key=>[key,String(selected.params[key]).slice(0,16)])) as typeof dates)}};
 const frozen=stage==='test';
 const controls=<Panel><PanelHeader title="TRAIN / TEST CONFIGURATION"/><div className="panel-content"><p className="muted">Backtests use detailed quote events and do not infer fills from daily candles. Current data is synthetic; production use is blocked.</p>{(tapes.isPending||runs.isPending)&&<LoadingState>Loading snapshots and Train history…</LoadingState>}<ErrorState error={tapes.error||runs.error}/><div className="form-grid"><Field label="Detailed data snapshot"><Select value={params.event_snapshot} disabled={frozen||!tapes.data?.length} onChange={e=>setTape(e.target.value)}>{tapes.data?.map(v=><option key={v.snapshot_id} value={v.snapshot_id}>{v.source_id} · {v.event_count} {v.granularity}</option>)}</Select></Field><Field label="Capital · VND" error={!validCapital?'Enter a positive number using a decimal point.':undefined}><TextInput disabled={frozen} value={capital} inputMode="decimal" onChange={e=>setCapital(e.target.value)}/></Field><Field label="Train or Test"><Select value={stage} onChange={e=>setStage(e.target.value)}><option value="train">Train — research</option><option value="test">Test — frozen configuration</option></Select></Field>{frozen&&<Field label="Frozen Train run"><Select value={train} onChange={e=>choose(e.target.value)}><option value="">Select a completed Train run</option>{runs.data?.filter(v=>v.status==='completed'&&v.params.stage==='train').map(v=><option key={v.id} value={v.id}>{v.file} · {v.id.slice(0,8)}</option>)}</Select></Field>}{Object.entries(dates).map(([key,value])=><Field key={key} label={dateLabels[key as keyof typeof dates]+' · UTC'}><TextInput disabled={frozen} type="datetime-local" value={value} onChange={e=>setDates({...dates,[key]:e.target.value})}/></Field>)}</div>{dateError&&<p className="error">{dateError}</p>}<p className="muted">Test preserves the selected Train parameters. The backend still validates code, helpers, and data; code changes require a new Train run.</p></div></Panel>;
 return <Workspace kind="backtest" title="Backtest" controls={<>{controls}<RunComparison runs={runs.data??[]}/></>} extraParams={params} runBlockedReason={blocked}/>;
}
