import {useEffect,useRef,useState,type ReactNode} from 'react';
import {Link,NavLink,useLocation} from 'react-router-dom';
import {Button} from './buttons';
import {StatusLabel} from './data';
import {ErrorState} from './feedback';
import {TerminalDrawer} from '../terminal/TerminalDrawer';
const navigation=[['/market','Market'],['/quant','Quant'],['/backtest','Backtest'],['/strategies','Strategies'],['/assets','Assets / Funds'],['/portfolio','Portfolio'],['/settings','Settings']];
export function AppShell({children,onLock}:{children:ReactNode;onLock:()=>Promise<void>}){
  const [busy,setBusy]=useState(false),[error,setError]=useState<unknown>(null);
  const [terminalOpen,setTerminalOpen]=useState(false);
  const [navWidth,setNavWidth]=useState<number>(()=>{try{const saved=Number(localStorage.getItem('kestrel.nav.width'));if(Number.isFinite(saved)&&saved>=160&&saved<=360)return saved}catch{}return 205});
  const dragRef=useRef<{active:boolean;startX:number;startWidth:number}>({active:false,startX:0,startWidth:205});
  const sending=useRef(false);
  const {pathname}=useLocation();
  const updateNavWidth=(w:number)=>{const clamped=Math.max(160,Math.min(360,w));setNavWidth(clamped);try{localStorage.setItem('kestrel.nav.width',String(clamped))}catch{}};
  useEffect(()=>{window.scrollTo(0,0);document.getElementById('main-content')?.focus({preventScroll:true})},[pathname]);
  useEffect(()=>{const handleKey=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key==='`'){e.preventDefault();setTerminalOpen(o=>!o)}};window.addEventListener('keydown',handleKey);return()=>window.removeEventListener('keydown',handleKey)},[]);
  return <div className="app-shell" style={{['--nav-width' as string]:`${navWidth}px`}}><a className="skip-link" href="#main-content">Skip to main content</a><aside className="app-nav"><div className="wordmark"><span className="brand-symbol">K</span><span>KESTREL<small>TERMINAL</small></span></div><nav aria-label="Main navigation">{navigation.map(([to,label])=><NavLink key={to} to={to}>{label}</NavLink>)}</nav><div className="nav-bottom"><StatusLabel tone="warning">LOCAL · FIXTURE</StatusLabel><Button pending={busy} onClick={async()=>{if(sending.current)return;sending.current=true;setBusy(true);setError(null);try{await onLock()}catch(e){setError(e)}finally{sending.current=false;setBusy(false)}}}>Lock session</Button><ErrorState error={error}/></div><div role="separator" tabIndex={0} aria-orientation="vertical" aria-label="Resize navigation sidebar" aria-valuenow={Math.round(navWidth)} aria-valuemin={160} aria-valuemax={360} className="nav-resize-handle" title="Drag to resize sidebar, double-click to reset" onDoubleClick={()=>updateNavWidth(205)} onPointerDown={e=>{e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);dragRef.current={active:true,startX:e.clientX,startWidth:navWidth}}} onPointerMove={e=>{if(!dragRef.current.active)return;updateNavWidth(dragRef.current.startWidth+(e.clientX-dragRef.current.startX))}} onPointerUp={e=>{dragRef.current.active=false;try{e.currentTarget.releasePointerCapture(e.pointerId)}catch{}}} onKeyDown={e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();updateNavWidth(navWidth+(e.key==='ArrowRight'?8:-8))}}}/></aside><div className="app-body"><header className="app-header"><span>Research workspace</span><div className="header-actions"><span className="muted">SSI production blocked · VND</span><Link to="/settings#appearance">Appearance</Link></div></header><main id="main-content" tabIndex={-1} style={{paddingBottom:40}}>{children}</main></div><TerminalDrawer open={terminalOpen} onToggle={()=>setTerminalOpen(o=>!o)}/></div>
}
