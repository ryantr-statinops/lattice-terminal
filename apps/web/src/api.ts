export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch('/api/v1'+path,{credentials:'same-origin',...options,headers:{...(options.body?{'Content-Type':'application/json'}:{}),...options.headers}});
 if(response.status===401&&!path.startsWith('/auth/'))window.dispatchEvent(new Event('kestrel:locked'));
 const text=await response.text();let payload:unknown=null;try{payload=text?JSON.parse(text):null}catch{payload=text}
 if(!response.ok)throw new Error(typeof payload==='object'&&payload&&'error'in payload?String(payload.error):typeof payload==='string'?payload:'Request failed');
 return payload as T;
}
export const send=<T,>(path:string,value:unknown,method='POST')=>request<T>(path,{method,body:JSON.stringify(value)});
export type Instrument={id:string;venue:string|null;board?:string;native_symbol:string;instrument_class?:string;name:string;currency?:string|null;metadata?:Record<string,unknown>;is_synthetic:boolean};
export type DatasetSnapshot={snapshot_id:string;provider_id:string;dataset:string;source_id:string;row_count:number;parser_versions:string[];quality:string[];available_from:string;available_to:string;terms_reference:string;entitlement_reference:string;expires_at:string};
export type IngestionJob={id:string;provider_id:string;capability_id:string;dataset:string;asset_class:string;venue?:string;status:'queued'|'running'|'completed'|'failed'|'cancelled'|'interrupted';processed_records:number;total_records:number;error_code?:string;checkpoint?:{version:number;kind:string;value:string};created_at:string;updated_at:string};
export type Candle={open_time:string;close_time:string;available_at:string;open:string;high:string;low:string;close:string;volume:string|null;currency?:string;price_unit?:string;volume_unit?:string;source_id?:string;revision?:string;is_closed:boolean};
export type Snapshot={snapshot_id:string;instrument:Instrument;quality:{state:string;gaps:string[];adjustment:string;calendar?:string;provisional_count?:number};candles:Candle[]};
