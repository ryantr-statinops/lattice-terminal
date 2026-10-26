// @vitest-environment jsdom
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';

const echarts=vi.hoisted(()=>{
 const instance={setOption:vi.fn(),resize:vi.fn(),dispose:vi.fn()};
 return {instance,init:vi.fn(()=>instance),use:vi.fn()};
});
vi.mock('echarts/core',()=>({init:echarts.init,use:echarts.use}));
vi.mock('echarts/charts',()=>({CandlestickChart:'candlestick-chart',LineChart:'line-chart',BarChart:'bar-chart'}));
vi.mock('echarts/components',()=>({AxisPointerComponent:'axis-pointer',DataZoomInsideComponent:'inside-data-zoom',GridComponent:'grid',TooltipComponent:'tooltip'}));
vi.mock('echarts/renderers',()=>({CanvasRenderer:'canvas-renderer'}));

import {Market} from './Market';
import {setColor,resetAppearance} from './theme/store';
import type {Candle,Instrument,Snapshot} from './api';

const instruments:Instrument[]=[
 {id:'VN:SYN01',venue:'HOSE',native_symbol:'SYN01',instrument_class:'equity',name:'Synthetic One',is_synthetic:true},
 {id:'VN:BOND01',venue:'HNX',native_symbol:'BOND01',instrument_class:'bond',name:'Synthetic Bond',is_synthetic:true},
];
const candles:Candle[]=[
 {open_time:'2026-10-19T02:00:00Z',close_time:'2026-10-19T09:00:00Z',available_at:'2026-10-19T09:00:00Z',open:'100',high:'112',low:'99',close:'110',volume:'1200',currency:'VND',price_unit:'VND/share',volume_unit:'share',source_id:'provider-fixture',revision:'1',is_closed:true},
 {open_time:'2026-10-20T02:00:00Z',close_time:'2026-10-20T09:00:00Z',available_at:'2026-10-20T09:00:00Z',open:'110',high:'115',low:'108',close:'109',volume:'1500',currency:'VND',price_unit:'VND/share',volume_unit:'share',source_id:'provider-fixture',revision:'2',is_closed:true},
];
const snapshot:Snapshot={snapshot_id:'fixture-market-snapshot',instrument:instruments[0],quality:{state:'complete',gaps:[],adjustment:'unadjusted'},candles};
let resizeCallback:ResizeObserverCallback|undefined;

class TestResizeObserver{
 constructor(callback:ResizeObserverCallback){resizeCallback=callback}
 observe=vi.fn();
 disconnect=vi.fn();
}

function showMarket(response=(url:string)=>url.includes('/market/datasets')?[]:url.includes('/providers/routing')?{datasets:{}}:url.includes('/instruments')?instruments:snapshot){
 const fetcher=vi.fn(async(input:RequestInfo|URL)=>new Response(JSON.stringify(response(String(input))),{status:200,headers:{'Content-Type':'application/json'}}));
 vi.stubGlobal('fetch',fetcher);
 return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
}

beforeEach(()=>{
 resizeCallback=undefined;
 document.documentElement.dataset.theme='dark';
 vi.stubGlobal('ResizeObserver',TestResizeObserver);
});
afterEach(()=>{cleanup();resetAppearance();vi.unstubAllGlobals();vi.clearAllMocks();localStorage.clear()});

