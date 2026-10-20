import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {init,use} from 'echarts/core';
import type {EChartsOption} from 'echarts';
import {CandlestickChart} from 'echarts/charts';
import {AxisPointerComponent,DataZoomInsideComponent,GridComponent,TooltipComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import {request,type Candle,type Instrument,type Snapshot} from './api';
import {PageHeader,Panel,PanelHeader,Toolbar} from './ui/layout';
import {Button} from './ui/buttons';
import {Select} from './ui/fields';
import {DataTable,NumericValue,SourceMetadata,StatusLabel} from './ui/data';
import {EmptyState,ErrorState,InlineNotice,LoadingState} from './ui/feedback';
import {useAppearance} from './theme/store';
import {fontFamilies} from './theme/tokens';
import type {AppearancePreferences} from './theme/preferences';

use([CandlestickChart,AxisPointerComponent,DataZoomInsideComponent,GridComponent,TooltipComponent,CanvasRenderer]);

const vietnamDate=new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric',timeZone:'Asia/Ho_Chi_Minh'});
const vietnamPrice=new Intl.NumberFormat('vi-VN',{maximumFractionDigits:2});

function chartOption(candles:Candle[],appearance:AppearancePreferences):EChartsOption{
 const c=appearance.colors;
 const labels=candles.map(candle=>vietnamDate.format(new Date(candle.open_time)));
 const values=candles.map(candle=>[
  Number(candle.open),
  Number(candle.close),
  Number(candle.low),
  Number(candle.high),
 ]);
 return {
  animation:false,
  textStyle:{fontFamily:fontFamilies[appearance.font],fontSize:appearance.fontSize},
  backgroundColor:c.panel,
  grid:{left:64,right:24,top:24,bottom:36,containLabel:false},
  tooltip:{
   trigger:'axis',
   axisPointer:{type:'cross',lineStyle:{color:c.secondary}},
   backgroundColor:c.raised,
   borderColor:c.border,
   textStyle:{color:c.text},
   formatter:(raw)=>{
    const item=Array.isArray(raw)?raw[0]:raw;
    if(!item||typeof item!=='object')return '';
    const row=item as {axisValueLabel?:string;value?:unknown;data?:unknown};
    const source=row.value??row.data;
    const ohlc=Array.isArray(source)?source:source&&typeof source==='object'&&'value'in source?(source as {value?:unknown}).value:undefined;
    if(!Array.isArray(ohlc)||ohlc.length<4)return row.axisValueLabel??'';
    const [open,close,low,high]=ohlc.map(Number);
    return `${row.axisValueLabel??''}<br/>Open: ${vietnamPrice.format(open)}<br/>High: ${vietnamPrice.format(high)}<br/>Low: ${vietnamPrice.format(low)}<br/>Close: ${vietnamPrice.format(close)}`;
   },
  },
  xAxis:{
   type:'category',
   data:labels,
   boundaryGap:true,
   axisLine:{lineStyle:{color:c.borderStrong}},
   axisTick:{show:false},
   axisLabel:{color:c.muted,hideOverlap:true},
  },
  yAxis:{
   type:'value',
   scale:true,
   axisLine:{show:false},
   axisTick:{show:false},
   axisLabel:{color:c.muted,formatter:(value:number)=>vietnamPrice.format(value)},
   splitLine:{lineStyle:{color:c.border}},
  },
  dataZoom:[{type:'inside',xAxisIndex:0,zoomOnMouseWheel:true,moveOnMouseMove:true,moveOnMouseWheel:false}],
  series:[{
   type:'candlestick',
   name:'OHLC',
   data:values,
   itemStyle:{color:c.positive,color0:c.negative,borderColor:c.positive,borderColor0:c.negative,borderWidth:1},
  }],
 };
}

function Chart({candles}:{candles:Candle[]}){
 const container=useRef<HTMLDivElement>(null),instance=useRef<ReturnType<typeof init>|null>(null),configured=useRef(false);
 const appearance=useAppearance();
 useEffect(()=>{const element=container.current;if(!element)return;const chart=init(element,undefined,{renderer:'canvas'});instance.current=chart;configured.current=false;const resize=new ResizeObserver(([entry])=>{if(entry.contentRect.width>0)chart.resize({width:entry.contentRect.width})});resize.observe(element);return()=>{resize.disconnect();chart.dispose();instance.current=null}},[]);
 useEffect(()=>{if(!instance.current)return;let alive=true;const {dataZoom,...option}=chartOption(candles,appearance);instance.current.setOption(configured.current?option:{...option,dataZoom});configured.current=true;void document.fonts?.load(`${appearance.fontSize}px ${fontFamilies[appearance.font]}`).then(()=>{if(alive)instance.current?.resize()});return()=>{alive=false}},[candles,appearance]);
 return <div role="img" aria-label="Synthetic candlestick chart; data table below" ref={container} style={{height:360,width:'100%'}}/>;
}

export function Market(){
 const instruments=useQuery({queryKey:['instruments'],queryFn:()=>request<Instrument[]>('/engine/market/instruments')});
 const [selected,setSelected]=useState(''),[notice,setNotice]=useState('');
 const [watchlist,setWatchlist]=useState<string[]>(()=>{try{const saved=JSON.parse(localStorage.getItem('kestrel.watchlist')||'[]');return Array.isArray(saved)?saved.filter((v:unknown)=>typeof v==='string'):[]}catch{return []}});
 const id=selected||instruments.data?.[0]?.id||'';
 const data=useQuery({queryKey:['candles',id],queryFn:()=>request<Snapshot>('/engine/market/candles?instrument_id='+encodeURIComponent(id)),enabled:!!id});
 const toggle=()=>{const next=watchlist.includes(id)?watchlist.filter(v=>v!==id):[...watchlist,id];setWatchlist(next);try{localStorage.setItem('kestrel.watchlist',JSON.stringify(next));setNotice('')}catch{setNotice('Watchlist changes are saved for this session only.')}};
 const snapshot=data.data;
 return <section><PageHeader eyebrow="MARKET / EQUITIES" title="Market" actions={<StatusLabel tone="warning">SYNTHETIC-FIXTURE</StatusLabel>}/>
 <Toolbar><Select aria-label="Instrument" value={id} disabled={instruments.isPending||!instruments.data?.length} onChange={e=>setSelected(e.target.value)}>{instruments.data?.map(v=><option value={v.id} key={v.id}>{v.native_symbol} · {v.venue}</option>)}</Select><Button disabled={!id} aria-pressed={watchlist.includes(id)} onClick={toggle}>{watchlist.includes(id)?'★ Watching':'☆ Watch'}</Button><Button disabled={!id} pending={data.isFetching} onClick={()=>void data.refetch()}>Refresh</Button></Toolbar>
 <SourceMetadata>Synthetic data for development. SSI is not authorized for production use; this is not live market data.</SourceMetadata>
 {notice&&<InlineNotice tone="warning">{notice}</InlineNotice>}{(instruments.isPending||data.isFetching)&&<LoadingState>Loading snapshot…</LoadingState>}<ErrorState error={instruments.error||data.error} onRetry={()=>{void instruments.refetch();if(id)void data.refetch()}}/>
 {!instruments.isPending&&!instruments.error&&!instruments.data?.length&&<EmptyState>No instruments are available.</EmptyState>}
 {snapshot&&<><Panel><PanelHeader title={snapshot.instrument.name} actions={<span>{snapshot.quality.state} · {snapshot.candles.length} daily bars</span>}/>{snapshot.candles.length?<Chart candles={snapshot.candles}/>:<EmptyState>This snapshot has no candles.</EmptyState>}</Panel>
 <SourceMetadata>Snapshot {snapshot.snapshot_id.slice(0,16)} · Adjustment: {snapshot.quality.adjustment}<br/>As-of {snapshot.candles.at(-1)?.available_at?new Date(snapshot.candles.at(-1)!.available_at).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})+' ICT':'unavailable'}<br/>Gaps: {snapshot.quality.gaps.length?snapshot.quality.gaps.join(', '):'Not included in fixture; live calendar not verified'}</SourceMetadata>
 <Panel><DataTable caption="Latest candles — synthetic prices and volume" rows={snapshot.candles.slice(-10)} rowKey={v=>v.open_time} columns={[{key:'date',label:'Date',render:v=>new Date(v.open_time).toLocaleDateString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})},...(['open','high','low','close','volume'] as const).map(key=>({key,label:key.toUpperCase(),numeric:true,render:(v:Candle)=><NumericValue value={v[key]}/>}))]}/></Panel></>}
 </section>;
}
