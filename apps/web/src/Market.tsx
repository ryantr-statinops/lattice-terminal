import {useMemo,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {request,type Candle,type DatasetSnapshot,type Instrument,type Snapshot} from './api';
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
 const datasets=useQuery({queryKey:['market-provider-datasets'],queryFn:()=>request<DatasetSnapshot[]>('/engine/market/datasets')});
 const providerCatalogues=useMemo(()=>Array.from(new Set((datasets.data??[]).filter(value=>value.dataset.startsWith('instruments.')).map(value=>value.provider_id))).sort(),[datasets.data]);
 const [catalogueProvider,setCatalogueProvider]=useState('fixture');
 const instruments=useQuery({queryKey:['instruments',catalogueProvider],queryFn:()=>request<Instrument[]>(catalogueProvider==='fixture'?'/engine/market/instruments':`/engine/market/instruments?provider_id=${encodeURIComponent(catalogueProvider)}`)});
 const [selected,setSelected]=useState(''),[assetClass,setAssetClass]=useState('all'),[notice,setNotice]=useState('');
 const [indicators,setIndicators]=useState<IndicatorConfig>({ma20:true,ma50:false,volume:true});
 const [watchlist,setWatchlist]=useState<string[]>(()=>{try{const saved=JSON.parse(localStorage.getItem('kestrel.watchlist')||'[]');return Array.isArray(saved)?saved.filter((v:unknown)=>typeof v==='string'):[]}catch{return []}});
 const availableClasses=useMemo(()=>Array.from(new Set((instruments.data??[]).map(instrument=>instrument.instrument_class||'unknown'))).sort(),[instruments.data]);
 const filteredInstruments=useMemo(()=> (instruments.data??[]).filter(instrument=>assetClass==='all'||(instrument.instrument_class||'unknown')===assetClass),[instruments.data,assetClass]);
 const id=filteredInstruments.some(instrument=>instrument.id===selected)?selected:filteredInstruments[0]?.id||'';
 const hasFixtureCandles=catalogueProvider==='fixture';
 const data=useQuery({queryKey:['candles',catalogueProvider,id],queryFn:()=>request<Snapshot>('/engine/market/candles?instrument_id='+encodeURIComponent(id)),enabled:!!id&&hasFixtureCandles});
 const toggle=()=>{const next=watchlist.includes(id)?watchlist.filter(v=>v!==id):[...watchlist,id];setWatchlist(next);try{localStorage.setItem('kestrel.watchlist',JSON.stringify(next));setNotice('')}catch{setNotice('Watchlist changes are saved for this session only.')}};
 const snapshot=data.data;
 const latest=snapshot?.candles.at(-1);
 const quality=snapshot?.quality;
 const hasQualityWarnings=!!quality&&(quality.state==='partial'||quality.state==='stale'||quality.state==='unavailable'||quality.gaps.length>0||(quality.provisional_count||0)>0);
 const currency=latest?.currency&&latest.currency!=='unknown'?latest.currency:snapshot?.instrument.currency||'unknown';
 const priceUnit=latest?.price_unit||'unknown';
 const volumeUnit=latest?.volume_unit||'unknown';
 return <section><PageHeader title="Market" actions={<StatusLabel tone={hasFixtureCandles?'warning':'info'}>{hasFixtureCandles?'SYNTHETIC':`${catalogueProvider.toUpperCase()} CATALOGUE`}</StatusLabel>}/>
 <Toolbar>
  <Select aria-label="Instrument source" value={catalogueProvider} disabled={datasets.isPending} onChange={e=>{setCatalogueProvider(e.target.value);setSelected('');setAssetClass('all')}}><option value="fixture">Local fixture</option>{providerCatalogues.map(provider=><option value={provider} key={provider}>{provider.toUpperCase()}</option>)}</Select>
  <Select aria-label="Asset class" value={assetClass} disabled={instruments.isPending||availableClasses.length===0} onChange={e=>setAssetClass(e.target.value)}><option value="all">All asset classes</option>{availableClasses.map(value=><option value={value} key={value}>{value.replaceAll('_',' ')}</option>)}</Select>
  <Select aria-label="Instrument" value={id} disabled={instruments.isPending||!filteredInstruments.length} onChange={e=>setSelected(e.target.value)}>{filteredInstruments.map(v=><option value={v.id} key={v.id}>{v.native_symbol} · {v.venue??'No venue'}</option>)}</Select>
  <Button disabled={!id} aria-pressed={watchlist.includes(id)} onClick={toggle}>{watchlist.includes(id)?'★ Watching':'☆ Watch'}</Button>
  <Button disabled={!id||!hasFixtureCandles} pending={data.isFetching} onClick={()=>void data.refetch()}>Refresh</Button>
  <Button aria-pressed={indicators.ma20} onClick={()=>setIndicators(i=>({...i,ma20:!i.ma20}))}>MA20</Button>
  <Button aria-pressed={indicators.ma50} onClick={()=>setIndicators(i=>({...i,ma50:!i.ma50}))}>MA50</Button>
  <Button aria-pressed={indicators.volume} onClick={()=>setIndicators(i=>({...i,volume:!i.volume}))}>Volume</Button>
 </Toolbar>
 {notice&&<InlineNotice tone="warning">{notice}</InlineNotice>}{(datasets.isPending||instruments.isPending||data.isFetching)&&<LoadingState>Loading market data…</LoadingState>}<ErrorState error={datasets.error||instruments.error||data.error} onRetry={()=>{void datasets.refetch();void instruments.refetch();if(id&&hasFixtureCandles)void data.refetch()}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>No instruments are available.</EmptyState>}
 {!hasFixtureCandles&&!!instruments.data?.length&&<Panel><PanelHeader title="INSTRUMENT CATALOGUE" actions={<StatusLabel tone="info">PROVIDER DATA</StatusLabel>}/><div className="panel-content"><p>Catalogue source: {catalogueProvider}. No candle snapshot is available for this instrument yet, so chart and indicator analysis remain unavailable.</p></div></Panel>}
 {hasQualityWarnings&&quality&&<InlineNotice tone="warning">Snapshot quality is {quality.state}. {quality.gaps.length?`Gaps: ${quality.gaps.join(', ')}. `:''}{quality.provisional_count?`${quality.provisional_count} provisional bars are excluded from historical use.`:''}</InlineNotice>}
 {snapshot&&<Panel><PanelHeader title="DATASET COVERAGE" actions={<StatusLabel tone="info">ANALYSIS DATA</StatusLabel>}/><div className="panel-content"><p>Chart and indicator analysis: available from this candle snapshot, subject to the quality details above.</p><p>Strategy signals: require a separately declared live or replay feed; this snapshot does not declare signal coverage.</p><p>Simulation: unavailable from OHLC candles alone. It requires detailed quote events and matching effective rule and fill coverage.</p></div></Panel>}
 {snapshot&&<><Panel><PanelHeader title={snapshot.instrument.name} actions={<span>{snapshot.quality.state} · {snapshot.candles.length} daily bars · {currency}</span>}/>{snapshot.candles.length?<MarketChart candles={snapshot.candles} indicators={indicators}/>:<EmptyState>This snapshot has no candles.</EmptyState>}</Panel>
 <SourceMetadata>Snapshot {snapshot.snapshot_id.slice(0,16)} · Source: {latest?.source_id||'unknown'} · Revision: {latest?.revision||'unknown'} · Quality: {quality?.state||'unknown'} · Gaps: {quality?.gaps.length??0} · Provisional: {quality?.provisional_count??0} · Adjustment: {quality?.adjustment||'unknown'} · Calendar: {quality?.calendar||'unknown'} · Currency: {currency} · Prices: {priceUnit} · Volume: {volumeUnit} · {latest?.available_at?formatDateTime(latest.available_at,appearance.dateTimeRegion):'unavailable'}</SourceMetadata>
 <Panel><DataTable caption="Latest candles" rows={snapshot.candles.slice(-10)} rowKey={v=>v.open_time} columns={[{key:'date',label:'Date',render:v=>formatDate(v.open_time,appearance.dateTimeRegion)},...(['open','high','low','close'] as const).map(key=>({key,label:`${key.toUpperCase()} · ${priceUnit}`,numeric:true,render:(v:Candle)=><NumericValue value={v[key]}/>})),{key:'volume',label:`VOLUME · ${volumeUnit}`,numeric:true,render:(v:Candle)=><NumericValue value={v.volume}/>} ]}/></Panel></>}
 </section>;
}
