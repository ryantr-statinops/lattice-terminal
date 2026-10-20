// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {act,cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Workspace} from './Workspace';
import {request,send} from './api';
vi.mock('./api',()=>({request:vi.fn(),send:vi.fn()}));
vi.mock('./CodeEditor',()=>({default:({value,onChange}:{value:string;onChange:(s:string)=>void})=><textarea aria-label="Editor content" value={value} onChange={e=>onChange(e.target.value)}/>}));
class Observer{observe(){}disconnect(){}}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.clearAllMocks()});
it('keeps unsaved buffers across file switches and scopes the save shortcut',async()=>{
 vi.stubGlobal('ResizeObserver',Observer);vi.mocked(request).mockImplementation(async path=>path==='/workspaces/research'?[{path:'a.py',directory:false},{path:'b.py',directory:false}]:path.includes('/file?')?{content:path.includes('a.py')?'original A':'original B'}:[]);vi.mocked(send).mockResolvedValue({});
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Workspace kind="research" title="Research"/></QueryClientProvider>);
 fireEvent.click(await screen.findByRole('treeitem',{name:/a.py/}));const editor=await screen.findByLabelText('Editor content');fireEvent.change(editor,{target:{value:'edited A'}});
 fireEvent.click(screen.getByRole('treeitem',{name:/b.py/}));await waitFor(()=>expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('original B'));
 fireEvent.click(screen.getByRole('treeitem',{name:/a.py/}));await waitFor(()=>expect((screen.getByLabelText('Editor content') as HTMLTextAreaElement).value).toBe('edited A'));
 await waitFor(()=>expect((screen.getByRole('button',{name:'Lưu'}) as HTMLButtonElement).disabled).toBe(false));
 fireEvent.keyDown(screen.getByLabelText('Editor content'),{key:'s',ctrlKey:true});await waitFor(()=>expect(send).toHaveBeenCalledWith('/workspaces/research/file',{Path:'a.py',Content:'edited A',Directory:false},'PUT'));
});
it('keeps Stop disabled once the service reports stopping despite an older running event',async()=>{
 let state='running';let stream:Stream|undefined;
 class Stream{listeners:Record<string,(event:unknown)=>void>={};onerror=()=>{};constructor(){stream=this}addEventListener(type:string,listener:(event:unknown)=>void){this.listeners[type]=listener}close(){}}
 vi.stubGlobal('ResizeObserver',Observer);vi.stubGlobal('EventSource',Stream);
 vi.mocked(request).mockImplementation(async path=>path==='/workspaces/research'?[{path:'a.py',directory:false}]:path.includes('/file?')?{content:'original A'}:[{id:'live',file:'a.py',status:state,created_at:'2026-10-20T00:00:00Z'}]);
 vi.mocked(send).mockImplementation(async path=>{if(path==='/runs/live/stop')state='stopping';return {}});
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Workspace kind="research" title="Research"/></QueryClientProvider>);
 fireEvent.click(await screen.findByRole('treeitem',{name:/a.py/}));await screen.findByLabelText('Editor content');fireEvent.change(screen.getByLabelText('Run history'),{target:{value:'live'}});
 await waitFor(()=>expect(stream).toBeDefined());act(()=>stream!.listeners.run({data:JSON.stringify({seq:1,type:'state',payload:{status:'running'}})}));
 fireEvent.click(screen.getByRole('button',{name:'■ Stop'}));await waitFor(()=>expect(send).toHaveBeenCalledWith('/runs/live/stop',{}));await screen.findByText('stopping');expect((screen.getByRole('button',{name:'■ Stop'}) as HTMLButtonElement).disabled).toBe(true);
});
