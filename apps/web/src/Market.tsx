import {useEffect,useRef,useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {ColorType,createChart,type UTCTimestamp} from 'lightweight-charts';
import {request,type Candle,type Instrument,type Snapshot} from './api';
import {useTheme} from './theme';

function Chart({candles}:{candles:Candle[]}){
 const container=useRef<HTMLDivElement>(null);
 const theme=useTheme();
 useEffect(()=>{if(!container.current)return;const chart=createChart(container.current,{height:360,layout:{background:{type:ColorType.Solid,color:theme==='light'?'#f5f8fa':'#0b1017'},textColor:theme==='light'?'#364657':'#91a4b8'},grid:{vertLines:{color:theme==='light'?'#d7e0e6':'#1b2532'},horzLines:{color:theme==='light'?'#d7e0e6':'#1b2532'}}});const series=chart.addCandlestickSeries({upColor:'#61c6a6',downColor:'#ee8391',borderVisible:false,wickUpColor:'#61c6a6',wickDownColor:'#ee8391'});series.setData(candles.map(v=>({time:Math.floor(Date.parse(v.open_time)/1000) as UTCTimestamp,open:Number(v.open),high:Number(v.high),low:Number(v.low),close:Number(v.close)})));chart.timeScale().fitContent();const resize=new ResizeObserver(([entry])=>chart.applyOptions({width:entry.contentRect.width}));resize.observe(container.current);return()=>{resize.disconnect();chart.remove()}},[candles,theme]);
 return <div role="img" aria-label="Biểu đồ nến tổng hợp; bảng dữ liệu ở dưới" ref={container}/>;
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
