import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {request} from './api';
import {Workspace} from './Workspace';
import {Panel,PanelHeader} from './ui/layout';
import {Field,Select} from './ui/fields';
import {StatusLabel} from './ui/data';
import {ErrorState,LoadingState} from './ui/feedback';
type Allocation={id:string;name:string;mode:string;cash:string;status:string};
type Tape={snapshot_id:string;source_id:string;event_count:number};
export function StrategiesWorkspace(){
 const allocations=useQuery({queryKey:['allocations'],queryFn:()=>request<Allocation[]>('/allocations'),refetchInterval:3000});
 const tapes=useQuery({queryKey:['detailed-tapes'],queryFn:()=>request<Tape[]>('/engine/backtest/data')});
 const [id,setID]=useState(''),[source,setSource]=useState('ssi-live'),[tape,setTape]=useState('');
 const allocation=allocations.data?.find(v=>v.id===id&&v.mode==='strategy');const snapshot=tape||tapes.data?.[0]?.snapshot_id||'';
 const blocked=allocations.isPending||tapes.isPending?'Loading configuration…':allocations.error||tapes.error?'Could not load allocations or snapshots.':source!=='fixture-replay'?'SSI live trading is blocked. Explicitly select Synthetic fixture replay to test.':!allocation?'Select a Strategy allocation in Assets.':allocation.status!=='stopped'?'The allocation must be stopped.':!snapshot?'No fixture event tape is available.':'';
 const controls=<Panel><PanelHeader title="STRATEGY / PAPER CONFIGURATION" actions={<StatusLabel tone="warning">SSI LIVE BLOCKED</StatusLabel>}/><div className="panel-content"><p>Python strategy callbacks for Paper. Backtest files are not accepted here.</p>{(allocations.isPending||tapes.isPending)&&<LoadingState>Loading allocations and data…</LoadingState>}<ErrorState error={allocations.error||tapes.error}/><div className="form-grid"><Field label="Strategy allocation"><Select value={id} onChange={e=>setID(e.target.value)}><option value="">Select an allocation from Assets</option>{allocations.data?.filter(v=>v.mode==='strategy').map(v=><option key={v.id} value={v.id} disabled={v.status!=='stopped'}>{v.name} · {v.cash} VND · {v.status}</option>)}</Select></Field><Field label="Paper source"><Select value={source} onChange={e=>setSource(e.target.value)}><option value="ssi-live">SSI live — blocked</option><option value="fixture-replay">Synthetic fixture replay — not real time</option></Select></Field>{source==='fixture-replay'&&<Field label="Fixture event tape"><Select value={snapshot} onChange={e=>setTape(e.target.value)}>{tapes.data?.map(v=><option key={v.snapshot_id} value={v.snapshot_id}>{v.source_id} · {v.event_count} events</option>)}</Select></Field>}</div><Link to="/assets">Manage funds →</Link><p className="muted">Capital comes from the selected allocation; the backend validates it and keeps control isolated. Stopping preserves positions and committed capital. Fixture replay does not prove SSI live trading works.</p></div></Panel>;
 return <Workspace kind="strategy" title="Strategies" controls={controls} extraParams={{allocation_id:id,paper_source:source,event_snapshot:snapshot}} runBlockedReason={blocked}/>;
}
