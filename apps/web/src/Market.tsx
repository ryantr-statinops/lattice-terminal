import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request,type Candle,type Instrument,type Snapshot} from './api';
import {PageHeader,Panel,PanelHeader,Toolbar} from './ui/layout';
import {Button} from './ui/buttons';
import {Select} from './ui/fields';
import {DataTable,NumericValue,SourceMetadata,StatusLabel} from './ui/data';
import {EmptyState,ErrorState,InlineNotice,LoadingState} from './ui/feedback';
import {useAppearance} from './theme/store';
import {formatDate,formatDateTime} from './theme/dateTime';
import {MarketChart} from './market/MarketChart';
import type {IndicatorConfig} from './market/indicators';

export function Market(){
 const appearance=useAppearance();
 const instruments=useQuery({queryKey:['instruments'],queryFn:()=>request<Instrument[]>('/engine/market/instruments')});
 const [selected,setSelected]=useState(''),[notice,setNotice]=useState('');
 const [indicators,setIndicators]=useState<IndicatorConfig>({ma20:true,ma50:false,volume:true});
 const [watchlist,setWatchlist]=useState<string[]>(()=>{try{const saved=JSON.parse(localStorage.getItem('kestrel.watchlist')||'[]');return Array.isArray(saved)?saved.filter((v:unknown)=>typeof v==='string'):[]}catch{return []}});
 const id=selected||instruments.data?.[0]?.id||'';
 const data=useQuery({queryKey:['candles',id],queryFn:()=>request<Snapshot>('/engine/market/candles?instrument_id='+encodeURIComponent(id)),enabled:!!id});
 const toggle=()=>{const next=watchlist.includes(id)?watchlist.filter(v=>v!==id):[...watchlist,id];setWatchlist(next);try{localStorage.setItem('kestrel.watchlist',JSON.stringify(next));setNotice('')}catch{setNotice('Watchlist changes are saved for this session only.')}};
 const snapshot=data.data;
 return <section><PageHeader eyebrow="MARKET / EQUITIES" title="Market" actions={<StatusLabel tone="warning">SYNTHETIC-FIXTURE</StatusLabel>}/>
 <Toolbar>
  <Select aria-label="Instrument" value={id} disabled={instruments.isPending||!instruments.data?.length} onChange={e=>setSelected(e.target.value)}>{instruments.data?.map(v=><option value={v.id} key={v.id}>{v.native_symbol} · {v.venue}</option>)}</Select>
  <Button disabled={!id} aria-pressed={watchlist.includes(id)} onClick={toggle}>{watchlist.includes(id)?'★ Watching':'☆ Watch'}</Button>
  <Button disabled={!id} pending={data.isFetching} onClick={()=>void data.refetch()}>Refresh</Button>
  <Button aria-pressed={indicators.ma20} onClick={()=>setIndicators(i=>({...i,ma20:!i.ma20}))}>MA20</Button>
  <Button aria-pressed={indicators.ma50} onClick={()=>setIndicators(i=>({...i,ma50:!i.ma50}))}>MA50</Button>
  <Button aria-pressed={indicators.volume} onClick={()=>setIndicators(i=>({...i,volume:!i.volume}))}>Volume</Button>
 </Toolbar>
 <SourceMetadata>Synthetic data for development. SSI is not authorized for production use; this is not live market data.</SourceMetadata>
 {notice&&<InlineNotice tone="warning">{notice}</InlineNotice>}{(instruments.isPending||data.isFetching)&&<LoadingState>Loading snapshot…</LoadingState>}<ErrorState error={instruments.error||data.error} onRetry={()=>{void instruments.refetch();if(id)void data.refetch()}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>No instruments are available.</EmptyState>}
 {snapshot&&<><Panel><PanelHeader title={snapshot.instrument.name} actions={<span>{snapshot.quality.state} · {snapshot.candles.length} daily bars</span>}/>{snapshot.candles.length?<MarketChart candles={snapshot.candles} indicators={indicators}/>:<EmptyState>This snapshot has no candles.</EmptyState>}</Panel>
 <SourceMetadata>Snapshot {snapshot.snapshot_id.slice(0,16)} · Adjustment: {snapshot.quality.adjustment}<br/>As of {snapshot.candles.at(-1)?.available_at?formatDateTime(snapshot.candles.at(-1)!.available_at,appearance.dateTimeRegion):'unavailable'}<br/>Gaps: {snapshot.quality.gaps.length?snapshot.quality.gaps.join(', '):'Not included in fixture; live calendar not verified'}</SourceMetadata>
 <Panel><DataTable caption="Latest candles — synthetic prices and volume" rows={snapshot.candles.slice(-10)} rowKey={v=>v.open_time} columns={[{key:'date',label:'Date',render:v=>formatDate(v.open_time,appearance.dateTimeRegion)},...(['open','high','low','close','volume'] as const).map(key=>({key,label:key.toUpperCase(),numeric:true,render:(v:Candle)=><NumericValue value={v[key]}/>}))]}/></Panel></>}
 </section>;
}
