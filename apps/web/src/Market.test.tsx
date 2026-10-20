// @vitest-environment jsdom
import {afterEach,beforeEach,describe,expect,it,vi} from 'vitest';
import {act,cleanup,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';

const echarts=vi.hoisted(()=>{
 const instance={setOption:vi.fn(),resize:vi.fn(),dispose:vi.fn()};
 return {instance,init:vi.fn(()=>instance),use:vi.fn()};
});
vi.mock('echarts/core',()=>({init:echarts.init,use:echarts.use}));
vi.mock('echarts/charts',()=>({CandlestickChart:'candlestick-chart'}));
vi.mock('echarts/components',()=>({AxisPointerComponent:'axis-pointer',DataZoomInsideComponent:'inside-data-zoom',GridComponent:'grid',TooltipComponent:'tooltip'}));
vi.mock('echarts/renderers',()=>({CanvasRenderer:'canvas-renderer'}));

import {Market} from './Market';
import {setColor,resetAppearance} from './theme/store';
import type {Candle,Instrument,Snapshot} from './api';

const instruments:Instrument[]=[{id:'VN:SYN01',venue:'HOSE',native_symbol:'SYN01',name:'Synthetic One',is_synthetic:true}];
const candles:Candle[]=[
 {open_time:'2026-10-19T02:00:00Z',close_time:'2026-10-19T09:00:00Z',available_at:'2026-10-19T09:00:00Z',open:'100',high:'112',low:'99',close:'110',volume:'1200',is_closed:true},
 {open_time:'2026-10-20T02:00:00Z',close_time:'2026-10-20T09:00:00Z',available_at:'2026-10-20T09:00:00Z',open:'110',high:'115',low:'108',close:'109',volume:'1500',is_closed:true},
];
const snapshot:Snapshot={snapshot_id:'fixture-market-snapshot',instrument:instruments[0],quality:{state:'complete',gaps:[],adjustment:'unadjusted'},candles};
let resizeCallback:ResizeObserverCallback|undefined;

class TestResizeObserver{
 constructor(callback:ResizeObserverCallback){resizeCallback=callback}
 observe=vi.fn();
 disconnect=vi.fn();
}

function showMarket(response=(url:string)=>url.includes('/instruments')?instruments:snapshot){
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
  await screen.findByRole('img',{name:'Synthetic candlestick chart; data table below'});
  await waitFor(()=>expect(echarts.instance.setOption).toHaveBeenCalledOnce());
  const option=echarts.instance.setOption.mock.calls[0][0] as {series:{type:string;data:number[][]}[];xAxis:{data:string[]};dataZoom:{type:string}[];tooltip:{axisPointer:{type:string};formatter:(params:unknown)=>string}};
  expect(option.series[0].type).toBe('candlestick');
  expect(option.series[0].data).toEqual([[100,110,99,112],[110,109,108,115]]);
  expect(option.xAxis.data).toEqual(['19/10/2026','20/10/2026']);
  expect(option.dataZoom[0]).toMatchObject({type:'inside',zoomOnMouseWheel:true,moveOnMouseMove:true});
  expect(option.tooltip.axisPointer.type).toBe('cross');
  expect(option.tooltip.formatter([{axisValueLabel:'20/10/2026',value:[110,109,108,115]}])).toContain('High: 115');
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
  showMarket(url=>url.includes('/instruments')?instruments:{...snapshot,candles:[]});
  await screen.findByText('This snapshot has no candles.');
  expect(echarts.init).not.toHaveBeenCalled();
 });

 it('keeps API errors visible and does not create a chart',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>new Response('market unavailable',{status:503})));
  render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Market/></QueryClientProvider>);
  await screen.findByRole('alert');
  expect(echarts.init).not.toHaveBeenCalled();
 });
});
