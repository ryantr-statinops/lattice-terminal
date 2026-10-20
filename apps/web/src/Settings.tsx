import {useEffect} from 'react';
import {useLocation} from 'react-router-dom';
import {useQuery} from '@tanstack/react-query';
import {request} from './api';
import {Appearance} from './appearance/Appearance';
import {PageHeader,Panel,PanelHeader} from './ui/layout';
import {DataTable,StatusLabel} from './ui/data';
import {ErrorState,LoadingState} from './ui/feedback';
type Source={id:string;documented:boolean;access_tested:boolean;rights_confirmed:boolean;approved:boolean;operating_state:string;reason:string};
export function Settings(){
 const query=useQuery({queryKey:['sources'],queryFn:()=>request<Source[]>('/engine/sources')});const {hash}=useLocation();
 useEffect(()=>{if(hash==='#appearance')document.getElementById('appearance')?.scrollIntoView({block:'start'})},[hash]);
 const local=useQuery({queryKey:['local-config'],queryFn:()=>request<{data_dir:string;account_source:string}>('/local/config')});
 return <section><PageHeader eyebrow="SETTINGS / LOCAL PROFILE" title="Settings"/><Appearance/><Panel><PanelHeader title="NGUỒN DỮ LIỆU"/><div className="panel-content"><p className="muted">Credentials chỉ được cấu hình bằng CLI và Windows Credential Manager. Không nhập SSI secret vào trình duyệt.</p>{query.isPending&&<LoadingState>Đang đọc source evidence…</LoadingState>}<ErrorState error={query.error} onRetry={()=>void query.refetch()}/></div><DataTable loading={query.isPending} caption="Source evidence — mỗi flag độc lập" rows={query.data??[]} rowKey={v=>v.id} columns={[{key:'id',label:'Capability',render:v=>v.id},...(['documented','access_tested','rights_confirmed','approved'] as const).map(key=>({key,label:key,render:(v:Source)=><StatusLabel tone={v[key]?'positive':'warning'}>{v[key]?'yes':'pending'}</StatusLabel>})),{key:'state',label:'Mode',render:v=>v.operating_state},{key:'reason',label:'Lý do',render:v=>v.reason}]}/></Panel><Panel><PanelHeader title="LOCAL PROFILE"/><div className="panel-content"><p>Một tài khoản local lấy từ .env khi khởi động.</p><p className="muted">Thư mục dữ liệu: <code>{local.data?.data_dir??'Đang đọc…'}</code></p><p>Sửa username/password trong .env ở thư mục dự án rồi khởi động lại để áp dụng.</p><pre>kestrel.exe -ssi-credentials set<br/>kestrel.exe -ssi-credentials status<br/>kestrel.exe -reset-password</pre><p className="muted">CLI chỉ hiển thị hướng dẫn sửa .env cho tài khoản; SSI credentials vẫn ở Windows Credential Manager.</p></div></Panel></section>;
}
