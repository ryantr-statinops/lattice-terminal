import {lazy,Suspense,useEffect,useRef,useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send} from './api';
import {RunHistory} from './workspace/RunHistory';
import {useRunEvents} from './workspace/useRunEvents';
import {RunOutput} from './workspace/RunOutput';
import {programTemplate} from './templates';
import {FileTree} from './workspace/FileTree';
import {WorkspaceToolbar} from './workspace/WorkspaceToolbar';
import {PageHeader} from './ui/layout';
import {StatusLabel} from './ui/data';
import {useActionDialog} from './ui/dialogs';
import {ResizablePaneGroup} from './ui/ResizablePaneGroup';
import {EditorBoundary} from './ui/EditorBoundary';
import {ErrorState,LoadingState,Toast} from './ui/feedback';
const CodeEditor=lazy(()=>import('./CodeEditor'));
export type WorkspaceKind='research'|'backtest'|'strategy';
type File={path:string;directory:boolean};
type Run={id:string;kind:string;file:string;status:string;created_at:string;params:Record<string,unknown>};

const memory=new Map<string,{buffers:Record<string,string>;saved:Record<string,string>}>();

export function Workspace({kind,title,controls,extraParams={},runBlockedReason}:{kind:WorkspaceKind;title:string;controls?:React.ReactNode;extraParams?:Record<string,unknown>;runBlockedReason?:string}){
 const dialog=useActionDialog();const sending=useRef(false);const [success,setSuccess]=useState('');
 const client=useQueryClient();const state=memory.get(kind)||{buffers:{},saved:{}};memory.set(kind,state);
 const [buffers,setBuffers]=useState(state.buffers);const [saved,setSaved]=useState(state.saved);const [active,setActive]=useState('');const [error,setError]=useState('');const [params,setParams]=useState('{}');const [runID,setRunID]=useState('');const {events,connection}=useRunEvents(runID,kind);const [busy,setBusy]=useState(false);const [collapsed,setCollapsed]=useState(new Set<string>());
 const files=useQuery({queryKey:['files',kind],queryFn:()=>request<File[]>('/workspaces/'+kind)});
 const file=useQuery({queryKey:['file',kind,active],enabled:!!active,queryFn:()=>request<{content:string}>(`/workspaces/${kind}/file?path=${encodeURIComponent(active)}`)});
 const runs=useQuery({queryKey:['runs',kind],queryFn:()=>request<Run[]>('/runs?kind='+kind),refetchInterval:3000});
 const content=buffers[active]??file.data?.content??'';
 const [detection,setDetection]=useState('auto');const [node,setNode]=useState<File|null>(null);const [diagnostic,setDiagnostic]=useState('');
 useEffect(()=>{if(!active.endsWith('.py')){setDiagnostic('');return}let stale=false;const timer=setTimeout(()=>{void send('/engine/programs/inspect',{source:content,kind,selected:detection==='selected'}).then(()=>{if(!stale)setDiagnostic('')}).catch((e:Error)=>{if(!stale)setDiagnostic(e.message)})},500);return()=>{stale=true;clearTimeout(timer)}},[active,content,kind,detection]);
 useEffect(()=>{if(active&&file.data&&saved[active]===undefined){const next={...saved,[active]:file.data.content};setSaved(next);state.saved=next}},[active,file.data,saved,state]);
 const update=(value:string)=>{const next={...buffers,[active]:value};setBuffers(next);state.buffers=next};
 useEffect(()=>{const dirty=Object.keys(buffers).some(v=>saved[v]!==undefined&&saved[v]!==buffers[v]);const before=(e:BeforeUnloadEvent)=>{if(dirty)e.preventDefault()};window.addEventListener('beforeunload',before);return()=>window.removeEventListener('beforeunload',before)},[buffers,saved]);

 const select=(path:string)=>{setActive(path);setNode({path,directory:false});setError('');setRunID('')};
 const save=async()=>{if(!active)throw Error('Chọn file trước');await send(`/workspaces/${kind}/file`,{Path:active,Content:content,Directory:false},'PUT');const next={...saved,[active]:content};setSaved(next);state.saved=next;await client.invalidateQueries({queryKey:['file',kind,active]})};
 const action=async(fn:()=>Promise<void>)=>{if(sending.current)return;sending.current=true;setError('');setBusy(true);try{await fn();setSuccess('Đã hoàn tất thao tác.')}catch(e){setError((e as Error).message)}finally{sending.current=false;setBusy(false)}};
 const executeRun=async()=>{const parsed=JSON.parse(params);if(!parsed||Array.isArray(parsed)||typeof parsed!=='object')throw Error('Parameters phải là JSON object');await save();const run=await send<Run>('/runs',{Kind:kind,File:active,Params:{...parsed,...extraParams,kind_detection:detection}});client.setQueryData<Run[]>(['runs',kind],old=>[run,...(old??[])]);setRunID(run.id);await client.invalidateQueries({queryKey:['runs',kind]})};
 const stopRun=async()=>{await send(`/runs/${runID}/stop`,{});client.setQueryData<Run[]>(['runs',kind],old=>old?.map(run=>run.id===runID?{...run,status:'stopping'}:run));await client.invalidateQueries({queryKey:['runs',kind]})};

 const create=(directory:boolean)=>dialog.show({title:directory?'Tạo thư mục':'Tạo file Python',fields:[{key:'path',label:'Đường dẫn tương đối',hint:directory?'Ví dụ: helpers':'Ví dụ: research.py'}],onSubmit:async values=>{const path=values.path.trim();if(!path)throw Error('Đường dẫn không được trống');if(!directory&&!path.endsWith('.py'))throw Error('File mới phải có đuôi .py');if(files.data?.some(v=>v.path===path))throw Error('Đường dẫn đã tồn tại');await send(`/workspaces/${kind}/file`,{Path:path,Content:directory?'':programTemplate(kind),Directory:directory},'PUT');await client.invalidateQueries({queryKey:['files',kind]});if(!directory)select(path)}});

 const rename=()=>{if(!node)return;const from=node.path;dialog.show({title:'Đổi tên '+from,fields:[{key:'to',label:'Đường dẫn mới',value:from}],onSubmit:async values=>{const to=values.to.trim();if(!to)throw Error('Tên mới không được trống');await send(`/workspaces/${kind}/rename`,{From:from,To:to});const remap=(items:Record<string,string>)=>Object.fromEntries(Object.entries(items).map(([key,value])=>[key===from||key.startsWith(from+'/')?to+key.slice(from.length):key,value]));const b=remap(buffers),savedNext=remap(saved);setBuffers(b);state.buffers=b;setSaved(savedNext);state.saved=savedNext;if(active===from||active.startsWith(from+'/'))setActive(to+active.slice(from.length));setNode({...node,path:to});await client.invalidateQueries({queryKey:['files',kind]})}})};
 const remove=()=>{if(!node)return;const target=node.path;dialog.show({title:'Xóa '+target,description:'Thư mục phải rỗng. Nội dung file chưa lưu sẽ bị bỏ. Thao tác này không dừng job đang chạy.',danger:true,onSubmit:async()=>{await request(`/workspaces/${kind}/file?path=${encodeURIComponent(target)}`,{method:'DELETE'});const b={...buffers},savedNext={...saved};delete b[target];delete savedNext[target];setBuffers(b);state.buffers=b;setSaved(savedNext);state.saved=savedNext;if(active===target)setActive('');setNode(null);await client.invalidateQueries({queryKey:['files',kind]})}})};
 const history=runs.data?.filter(v=>v.file===active)||[];
 const latestEvent=events.filter(v=>v.type==='state').at(-1);
 const historyStatus=runs.data?.find(v=>v.id===runID)?.status??'';const eventStatus=String(latestEvent?.payload.status??'');
 const runStatus=historyStatus==='stopping'&&!['completed','failed','cancelled','interrupted'].includes(eventStatus)?'stopping':eventStatus||historyStatus;
 let paramsError='';try{const parsed=JSON.parse(params);if(!parsed||Array.isArray(parsed)||typeof parsed!=='object')paramsError='Parameters phải là JSON object'}catch{paramsError='Parameters JSON chưa hợp lệ'}
 const canSave=!!active&&!busy&&!file.isFetching&&!file.error;
 const canRun=canSave&&active.endsWith('.py')&&!paramsError&&!runBlockedReason&&!diagnostic;
 const canStop=!!runID&&!busy&&['queued','running'].includes(runStatus);

 return <section className="workspace-page" onKeyDownCapture={event=>{if(!(event.ctrlKey||event.metaKey)||event.altKey||document.querySelector('dialog[open]'))return;if(event.key.toLowerCase()==='s'){event.preventDefault();if(canSave&&!event.repeat)void action(save)}else if(event.key==='Enter'){event.preventDefault();if(canRun&&!event.repeat)void action(executeRun)}}}><PageHeader eyebrow={'PYTHON / '+kind.toUpperCase()} title={title} actions={<StatusLabel tone="warning">LOCAL TRUSTED CODE</StatusLabel>}/>{controls}<WorkspaceToolbar kind={kind} active={active} dirty={buffers[active]!==undefined&&buffers[active]!==saved[active]} detection={detection} onDetection={setDetection} busy={busy} canSave={canSave} canRun={canRun} canStop={canStop} onSave={()=>void action(save)} onRun={()=>void action(executeRun)} onStop={()=>void action(stopRun)}/><p className="muted">Code chạy quyền Windows user, không sandbox. Chuyển file hoặc đóng trình duyệt không dừng job.</p>{error&&<p role="alert" className="error">{error}</p>}{diagnostic&&<p className="error">Entry diagnostics: {diagnostic}</p>}<ErrorState error={files.error||runs.error}/>{files.isPending&&<LoadingState>Đang đọc cây file…</LoadingState>}{(paramsError||runBlockedReason)&&<p className="muted">{paramsError||runBlockedReason}</p>}<Toast message={success} onDismiss={()=>setSuccess('')}/>
 <ResizablePaneGroup storageKey={'kestrel.panes.'+kind} left={left=><FileTree width={left} files={files.data??[]} active={active} selected={node?.path??''} buffers={buffers} saved={saved} collapsed={collapsed} busy={busy} onSelect={select} onDirectory={v=>{setNode(v);const next=new Set(collapsed);if(next.has(v.path))next.delete(v.path);else next.add(v.path);setCollapsed(next)}} onCreate={create} onRename={rename} onDelete={remove}/>} right={right=><aside className="results-pane" style={{width:right}}><h3>Runs / Kết quả</h3>{runID&&<div className="run-state"><StatusLabel tone={runStatus==='failed'?'negative':runStatus==='completed'?'positive':'info'}>{runStatus||'Đang đọc trạng thái…'}</StatusLabel></div>}{runID&&connection==='reconnecting'&&<p className="notice tone-warning" role="status">Kết nối kết quả bị gián đoạn; đang kết nối lại theo event ID. Job vẫn do local service quản lý.</p>}{runID&&connection==='connecting'&&<LoadingState>Đang kết nối output…</LoadingState>}<RunHistory runs={history} value={runID} onChange={setRunID}/><label className="muted">Parameters JSON<textarea aria-label="Parameters JSON" value={params} onChange={e=>setParams(e.target.value)}/></label><RunOutput events={events} runID={runID}/></aside>}>{active?(file.isPending&&buffers[active]===undefined?<LoadingState>Đang tải file…</LoadingState>:file.error?<ErrorState error={file.error} onRetry={()=>void file.refetch()}/>:<EditorBoundary key={kind+'/'+active}><Suspense fallback={<p>Đang nạp editor local…</p>}><CodeEditor path={kind+'/'+active} value={content} onChange={update} diagnostic={diagnostic}/></Suspense></EditorBoundary>):<p className="muted" style={{padding:24}}>Tạo file Python để bắt đầu.</p>}</ResizablePaneGroup>{dialog.element}</section>
}
