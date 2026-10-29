import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {request,type Instrument} from './api';
import {Plot} from './Plot';
import {PageHeader,Panel,Toolbar} from './ui/layout';
import {Field,Select,TextInput} from './ui/fields';
import {DataTable,SourceMetadata,StatusLabel} from './ui/data';
import {EmptyState,ErrorState,LoadingState} from './ui/feedback';
type Result={indicator:string;times:string[];series:{name:string;values:(number|null)[]}[];warnings:string[];snapshot_id:string;quality:{state:string;gaps:string[]}};
type Snapshot={snapshot_id:string;instrument:{id:string;native_symbol:string;venue:string|null};source_id:string;quality:{state:string}};
export function Quant(){
 const instruments=useQuery({queryKey:['instruments'],queryFn:()=>request<Instrument[]>('/engine/market/instruments')});
 const snapshots=useQuery({queryKey:['market-snapshots'],queryFn:()=>request<Snapshot[]>('/engine/market/snapshots')});
 const catalog=useQuery({queryKey:['indicator-catalog'],queryFn:()=>request<string[]>('/engine/quant/indicators')});
 const [selected,setSelected]=useState(''),[selectedSnapshot,setSelectedSnapshot]=useState(''),[indicator,setIndicator]=useState('sma'),[period,setPeriod]=useState(14),[benchmark,setBenchmark]=useState('');
 const id=selected||instruments.data?.[0]?.id||'';const valid=Number.isInteger(period)&&period>=2&&period<=1000;
 const options=snapshots.data?.filter(v=>v.instrument.id===id)||[];const snapshotID=options.some(v=>v.snapshot_id===selectedSnapshot)?selectedSnapshot:options[0]?.snapshot_id||'';
 const query=useQuery({queryKey:['quant',id,snapshotID,indicator,period,benchmark],enabled:!!id&&!!snapshotID&&valid&&!catalog.error&&!!catalog.data?.includes(indicator),queryFn:()=>request<Result>(`/engine/quant/calculate?instrument_id=${encodeURIComponent(id)}&snapshot_id=${encodeURIComponent(snapshotID)}&indicator=${encodeURIComponent(indicator)}&period=${period}${benchmark?'&benchmark_id='+encodeURIComponent(benchmark):''}`)});
 return <section><PageHeader title="Quant Indicators" actions={<StatusLabel tone="warning">FIXTURE</StatusLabel>}/><Link to="/quant/research">Open Python Research Editor →</Link><Toolbar><Field label="Instrument"><Select value={id} disabled={!instruments.data?.length} onChange={e=>{setSelected(e.target.value);setSelectedSnapshot('')}}>{instruments.data?.map(v=><option key={v.id} value={v.id}>{v.native_symbol} · {v.venue}</option>)}</Select></Field><Field label="Dataset snapshot"><Select value={snapshotID} disabled={!options.length} onChange={e=>setSelectedSnapshot(e.target.value)}>{options.map(v=><option key={v.snapshot_id} value={v.snapshot_id}>{v.source_id} · {v.quality.state} · {v.snapshot_id.slice(0,12)}</option>)}</Select></Field><Field label="Indicator"><Select value={indicator} disabled={!catalog.data?.length} onChange={e=>setIndicator(e.target.value)}>{catalog.data?.map(v=><option key={v}>{v}</option>)}</Select></Field><Field label="Period (2–1000)" error={!valid?'Enter an integer from 2 to 1,000.':undefined}><TextInput type="number" min={2} max={1000} value={period||''} onChange={e=>setPeriod(Number(e.target.value))}/></Field><Field label="Benchmark"><Select value={benchmark} onChange={e=>setBenchmark(e.target.value)}><option value="">No benchmark selected</option>{instruments.data?.map(v=><option key={v.id} value={v.id}>{v.native_symbol}</option>)}</Select></Field></Toolbar>
 {(instruments.isPending||snapshots.isPending||catalog.isPending||query.isFetching)&&<LoadingState>Loading data and calculating indicator…</LoadingState>}<ErrorState error={instruments.error||snapshots.error||catalog.error||query.error} onRetry={()=>{void instruments.refetch();void snapshots.refetch();void catalog.refetch();if(id&&valid)void query.refetch()}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>No instruments available.</EmptyState>}{!catalog.isPending&&!catalog.error&&!catalog.data?.length&&<EmptyState>No indicators are available.</EmptyState>}
 {query.data&&<><Panel><Plot title={indicator.toUpperCase()} data={query.data.series.map(v=>({type:'scatter',mode:'lines',name:v.name,x:query.data.times,y:v.values,connectgaps:false}))}/></Panel><SourceMetadata>Snapshot {query.data.snapshot_id} · Source: {snapshots.data?.find(v=>v.snapshot_id===query.data.snapshot_id)?.source_id||'unknown'} · Quality: {query.data.quality.state} · Gaps: {query.data.quality.gaps.length}</SourceMetadata>{query.data.warnings.map(v=><p className="muted" key={v}>{v}</p>)}<Panel><DataTable caption="Latest values" rows={query.data.series} rowKey={v=>v.name} columns={[{key:'name',label:'Series',render:v=>v.name},{key:'value',label:'Value',numeric:true,render:v=><span className="numeric">{v.values.at(-1)?.toPrecision(8)??'unavailable'}</span>}]}/></Panel></>}
 </section>;
}
