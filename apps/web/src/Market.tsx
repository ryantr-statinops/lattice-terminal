import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {init,use} from 'echarts/core';
import type {EChartsOption} from 'echarts';
import {CandlestickChart} from 'echarts/charts';
import {AxisPointerComponent,DataZoomInsideComponent,GridComponent,TooltipComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import {request,type Candle,type Instrument,type Snapshot} from './api';
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
 useEffect(()=>{if(!instance.current)return;const {dataZoom,...option}=chartOption(candles,appearance);instance.current.setOption(configured.current?option:{...option,dataZoom});configured.current=true},[candles,appearance]);
 return <div role="img" aria-label="Biểu đồ nến tổng hợp; bảng dữ liệu ở dưới" ref={container} style={{height:360,width:'100%'}}/>;
}

export function Market(){
 const instruments=useQuery({queryKey:['instruments'],queryFn:()=>request<Instrument[]>('/engine/market/instruments')});
 const [selected,setSelected]=useState('');
 const [watchlist,setWatchlist]=useState<string[]>(()=>{try{return JSON.parse(localStorage.getItem('kestrel.watchlist')||'[]')}catch{return []}});
 const id=selected||instruments.data?.[0]?.id||'';
 const data=useQuery({queryKey:['candles',id],queryFn:()=>request<Snapshot>('/engine/market/candles?instrument_id='+encodeURIComponent(id)),enabled:!!id});
 const toggle=()=>{const next=watchlist.includes(id)?watchlist.filter(v=>v!==id):[...watchlist,id];setWatchlist(next);localStorage.setItem('kestrel.watchlist',JSON.stringify(next))};
 return <section><div className="page-title"><div><small>MARKET / EQUITIES</small><h1>Thị trường</h1></div><span className="badge">SYNTHETIC-FIXTURE</span></div>
 <div className="toolbar"><select aria-label="Instrument" value={id} onChange={e=>setSelected(e.target.value)}>{instruments.data?.map(v=><option value={v.id} key={v.id}>{v.native_symbol} · {v.venue}</option>)}</select><button disabled={!id} onClick={toggle}>{watchlist.includes(id)?'★ Đã theo dõi':'☆ Theo dõi'}</button><button onClick={()=>data.refetch()}>Làm mới</button></div>
 <p className="muted">Dữ liệu tổng hợp dùng để phát triển. SSI chưa được cấp quyền vận hành; không phải dữ liệu thị trường thật.</p>
 {(instruments.isPending||data.isFetching)&&<p role="status">Đang đọc snapshot…</p>}
 {(instruments.error||data.error)&&<p role="alert" className="error">{(instruments.error||data.error)?.message}</p>}
 {data.data&&<><div className="panel"><div className="panel-heading"><strong>{data.data.instrument.name}</strong><span>{data.data.quality.state} · {data.data.candles.length} daily bars</span></div>{data.data.candles.length?<Chart candles={data.data.candles}/>:<p>Snapshot không có nến.</p>}</div>
 <p className="muted numeric">Snapshot {data.data.snapshot_id.slice(0,16)} · Adjustment: {data.data.quality.adjustment}<br/>As-of {data.data.candles.at(-1)?.available_at?new Date(data.data.candles.at(-1)!.available_at).toLocaleString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})+' ICT':'unavailable'}</p>
 <p className="muted">Gaps: {data.data.quality.gaps.length?data.data.quality.gaps.join(', '):'Không có trong fixture; chưa xác minh calendar thật'}</p><div className="panel"><table><caption>Nến gần nhất — giá và volume tổng hợp</caption><thead><tr>{['Ngày','Open','High','Low','Close','Volume'].map(v=><th key={v}>{v}</th>)}</tr></thead><tbody>{data.data.candles.slice(-10).map(v=><tr key={v.open_time}><td>{new Date(v.open_time).toLocaleDateString('vi-VN',{timeZone:'Asia/Ho_Chi_Minh'})}</td>{[v.open,v.high,v.low,v.close,v.volume].map((n,i)=><td className="numeric" key={i}>{n===null?'unavailable':Number(n).toLocaleString('vi-VN')}</td>)}</tr>)}</tbody></table></div></>}
 </section>
}
