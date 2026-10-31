// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {act,cleanup,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {useRunEvents} from '@web/workspace/useRunEvents';
const streams:FakeStream[]=[];
class FakeStream{listeners:Record<string,(event:unknown)=>void>={};onerror=()=>{};close=vi.fn();constructor(){streams.push(this)}addEventListener(type:string,fn:(event:unknown)=>void){this.listeners[type]=fn}emit(seq:number,type='log',payload:Record<string,unknown>={message:'output'}){this.listeners.run({data:JSON.stringify({seq,type,payload})})}}
afterEach(()=>{cleanup();vi.unstubAllGlobals();streams.length=0});
it('retains deduplicated events across reconnect and isolates a newly selected run',()=>{vi.stubGlobal('EventSource',FakeStream);const client=new QueryClient();function Host({id}:{id:string}){const s=useRunEvents(id,'research');return <div>{s.connection}:{s.events.map(e=>e.seq).join(',')}</div>}const wrap=(id:string)=><QueryClientProvider client={client}><Host id={id}/></QueryClientProvider>;const view=render(wrap('a'));act(()=>{streams[0].emit(1);streams[0].emit(1);streams[0].onerror()});expect(screen.getByText('reconnecting:1')).toBeTruthy();act(()=>streams[0].emit(2,'state',{status:'completed'}));expect(screen.getByText('closed:1,2')).toBeTruthy();expect(streams[0].close).toHaveBeenCalledOnce();view.rerender(wrap('b'));expect(screen.getByText('connecting:')).toBeTruthy();act(()=>streams[0].emit(3));expect(screen.getByText('connecting:')).toBeTruthy()});