describe('Market ECharts chart',()=>{
 it('maps daily OHLC into a Vietnamese-localized, zoomable candlestick chart',async()=>{
  showMarket();
  await screen.findByRole('img',{name:'Candlestick chart; data table below'});
  await waitFor(()=>expect(echarts.instance.setOption).toHaveBeenCalledOnce());
  const option=echarts.instance.setOption.mock.calls[0][0] as {series:{type:string;data:number[][]}[];xAxis:{data:string[]};dataZoom:{type:string}[];tooltip:{axisPointer:{type:string};formatter:(params:unknown)=>string}};
  expect(option.series[0].type).toBe('candlestick');
  expect(option.series[0].data).toEqual([[100,110,99,112],[110,109,108,115]]);
  expect(option.xAxis.data).toEqual(['19/10/2026','20/10/2026']);
  expect(option.dataZoom[0]).toMatchObject({type:'inside',zoomOnMouseWheel:true,moveOnMouseMove:true});
  expect(option.tooltip.axisPointer.type).toBe('cross');
  expect(option.tooltip.formatter([{axisValueLabel:'20/10/2026',value:[110,109,108,115]}])).toContain('High: 115');
  expect(screen.getByText(/Currency: VND · Prices: VND\/share · Volume: share/)).toBeDefined();
  expect(screen.getByText(/Source: provider-fixture · Revision: 2/)).toBeDefined();
  expect(screen.getByText(/Chart and indicator analysis: available from this candle snapshot/)).toBeDefined();
  expect(screen.getByText(/Strategy signals: require a separately declared live or replay feed/)).toBeDefined();
  expect(screen.getByText(/Simulation: unavailable from OHLC candles alone/)).toBeDefined();
  expect(screen.getByRole('columnheader',{name:'OPEN · VND/share'})).toBeDefined();
  expect(screen.getByRole('columnheader',{name:'VOLUME · share'})).toBeDefined();
  resizeCallback?.([{contentRect:{width:640}} as ResizeObserverEntry],{} as ResizeObserver);
  expect(echarts.instance.resize).toHaveBeenCalledWith({width:640});
 });

 it('updates colors without recreating the chart or resetting inside zoom',async()=>{
  showMarket();await screen.findByRole('img');await waitFor(()=>expect(echarts.instance.setOption).toHaveBeenCalledOnce());
  act(()=>setColor('positive','#ABCDEF'));
  expect(echarts.init).toHaveBeenCalledOnce();
  const option=echarts.instance.setOption.mock.calls.at(-1)![0] as {dataZoom?:unknown;series:{itemStyle:{color:string}}[]};
  expect(option.dataZoom).toBeUndefined();expect(option.series[0].itemStyle.color).toBe('#ABCDEF');
 });

 it('shows an empty snapshot without creating a chart',async()=>{
  showMarket(url=>url.includes('/market/datasets')?[]:url.includes('/instruments')?instruments:{...snapshot,candles:[]});
  await screen.findByText('This snapshot has no candles.');
  expect(echarts.init).not.toHaveBeenCalled();
 });

 it('filters instrument choices by asset class',async()=>{
  showMarket();
  const filter=await screen.findByLabelText('Asset class');
  await screen.findByRole('option',{name:'SYN01 · HOSE'});
  const instrument=screen.getByLabelText('Instrument') as HTMLSelectElement;
  expect(Array.from(instrument.options).map(option=>option.value)).toEqual(['VN:SYN01','VN:BOND01']);
  fireEvent.change(filter,{target:{value:'bond'}});
  expect(Array.from(instrument.options).map(option=>option.value)).toEqual(['VN:BOND01']);
  expect(instrument.value).toBe('VN:BOND01');
 });

 it('loads a provider instrument catalogue and explains missing candle coverage',async()=>{
  const providerInstrument:Instrument={id:'SSI:ISIN-AAA',venue:'HOSE',board:'unknown',native_symbol:'AAA',instrument_class:'equity',name:'Provider AAA',currency:'VND',is_synthetic:false};
  const fetcher=vi.fn(async(input:RequestInfo|URL)=>{
   const url=String(input);
   const value=url.includes('/market/datasets')?[{provider_id:'ssi',dataset:'instruments.details',snapshot_id:'catalogue-1'}]:url.includes('/instruments?provider_id=ssi')?[providerInstrument]:url.includes('/instruments')?instruments:snapshot;
   return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
  });
  vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);

  const source=await screen.findByLabelText('Instrument source');
  await screen.findByRole('option',{name:'SSI'});
  fireEvent.change(source,{target:{value:'ssi'}});
  await screen.findByRole('option',{name:'AAA · HOSE'});
  expect(screen.getByText(/Historical candles are stored with provider provenance/)).toBeDefined();
  expect(screen.getByText(/No daily candle snapshot is saved\. Sync requires approval for exact SSI access and storage rights/)).toBeDefined();
  expect(fetcher).toHaveBeenCalledWith('/api/v1/engine/market/instruments?provider_id=ssi',expect.any(Object));
  expect(echarts.init).not.toHaveBeenCalled();
 });

 it('shows SSI index catalogue records as indexes without treating them as equities',async()=>{
  const providerIndex:Instrument={id:'SSI:INDEX:HOSE:VN30',venue:'HOSE',board:'unknown',native_symbol:'VN30',instrument_class:'index',name:'VN30',metadata:{index_code:'VN30',exchange:'HOSE'},is_synthetic:false};
  const fetcher=vi.fn(async(input:RequestInfo|URL)=>{
   const url=String(input);
   const value=url.includes('/market/datasets')?[{provider_id:'ssi',dataset:'instruments.index',snapshot_id:'indices-1'}]:url.includes('/instruments?provider_id=ssi')?[providerIndex]:url.includes('/providers/routing')?{datasets:{}}:url.includes('/instruments')?instruments:snapshot;
   return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
  });
  vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('option',{name:'SSI'});
  fireEvent.change(await screen.findByLabelText('Instrument source'),{target:{value:'ssi'}});
  await screen.findByRole('option',{name:'VN30 · HOSE'});
  expect(await screen.findByText(/HOSE membership can be saved as an observed snapshot/)).toBeDefined();
  expect(screen.queryByRole('img',{name:'Candlestick chart; data table below'})).toBeNull();
 });

 it('shows HNX index identities with their actual venue',async()=>{
  const providerIndex:Instrument={id:'SSI:INDEX:HNX:HNX30',venue:'HNX',board:'unknown',native_symbol:'HNX30',instrument_class:'index',name:'HNX 30',metadata:{index_code:'HNX30',exchange:'HNX'},is_synthetic:false};
  const fetcher=vi.fn(async(input:RequestInfo|URL)=>{
   const url=String(input);
   const value=url.includes('/market/datasets')?[{provider_id:'ssi',dataset:'instruments.index',snapshot_id:'hnx-indices-1'}]:url.includes('/instruments?provider_id=ssi')?[providerIndex]:url.includes('/providers/routing')?{datasets:{}}:url.includes('/instruments')?instruments:snapshot;
   return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
  });
  vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('option',{name:'SSI'});
  fireEvent.change(await screen.findByLabelText('Instrument source'),{target:{value:'ssi'}});
  expect(await screen.findByRole('option',{name:'HNX30 · HNX'})).toBeDefined();
  expect(await screen.findByText('Index catalogue entry is available for browsing. Daily index observations are not implemented yet.')).toBeDefined();
 });

 it('syncs and displays an observed SSI HOSE constituent snapshot',async()=>{
  const providerIndex:Instrument={id:'SSI:INDEX:HOSE:VN30',venue:'HOSE',board:'unknown',native_symbol:'VN30',instrument_class:'index',name:'VN30',metadata:{index_code:'VN30',exchange:'HOSE'},is_synthetic:false};
  let synced=false;
  const fetcher=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
   const url=String(input);
   let value:unknown=[];
   if(url.includes('/market/datasets'))value=synced?[{provider_id:'ssi',dataset:'instruments.index',snapshot_id:'hose-indices-1'},{provider_id:'ssi',dataset:'indices.constituents',snapshot_id:'hose-members-1'}]:[{provider_id:'ssi',dataset:'instruments.index',snapshot_id:'hose-indices-1'}];
   else if(url.includes('/providers/routing'))value={datasets:{'indices.constituents:index:HOSE':'ssi:market-data:indices.constituents:index:HOSE'}};
   else if(url.includes('/instruments?provider_id=ssi'))value=[providerIndex];
   else if(url.includes('/ingestion/index-constituents/ssi/hose')&&init?.method==='POST'){synced=true;value={job:{status:'completed'},snapshot_id:'feed0123456789ab'};}
   else if(url.includes('/market/provider-index-constituents'))value={snapshot_id:'hose-members-1',index:providerIndex,observed_at:'2026-10-27T02:00:00Z',constituents:{index_instrument_id:providerIndex.id,index_code:'VN30',index_name:'VN30',exchange:'HOSE',reported_total_symbol_count:1,constituents:[{provider_security_id:'ACB',native_symbol:'ACB'}],source_id:'SSI-FC-DATA',observed_at:'2026-10-27T02:00:00Z'}};
   else if(url.includes('/instruments'))value=instruments;
   else value=snapshot;
   return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
  });
  vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('option',{name:'SSI'});
  fireEvent.change(await screen.findByLabelText('Instrument source'),{target:{value:'ssi'}});
  expect(await screen.findByText(/historical effective dates are not inferred/)).toBeDefined();
  fireEvent.click(await screen.findByRole('button',{name:'Sync SSI HOSE constituents'}));
  await screen.findByText('SSI HOSE constituent snapshot saved as feed01234567.');
  expect(await screen.findByRole('region',{name:'SSI HOSE index constituents'})).toBeDefined();
  expect(screen.getAllByText('ACB')).toHaveLength(2);
  expect(screen.getByText(/Provider reports 1 members\. This is the observed membership set at/)).toBeDefined();
  const requestCall=fetcher.mock.calls.find(([url,init])=>String(url).includes('/ingestion/index-constituents/ssi/hose')&&init?.method==='POST');
  expect(requestCall).toBeDefined();
  expect(JSON.parse(String(requestCall?.[1]?.body))).toEqual({index_instrument_id:providerIndex.id});
 });

 it('syncs SSI daily candles for the selected HOSE instrument and displays the stored snapshot',async()=>{
  const providerInstrument:Instrument={id:'SSI:ISIN-AAA',venue:'HOSE',board:'unknown',native_symbol:'AAA',instrument_class:'equity',name:'Provider AAA',currency:'unknown',is_synthetic:false};
  const providerSnapshot:Snapshot={...snapshot,snapshot_id:'ssi-daily-snapshot',instrument:providerInstrument,quality:{state:'partial',gaps:[],adjustment:'unknown',calendar:'provider availability and exchange calendar unverified'},candles:candles.map(candle=>({...candle,currency:'unknown',price_unit:'unknown',volume_unit:'unknown',source_id:'SSI-FC-DATA'}))};
  let synced=false;
  const fetcher=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
   const url=String(input);
   let value:unknown=[];
   if(url.includes('/market/datasets'))value=synced?[{provider_id:'ssi',dataset:'instruments.details',snapshot_id:'catalogue-1'},{provider_id:'ssi',dataset:'candles.1d',snapshot_id:'daily-1'}]:[{provider_id:'ssi',dataset:'instruments.details',snapshot_id:'catalogue-1'}];
   else if(url.includes('/providers/routing'))value={datasets:{'candles.1d:equity:HOSE':'ssi:market-data:candles.1d:equity:HOSE'}};
   else if(url.includes('/instruments?provider_id=ssi'))value=[providerInstrument];
   else if(url.includes('/market/provider-candles'))value=providerSnapshot;
   else if(url.includes('/ingestion/candles/ssi/hose-equity/daily')&&init?.method==='POST'){synced=true;value={job:{status:'completed'},snapshot_id:'abcdef0123456789'};}
   else if(url.includes('/instruments'))value=instruments;
   else value=snapshot;
   return new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}});
  });
  vi.stubGlobal('fetch',fetcher);
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('option',{name:'SSI'});
  fireEvent.change(await screen.findByLabelText('Instrument source'),{target:{value:'ssi'}});
  const sync=await screen.findByRole('button',{name:'Sync SSI daily candles'});
  fireEvent.click(sync);
  await screen.findByText('SSI daily candles saved as snapshot abcdef012345.');
  await screen.findByRole('img',{name:'Candlestick chart; data table below'});
  const requestCall=fetcher.mock.calls.find(([url,init])=>String(url).includes('/ingestion/candles/ssi/hose-equity/daily')&&init?.method==='POST');
  expect(requestCall).toBeDefined();
  const requestBody=JSON.parse(String(requestCall?.[1]?.body));
  expect(requestBody).toMatchObject({instrument_id:'SSI:ISIN-AAA'});
  expect(requestBody.from_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  expect(requestBody.to_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  expect(screen.getByText(/not enabled for simulation/)).toBeDefined();
 });

 it('surfaces stale and incomplete snapshot quality details',async()=>{
  showMarket(url=>url.includes('/market/datasets')?[]:url.includes('/instruments')?instruments:{...snapshot,quality:{state:'partial',gaps:['2026-10-17T02:00:00Z/2026-10-18T02:00:00Z'],adjustment:'unknown',calendar:'provider-calendar',provisional_count:1}});
  expect(await screen.findByText(/Snapshot quality is partial\. Gaps: 2026-10-17T02:00:00Z\/2026-10-18T02:00:00Z\. 1 provisional bars are excluded/)).toBeDefined();
  expect(screen.getByText(/Quality: partial · Gaps: 1 · Provisional: 1 · Adjustment: unknown · Calendar: provider-calendar/)).toBeDefined();
 });

 it('keeps API errors visible and does not create a chart',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('market unavailable',{status:503})));
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('alert');
  expect(echarts.init).not.toHaveBeenCalled();
 });
});
