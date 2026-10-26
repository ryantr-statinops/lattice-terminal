import {useMemo,useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send,type Candle,type DatasetSnapshot,type IndexConstituentSnapshot,type IndexDailySnapshot,type Instrument,type Snapshot} from './api';
import {PageHeader,Panel,PanelHeader,Toolbar} from './ui/layout';
import {Button} from './ui/buttons';
import {Field,Select,TextInput} from './ui/fields';
import {DataTable,NumericValue,SourceMetadata,StatusLabel} from './ui/data';
import {EmptyState,ErrorState,InlineNotice,LoadingState} from './ui/feedback';
import {useAppearance} from './theme/store';
import {formatDate,formatDateTime} from './theme/dateTime';
import {MarketChart} from './market/MarketChart';
import type {IndicatorConfig} from './market/indicators';

function localDate(value:Date){return `${value.getFullYear()}-${String(value.getMonth()+1).padStart(2,'0')}-${String(value.getDate()).padStart(2,'0')}`}
function defaultDailyRange(){const end=new Date();end.setDate(end.getDate()-1);const start=new Date(end);start.setFullYear(start.getFullYear()-1);return {start:localDate(start),end:localDate(end)}}

export function Market(){
 const appearance=useAppearance();
 const client=useQueryClient();
 const datasets=useQuery({queryKey:['market-provider-datasets'],queryFn:()=>request<DatasetSnapshot[]>('/engine/market/datasets')});
 const routing=useQuery({queryKey:['provider-routing'],queryFn:()=>request<{datasets?:Record<string,string>}>('/providers/routing')});
 const providerCatalogues=useMemo(()=>Array.from(new Set((datasets.data??[]).filter(value=>value.dataset.startsWith('instruments.')).map(value=>value.provider_id))).sort(),[datasets.data]);
 const [catalogueProvider,setCatalogueProvider]=useState('fixture');
 const instruments=useQuery({queryKey:['instruments',catalogueProvider],queryFn:()=>request<Instrument[]>(catalogueProvider==='fixture'?'/engine/market/instruments':`/engine/market/instruments?provider_id=${encodeURIComponent(catalogueProvider)}`)});
 const [selected,setSelected]=useState(''),[assetClass,setAssetClass]=useState('all'),[notice,setNotice]=useState('');
 const [dailyRange]=useState(defaultDailyRange);const [dailyStart,setDailyStart]=useState(dailyRange.start),[dailyEnd,setDailyEnd]=useState(dailyRange.end);
 const [syncing,setSyncing]=useState(false),[syncError,setSyncError]=useState<unknown>(null),[syncNotice,setSyncNotice]=useState(''),[constituentNotice,setConstituentNotice]=useState(''),[dailyIndexNotice,setDailyIndexNotice]=useState('');
 const [indicators,setIndicators]=useState<IndicatorConfig>({ma20:true,ma50:false,volume:true});
 const [watchlist,setWatchlist]=useState<string[]>(()=>{try{const saved=JSON.parse(localStorage.getItem('kestrel.watchlist')||'[]');return Array.isArray(saved)?saved.filter((v:unknown)=>typeof v==='string'):[]}catch{return []}});
 const availableClasses=useMemo(()=>Array.from(new Set((instruments.data??[]).map(instrument=>instrument.instrument_class||'unknown'))).sort(),[instruments.data]);
 const filteredInstruments=useMemo(()=> (instruments.data??[]).filter(instrument=>assetClass==='all'||(instrument.instrument_class||'unknown')===assetClass),[instruments.data,assetClass]);
 const id=filteredInstruments.some(instrument=>instrument.id===selected)?selected:filteredInstruments[0]?.id||'';
 const instrument=filteredInstruments.find(value=>value.id===id);
 const hasFixtureCandles=catalogueProvider==='fixture';
 const candleRoute='candles.1d:equity:HOSE';
 const hasProviderCandleRoute=routing.data?.datasets?.[candleRoute]===`${catalogueProvider}:market-data:${candleRoute}`;
 const hasProviderSnapshot=(datasets.data??[]).some(value=>value.provider_id===catalogueProvider&&value.dataset==='candles.1d');
 const hasProviderCandles=catalogueProvider==='ssi'&&hasProviderCandleRoute&&hasProviderSnapshot;
 const hasCandleSource=hasFixtureCandles||hasProviderCandles;
 const data=useQuery({queryKey:['candles',catalogueProvider,id],queryFn:()=>hasFixtureCandles?request<Snapshot>('/engine/market/candles?instrument_id='+encodeURIComponent(id)):request<Snapshot>(`/engine/market/provider-candles?provider_id=${encodeURIComponent(catalogueProvider)}&instrument_id=${encodeURIComponent(id)}`),enabled:!!id&&hasCandleSource});
 const isSsiHoseIndex=catalogueProvider==='ssi'&&instrument?.instrument_class==='index'&&instrument.venue==='HOSE';
 const isSsiIndex=catalogueProvider==='ssi'&&instrument?.instrument_class==='index'&&(instrument.venue==='HOSE'||instrument.venue==='HNX');
 const constituentRoute='indices.constituents:index:HOSE';
 const hasProviderConstituentRoute=routing.data?.datasets?.[constituentRoute]===`ssi:market-data:${constituentRoute}`;
 const hasProviderConstituentSnapshot=(datasets.data??[]).some(value=>value.provider_id==='ssi'&&value.dataset==='indices.constituents');
 const indexConstituents=useQuery({queryKey:['index-constituents','ssi',id],queryFn:()=>request<IndexConstituentSnapshot>(`/engine/market/provider-index-constituents?provider_id=ssi&index_instrument_id=${encodeURIComponent(id)}`),enabled:!!id&&isSsiHoseIndex&&hasProviderConstituentRoute&&hasProviderConstituentSnapshot});
 const dailyIndexVenue=isSsiIndex?instrument?.venue??'unknown':'unknown';
 const dailyIndexRoute=`indices.daily:index:${dailyIndexVenue}`;
 const hasProviderDailyIndexRoute=routing.data?.datasets?.[dailyIndexRoute]==='ssi:market-data:'+dailyIndexRoute;
 const hasProviderDailyIndexSnapshot=(datasets.data??[]).some(value=>value.provider_id==='ssi'&&value.dataset==='indices.daily');
 const dailyIndex=useQuery({queryKey:['daily-index','ssi',id],queryFn:()=>request<IndexDailySnapshot>(`/engine/market/provider-index-daily?provider_id=ssi&venue=${encodeURIComponent(dailyIndexVenue)}&index_instrument_id=${encodeURIComponent(id)}`),enabled:!!id&&isSsiIndex&&hasProviderDailyIndexRoute&&hasProviderDailyIndexSnapshot});
 const syncDaily=async()=>{
  if(!instrument||instrument.instrument_class!=='equity'||instrument.venue!=='HOSE')return;
  setSyncing(true);setSyncError(null);setSyncNotice('');
  try{
   const result=await send<{snapshot_id:string}>('/ingestion/candles/ssi/hose-equity/daily',{instrument_id:instrument.id,from_date:dailyStart,to_date:dailyEnd});
   setSyncNotice(`SSI daily candles saved as snapshot ${result.snapshot_id.slice(0,12)}.`);
   await Promise.all([client.invalidateQueries({queryKey:['ingestion-jobs']}),client.invalidateQueries({queryKey:['market-provider-datasets']}),client.invalidateQueries({queryKey:['candles','ssi',instrument.id]})]);
  }catch(error){setSyncError(error);void client.invalidateQueries({queryKey:['ingestion-jobs']})}
  finally{setSyncing(false)}
 };
 const syncIndexComponents=async()=>{
  if(!instrument||!isSsiHoseIndex)return;
  setSyncing(true);setSyncError(null);setConstituentNotice('');
  try{
   const result=await send<{snapshot_id:string}>('/ingestion/index-constituents/ssi/hose',{index_instrument_id:instrument.id});
   setConstituentNotice(`SSI HOSE constituent snapshot saved as ${result.snapshot_id.slice(0,12)}.`);
   await Promise.all([client.invalidateQueries({queryKey:['ingestion-jobs']}),client.invalidateQueries({queryKey:['market-provider-datasets']}),client.invalidateQueries({queryKey:['index-constituents','ssi',instrument.id]})]);
  }catch(error){setSyncError(error);void client.invalidateQueries({queryKey:['ingestion-jobs']})}
  finally{setSyncing(false)}
 };
 const syncDailyIndex=async()=>{
  if(!instrument||!instrument.venue||!isSsiIndex||!validDailyRange)return;
  setSyncing(true);setSyncError(null);setDailyIndexNotice('');
  try{
   const result=await send<{snapshot_id:string}>(`/ingestion/index-series/ssi/${instrument.venue.toLowerCase()}/daily`,{index_instrument_id:instrument.id,from_date:dailyStart,to_date:dailyEnd});
   setDailyIndexNotice(`SSI ${instrument.venue} daily index data saved as snapshot ${result.snapshot_id.slice(0,12)}.`);
   await Promise.all([client.invalidateQueries({queryKey:['ingestion-jobs']}),client.invalidateQueries({queryKey:['market-provider-datasets']}),client.invalidateQueries({queryKey:['daily-index','ssi',instrument.id]})]);
  }catch(error){setSyncError(error);void client.invalidateQueries({queryKey:['ingestion-jobs']})}
  finally{setSyncing(false)}
 };
 const toggle=()=>{const next=watchlist.includes(id)?watchlist.filter(v=>v!==id):[...watchlist,id];setWatchlist(next);try{localStorage.setItem('kestrel.watchlist',JSON.stringify(next));setNotice('')}catch{setNotice('Watchlist changes are saved for this session only.')}};
 const snapshot=data.data;
 const latest=snapshot?.candles.at(-1);
 const quality=snapshot?.quality;
 const hasQualityWarnings=!!quality&&(quality.state==='partial'||quality.state==='stale'||quality.state==='unavailable'||quality.gaps.length>0||(quality.provisional_count||0)>0);
 const currency=latest?.currency&&latest.currency!=='unknown'?latest.currency:snapshot?.instrument.currency||'unknown';
 const priceUnit=latest?.price_unit||'unknown';
 const volumeUnit=latest?.volume_unit||'unknown';
 const sourceLabel=hasFixtureCandles?'SYNTHETIC':hasProviderCandles?`${catalogueProvider.toUpperCase()} DAILY DATA`:`${catalogueProvider.toUpperCase()} CATALOGUE`;
 const validDailyRange=!!dailyStart&&!!dailyEnd&&dailyStart<=dailyEnd&&dailyEnd<localDate(new Date());
 return <section><PageHeader title="Market" actions={<StatusLabel tone={hasFixtureCandles?'warning':'info'}>{sourceLabel}</StatusLabel>}/>
 <Toolbar>
  <Select aria-label="Instrument source" value={catalogueProvider} disabled={datasets.isPending} onChange={e=>{setCatalogueProvider(e.target.value);setSelected('');setAssetClass('all')}}><option value="fixture">Local fixture</option>{providerCatalogues.map(provider=><option value={provider} key={provider}>{provider.toUpperCase()}</option>)}</Select>
  <Select aria-label="Asset class" value={assetClass} disabled={instruments.isPending||availableClasses.length===0} onChange={e=>setAssetClass(e.target.value)}><option value="all">All asset classes</option>{availableClasses.map(value=><option value={value} key={value}>{value.replaceAll('_',' ')}</option>)}</Select>
  <Select aria-label="Instrument" value={id} disabled={instruments.isPending||!filteredInstruments.length} onChange={e=>setSelected(e.target.value)}>{filteredInstruments.map(v=><option value={v.id} key={v.id}>{v.native_symbol} · {v.venue??'No venue'}</option>)}</Select>
  <Button disabled={!id} aria-pressed={watchlist.includes(id)} onClick={toggle}>{watchlist.includes(id)?'★ Watching':'☆ Watch'}</Button>
  <Button disabled={!id||!hasCandleSource} pending={data.isFetching} onClick={()=>void data.refetch()}>Refresh</Button>
  <Button aria-pressed={indicators.ma20} onClick={()=>setIndicators(i=>({...i,ma20:!i.ma20}))}>MA20</Button>
  <Button aria-pressed={indicators.ma50} onClick={()=>setIndicators(i=>({...i,ma50:!i.ma50}))}>MA50</Button>
  <Button aria-pressed={indicators.volume} onClick={()=>setIndicators(i=>({...i,volume:!i.volume}))}>Volume</Button>
 </Toolbar>
 {notice&&<InlineNotice tone="warning">{notice}</InlineNotice>}{(datasets.isPending||routing.isPending||instruments.isPending||data.isFetching||indexConstituents.isFetching||dailyIndex.isFetching)&&<LoadingState>Loading market data…</LoadingState>}<ErrorState error={datasets.error||routing.error||instruments.error||data.error||indexConstituents.error||dailyIndex.error||syncError} onRetry={()=>{void datasets.refetch();void routing.refetch();void instruments.refetch();if(id&&hasCandleSource)void data.refetch();if(id&&isSsiHoseIndex&&hasProviderConstituentRoute)void indexConstituents.refetch();if(id&&isSsiIndex&&hasProviderDailyIndexRoute)void dailyIndex.refetch();setSyncError(null)}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>No instruments are available.</EmptyState>}
 {!hasFixtureCandles&&!!instrument&&<Panel>
  <PanelHeader title="PROVIDER HISTORY" actions={<StatusLabel tone="info">{catalogueProvider.toUpperCase()} DATA</StatusLabel>}/>
  <div className="panel-content">
   <p>{instrument.instrument_class==='index'?(instrument.venue==='HOSE'&&catalogueProvider==='ssi'?'HOSE membership snapshots and daily index observations can be saved separately. Neither implies historical constituent dates or simulation coverage.':instrument.venue==='HNX'&&catalogueProvider==='ssi'?'HNX daily index observations are available separately from candles. They do not imply simulation coverage.':'Index catalogue entry is available for browsing. Daily index data has not been ingested for this venue.'):'Historical candles are stored with provider provenance. Unknown units, adjustment semantics and calendar quality remain visible; this dataset is not enabled for simulation.'}</p>
   {isSsiHoseIndex&&<>
    <Button pending={syncing} onClick={()=>void syncIndexComponents()}>Sync SSI HOSE constituents</Button>
    {constituentNotice&&<InlineNotice tone="positive">{constituentNotice}</InlineNotice>}
    {hasProviderConstituentSnapshot&&!hasProviderConstituentRoute&&<p className="muted">A constituent snapshot is saved, but Market reads it only when SSI is selected for the HOSE index constituents route in Provider settings.</p>}
    {!hasProviderConstituentSnapshot&&<p className="muted">No SSI HOSE constituent snapshot is saved. Sync requires approval for exact SSI access and storage rights.</p>}
    {hasProviderConstituentSnapshot&&hasProviderConstituentRoute&&!indexConstituents.data&&<p className="muted">No saved constituent snapshot exists for this index yet.</p>}
   </>}
   {isSsiIndex&&<>
    <div className="form-grid"><Field label="From date"><TextInput type="date" value={dailyStart} max={localDate(new Date())} onChange={event=>setDailyStart(event.target.value)}/></Field><Field label="Through date"><TextInput type="date" value={dailyEnd} max={localDate(new Date())} onChange={event=>setDailyEnd(event.target.value)}/></Field></div>
    <Button disabled={!validDailyRange} pending={syncing} onClick={()=>void syncDailyIndex()}>Sync SSI daily index data</Button>
    {dailyIndexNotice&&<InlineNotice tone="positive">{dailyIndexNotice}</InlineNotice>}
    {hasProviderDailyIndexSnapshot&&!hasProviderDailyIndexRoute&&<p className="muted">Daily index snapshots are saved, but Market reads them only when SSI is selected for the {dailyIndexVenue} daily index route in Provider settings.</p>}
    {!hasProviderDailyIndexSnapshot&&<p className="muted">No SSI {dailyIndexVenue} daily index snapshot is saved. Sync requires approval for exact SSI access and storage rights.</p>}
    {hasProviderDailyIndexSnapshot&&hasProviderDailyIndexRoute&&!dailyIndex.data&&<p className="muted">No daily index observations have been saved for this index yet.</p>}
   </>}
   {catalogueProvider==='ssi'&&instrument.instrument_class==='equity'&&instrument.venue==='HOSE'&&<>
     <div className="form-grid"><Field label="From date"><TextInput type="date" value={dailyStart} max={localDate(new Date())} onChange={event=>setDailyStart(event.target.value)}/></Field><Field label="Through date"><TextInput type="date" value={dailyEnd} max={localDate(new Date())} onChange={event=>setDailyEnd(event.target.value)}/></Field></div>
    <Button disabled={!validDailyRange} pending={syncing} onClick={()=>void syncDaily()}>Sync SSI daily candles</Button>
    {syncNotice&&<InlineNotice tone="positive">{syncNotice}</InlineNotice>}
    {!hasProviderSnapshot&&<p className="muted">No daily candle snapshot is saved. Sync requires approval for exact SSI access and storage rights.</p>}
    {hasProviderSnapshot&&!hasProviderCandleRoute&&<p className="muted">A daily snapshot exists, but Market reads it only when SSI is selected for the HOSE daily candle route in Provider settings.</p>}
    {hasProviderSnapshot&&hasProviderCandleRoute&&!snapshot&&<p className="muted">No daily candle snapshot exists for this instrument yet.</p>}
   </>}
  </div>
 </Panel>}
 {hasProviderConstituentRoute&&isSsiHoseIndex&&indexConstituents.data&&<Panel><PanelHeader title={indexConstituents.data.index.name} actions={<span>{indexConstituents.data.constituents.constituents.length} saved members · {indexConstituents.data.constituents.exchange}</span>}/><div className="panel-content"><p>Provider reports {indexConstituents.data.constituents.reported_total_symbol_count} members. This is the observed membership set at {formatDateTime(indexConstituents.data.observed_at,appearance.dateTimeRegion)}; it does not establish historical membership dates.</p><SourceMetadata>Snapshot {indexConstituents.data.snapshot_id.slice(0,16)} · Source: {indexConstituents.data.constituents.source_id} · Provider identifiers are shown as reported; their identifier type is unverified.</SourceMetadata><DataTable caption="SSI HOSE index constituents" rows={indexConstituents.data.constituents.constituents} rowKey={member=>`${member.native_symbol}-${member.provider_security_id||member.native_symbol}`} columns={[{key:'symbol',label:'Symbol',render:member=>member.native_symbol},{key:'provider-id',label:'Provider security identifier (unverified type)',render:member=>member.provider_security_id||'Not provided'}]}/></div></Panel>}
 {hasProviderDailyIndexRoute&&isSsiIndex&&dailyIndex.data&&<Panel><PanelHeader title={`${dailyIndex.data.index.name} daily observations`} actions={<span>{dailyIndex.data.records.length} days · {dailyIndex.data.index.venue}</span>}/><div className="panel-content"><p>Provider time and statistic units retain their documented or unknown semantics. This dataset is not candles and is not enabled for simulation.</p><SourceMetadata>Snapshots {dailyIndex.data.snapshot_ids.map(value=>value.slice(0,12)).join(', ')} · Source: SSI-FC-DATA · Observed locally; provider publication timing is unverified.</SourceMetadata><DataTable caption={`SSI ${dailyIndex.data.index.venue} daily index observations`} rows={dailyIndex.data.records} rowKey={record=>record.observation.trading_date} columns={[{key:'date',label:'Trading date',render:record=>formatDate(record.observation.trading_date,appearance.dateTimeRegion)},{key:'index',label:'Index value · provider scale',numeric:true,render:record=><NumericValue value={record.observation.index_value}/>},{key:'change',label:'Change · provider scale',numeric:true,render:record=><NumericValue value={record.observation.change} signed/>},{key:'ratio',label:'Change ratio · provider scale',numeric:true,render:record=><NumericValue value={record.observation.ratio_change} signed/>},{key:'volume',label:'Total volume · provider unit',numeric:true,render:record=><NumericValue value={record.observation.total_volume}/>},{key:'value',label:'Total value · currency unknown',numeric:true,render:record=><NumericValue value={record.observation.total_value}/>},{key:'advances',label:'Advances',numeric:true,render:record=><NumericValue value={record.observation.advances}/>},{key:'declines',label:'Declines',numeric:true,render:record=><NumericValue value={record.observation.declines}/>} ]}/></div></Panel>}
 {hasQualityWarnings&&quality&&<InlineNotice tone="warning">Snapshot quality is {quality.state}. {quality.gaps.length?`Gaps: ${quality.gaps.join(', ')}. `:''}{quality.provisional_count?`${quality.provisional_count} provisional bars are excluded from historical use.`:''}</InlineNotice>}
 {snapshot&&<Panel><PanelHeader title="DATASET COVERAGE" actions={<StatusLabel tone="info">ANALYSIS DATA</StatusLabel>}/><div className="panel-content"><p>Chart and indicator analysis: available from this candle snapshot, subject to the quality details above.</p><p>Strategy signals: require a separately declared live or replay feed; this snapshot does not declare signal coverage.</p><p>Simulation: unavailable from OHLC candles alone. It requires detailed quote events and matching effective rule and fill coverage.</p></div></Panel>}
 {snapshot&&<><Panel><PanelHeader title={snapshot.instrument.name} actions={<span>{snapshot.quality.state} · {snapshot.candles.length} daily bars · {currency}</span>}/>{snapshot.candles.length?<MarketChart candles={snapshot.candles} indicators={indicators}/>:<EmptyState>This snapshot has no candles.</EmptyState>}</Panel>
 <SourceMetadata>Snapshot {snapshot.snapshot_id.slice(0,16)} · Source: {latest?.source_id||'unknown'} · Revision: {latest?.revision||'unknown'} · Quality: {quality?.state||'unknown'} · Gaps: {quality?.gaps.length??0} · Provisional: {quality?.provisional_count??0} · Adjustment: {quality?.adjustment||'unknown'} · Calendar: {quality?.calendar||'unknown'} · Currency: {currency} · Prices: {priceUnit} · Volume: {volumeUnit} · {latest?.available_at?formatDateTime(latest.available_at,appearance.dateTimeRegion):'unavailable'}</SourceMetadata>
 <Panel><DataTable caption="Latest candles" rows={snapshot.candles.slice(-10)} rowKey={v=>v.open_time} columns={[{key:'date',label:'Date',render:v=>formatDate(v.open_time,appearance.dateTimeRegion)},...(['open','high','low','close'] as const).map(key=>({key,label:`${key.toUpperCase()} · ${priceUnit}`,numeric:true,render:(v:Candle)=><NumericValue value={v[key]}/>})),{key:'volume',label:`VOLUME · ${volumeUnit}`,numeric:true,render:(v:Candle)=><NumericValue value={v.volume}/>} ]}/></Panel></>}
 </section>;
}
