import {Plot} from '../Plot';
import {DataTable} from '../ui/data';
import {EmptyState} from '../ui/feedback';
export type RunEvent={seq:number;type:string;payload:Record<string,unknown>;created_at:string};
function StrategySignalOutput({signal}:{signal:Record<string,unknown>}){
 const action=String(signal.action??'custom').toUpperCase();
 const instrument=String(signal.instrument_id??'Unknown instrument');
 const priceContext=signal.price_context&&typeof signal.price_context==='object'?signal.price_context:{};
 return <article className="run-signal" aria-label="Strategy signal" style={{padding:10,background:'var(--raised)',border:'1px solid var(--border)',borderRadius:4}}>
  <header style={{display:'flex',justifyContent:'space-between',alignItems:'center',gap:8}}><strong>{action}{typeof signal.custom_action==='string'?` · ${signal.custom_action}`:''} · {instrument}</strong><span className="badge">{String(signal.source??'unknown').toUpperCase()}</span></header>
  <p style={{margin:'8px 0'}}>{String(signal.reason??'')}</p>
  <dl style={{display:'grid',gridTemplateColumns:'minmax(82px,auto) 1fr',gap:'4px 8px',margin:'8px 0',fontSize:11}}>
   <dt style={{color:'var(--secondary)'}}>Event time</dt><dd style={{margin:0,overflowWrap:'anywhere'}}>{String(signal.event_time??'unknown')}</dd>
   <dt style={{color:'var(--secondary)'}}>Expires</dt><dd style={{margin:0,overflowWrap:'anywhere'}}>{String(signal.expires_at??'unknown')}</dd>
   <dt style={{color:'var(--secondary)'}}>Logical key</dt><dd style={{margin:0,overflowWrap:'anywhere'}}>{String(signal.logical_key??'')}</dd>
   {typeof signal.correlation_id==='string'&&signal.correlation_id.length>0&&<><dt style={{color:'var(--secondary)'}}>Correlation</dt><dd style={{margin:0,overflowWrap:'anywhere'}}>{signal.correlation_id}</dd></>}
  </dl>
  {Object.keys(priceContext).length>0&&<pre aria-label="Signal price context" style={{maxHeight:120,overflow:'auto'}}>{JSON.stringify(priceContext,null,2)}</pre>}
 </article>
}
export function RunOutput({events,runID}:{events:RunEvent[];runID:string}){return !runID||!events.length?<EmptyState>No output for the selected run.</EmptyState>:<>{events.map(event=>{const p=event.payload;let output;if(event.type==='signal')output=<StrategySignalOutput signal={p}/>;else if(event.type==='artifact'&&typeof p.name==='string')output=<a download href={'/api/v1/runs/'+encodeURIComponent(runID)+'/artifacts/'+encodeURIComponent(p.name)}>Download artifact: {p.name}</a>;else if(event.type==='table'&&Array.isArray(p.columns)&&Array.isArray(p.rows)){const columns=p.columns;output=<DataTable<{row:unknown;index:number}> caption={String(p.name||'Table')} rows={p.rows.slice(0,500).map((row,index)=>({row,index}))} rowKey={v=>String(v.index)} columns={columns.map((label,i)=>({key:String(i),label:String(label),render:v=>Array.isArray(v.row)?v.row[i]===null?'unavailable':String(v.row[i]??''):''}))}/>;}else if(event.type==='chart'&&Array.isArray(p.x)&&Array.isArray(p.y))output=<Plot title={String(p.name||'Chart')} data={[{type:'scatter',mode:'lines',x:p.x,y:p.y,connectgaps:false}]}/>;else output=<pre className={event.type==='error'?'error':''}>{typeof p.message==='string'?p.message:JSON.stringify(p,null,2)}</pre>;return <div key={event.seq} className="run-output">{output}</div>})}</>}
