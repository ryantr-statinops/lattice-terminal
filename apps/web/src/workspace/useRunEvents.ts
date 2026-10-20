import {useEffect,useState} from 'react';
import {useQueryClient} from '@tanstack/react-query';
import type {RunEvent} from './RunOutput';
type Connection='connecting'|'connected'|'reconnecting'|'closed';
export function useRunEvents(runID:string,kind:string){
 const client=useQueryClient();
 const [state,setState]=useState<{id:string;events:RunEvent[];connection:Connection}>({id:'',events:[],connection:'closed'});
 useEffect(()=>{
  if(!runID)return;let alive=true,terminal=false;
  setState({id:runID,events:[],connection:'connecting'});
  const stream=new EventSource(`/api/v1/runs/${encodeURIComponent(runID)}/events`);
  stream.addEventListener('open',()=>{if(alive&&!terminal)setState(old=>({...old,connection:'connected'}))});
  stream.addEventListener('run',message=>{
   if(!alive||terminal)return;
   try{const event=JSON.parse((message as MessageEvent).data) as RunEvent;if(!Number.isInteger(event.seq)||!event.payload||typeof event.type!=='string')return;
    terminal=event.type==='state'&&['completed','failed','cancelled','interrupted'].includes(String(event.payload.status));
    setState(old=>({id:runID,events:old.events.some(v=>v.seq===event.seq)?old.events:[...old.events,event].sort((a,b)=>a.seq-b.seq),connection:terminal?'closed':'connected'}));
    if(terminal){stream.close();void client.invalidateQueries({queryKey:['runs',kind]});void client.invalidateQueries({queryKey:['allocations']})}
   }catch{if(alive)setState(old=>({...old,connection:'reconnecting'}))}
  });
  stream.onerror=()=>{if(!alive||terminal)return;setState(old=>({...old,connection:'reconnecting'}));void client.invalidateQueries({queryKey:['runs',kind]})};
  return()=>{alive=false;stream.close()};
 },[runID,kind,client]);
 return state.id===runID?state:{id:runID,events:[],connection:runID?'connecting' as const:'closed' as const};
}
