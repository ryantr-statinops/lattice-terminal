export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch('/api/v1'+path,{credentials:'same-origin',...options,headers:{...(options.body?{'Content-Type':'application/json'}:{}),...options.headers}});
 if(response.status===401&&!path.startsWith('/auth/'))window.dispatchEvent(new Event('kestrel:locked'));
 const text=await response.text();let payload:unknown=null;try{payload=text?JSON.parse(text):null}catch{payload=text}
 if(!response.ok)throw new Error(typeof payload==='object'&&payload&&'error'in payload?String(payload.error):typeof payload==='string'?payload:'Request failed');
 return payload as T;
}
export const send=<T,>(path:string,value:unknown,method='POST')=>request<T>(path,{method,body:JSON.stringify(value)});
export type Instrument={id:string;venue:string;native_symbol:string;name:string;is_synthetic:boolean};
export type Candle={open_time:string;close_time:string;available_at:string;open:string;high:string;low:string;close:string;volume:string|null;is_closed:boolean};
export type Snapshot={snapshot_id:string;instrument:Instrument;quality:{state:string;gaps:string[];adjustment:string};candles:Candle[]};
