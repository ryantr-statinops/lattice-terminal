import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {request,type Instrument} from './api';
import {Plot} from './Plot';
import {PageHeader,Panel,Toolbar} from './ui/layout';
import {Field,Select,TextInput} from './ui/fields';
import {DataTable,SourceMetadata,StatusLabel} from './ui/data';
import {EmptyState,ErrorState,LoadingState} from './ui/feedback';
type Result={indicator:string;times:string[];series:{name:string;values:(number|null)[]}[];warnings:string[];snapshot_id:string};
export function Quant(){
 const instruments=useQuery({queryKey:['instruments'],queryFn:()=>request<Instrument[]>('/engine/market/instruments')});
 const catalog=useQuery({queryKey:['indicator-catalog'],queryFn:()=>request<string[]>('/engine/quant/indicators')});
 const [selected,setSelected]=useState(''),[indicator,setIndicator]=useState('sma'),[period,setPeriod]=useState(14),[benchmark,setBenchmark]=useState('');
 const id=selected||instruments.data?.[0]?.id||'';const valid=Number.isInteger(period)&&period>=2&&period<=1000;
 const query=useQuery({queryKey:['quant',id,indicator,period,benchmark],enabled:!!id&&valid&&!catalog.error&&!!catalog.data?.includes(indicator),queryFn:()=>request<Result>(`/engine/quant/calculate?instrument_id=${encodeURIComponent(id)}&indicator=${encodeURIComponent(indicator)}&period=${period}${benchmark?'&benchmark_id='+encodeURIComponent(benchmark):''}`)});
 return <section><PageHeader eyebrow="QUANT / INDICATORS" title="Phân tích định lượng" actions={<StatusLabel tone="warning">FIXTURE · CLOSED BARS</StatusLabel>}/><Link to="/quant/research">Mở Python Research Editor →</Link><Toolbar><Field label="Instrument"><Select value={id} disabled={!instruments.data?.length} onChange={e=>setSelected(e.target.value)}>{instruments.data?.map(v=><option key={v.id} value={v.id}>{v.native_symbol} · {v.venue}</option>)}</Select></Field><Field label="Indicator"><Select value={indicator} disabled={!catalog.data?.length} onChange={e=>setIndicator(e.target.value)}>{catalog.data?.map(v=><option key={v}>{v}</option>)}</Select></Field><Field label="Lookback period" error={!valid?'Nhập số nguyên từ 2 đến 1000.':undefined}><TextInput type="number" min={2} max={1000} value={period||''} onChange={e=>setPeriod(Number(e.target.value))}/></Field><Field label="Benchmark"><Select value={benchmark} onChange={e=>setBenchmark(e.target.value)}><option value="">Chưa chọn benchmark</option>{instruments.data?.map(v=><option key={v.id} value={v.id}>{v.native_symbol}</option>)}</Select></Field></Toolbar><SourceMetadata>Nến đã đóng · right-aligned · warm-up giữ null · không điền dữ liệu thiếu. Kết quả từ fixtures, không phải tín hiệu đầu tư.</SourceMetadata>
 {(instruments.isPending||catalog.isPending||query.isFetching)&&<LoadingState>Đang đọc dữ liệu và tính chỉ báo…</LoadingState>}<ErrorState error={instruments.error||catalog.error||query.error} onRetry={()=>{void instruments.refetch();void catalog.refetch();if(id&&valid)void query.refetch()}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>Chưa có instrument.</EmptyState>}{!catalog.isPending&&!catalog.error&&!catalog.data?.length&&<EmptyState>Chưa có chỉ báo khả dụng.</EmptyState>}
 {query.data&&<><Panel><Plot title={indicator.toUpperCase()} data={query.data.series.map(v=>({type:'scatter',mode:'lines',name:v.name,x:query.data.times,y:v.values,connectgaps:false}))}/></Panel><SourceMetadata>Snapshot {query.data.snapshot_id}</SourceMetadata>{query.data.warnings.map(v=><p className="muted" key={v}>{v}</p>)}<Panel><DataTable caption="Giá trị gần nhất" rows={query.data.series} rowKey={v=>v.name} columns={[{key:'name',label:'Series',render:v=>v.name},{key:'value',label:'Value',numeric:true,render:v=><span className="numeric">{v.values.at(-1)?.toPrecision(8)??'unavailable'}</span>}]}/></Panel></>}
 </section>;
}
