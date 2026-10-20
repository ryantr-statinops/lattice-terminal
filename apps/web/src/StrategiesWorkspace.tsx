import {useState} from 'react';
import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {request} from './api';
import {Workspace} from './Workspace';
import {Panel,PanelHeader} from './ui/layout';
import {Field,Select} from './ui/fields';
import {StatusLabel} from './ui/data';
import {ErrorState,LoadingState} from './ui/feedback';
type Allocation={id:string;name:string;mode:string;cash:string;status:string};
type Tape={snapshot_id:string;source_id:string;event_count:number};
export function StrategiesWorkspace(){
 const allocations=useQuery({queryKey:['allocations'],queryFn:()=>request<Allocation[]>('/allocations'),refetchInterval:3000});
 const tapes=useQuery({queryKey:['detailed-tapes'],queryFn:()=>request<Tape[]>('/engine/backtest/data')});
 const [id,setID]=useState(''),[source,setSource]=useState('ssi-live'),[tape,setTape]=useState('');
 const allocation=allocations.data?.find(v=>v.id===id&&v.mode==='strategy');const snapshot=tape||tapes.data?.[0]?.snapshot_id||'';
 const blocked=allocations.isPending||tapes.isPending?'Đang đọc cấu hình…':allocations.error||tapes.error?'Không đọc được allocation hoặc snapshot.':source!=='fixture-replay'?'SSI live bị khóa. Chọn rõ Synthetic fixture replay để thử nghiệm.':!allocation?'Chọn phần vốn Strategy từ Assets.':allocation.status!=='stopped'?'Phần vốn phải ở trạng thái stopped.':!snapshot?'Chưa có fixture event tape.':'';
 const controls=<Panel><PanelHeader title="STRATEGY / PAPER CONFIGURATION" actions={<StatusLabel tone="warning">SSI LIVE BLOCKED</StatusLabel>}/><div className="panel-content"><p>Strategy callback Python cho Paper. File Backtest không được nhận ở đây.</p>{(allocations.isPending||tapes.isPending)&&<LoadingState>Đang đọc phần vốn và dữ liệu…</LoadingState>}<ErrorState error={allocations.error||tapes.error}/><div className="form-grid"><Field label="Strategy allocation"><Select value={id} onChange={e=>setID(e.target.value)}><option value="">Chọn phần vốn từ Assets</option>{allocations.data?.filter(v=>v.mode==='strategy').map(v=><option key={v.id} value={v.id} disabled={v.status!=='stopped'}>{v.name} · {v.cash} VND · {v.status}</option>)}</Select></Field><Field label="Paper source"><Select value={source} onChange={e=>setSource(e.target.value)}><option value="ssi-live">SSI live — blocked</option><option value="fixture-replay">Synthetic fixture replay — không realtime</option></Select></Field>{source==='fixture-replay'&&<Field label="Fixture event tape"><Select value={snapshot} onChange={e=>setTape(e.target.value)}>{tapes.data?.map(v=><option key={v.snapshot_id} value={v.snapshot_id}>{v.source_id} · {v.event_count} events</option>)}</Select></Field>}</div><Link to="/assets">Quản lý quỹ →</Link><p className="muted">Vốn lấy từ allocation đã chọn; backend kiểm tra và giữ quyền điều khiển riêng. Stop giữ nguyên vị thế/vốn đang cam kết. Fixture replay không chứng minh SSI live hoạt động.</p></div></Panel>;
 return <Workspace kind="strategy" title="Strategies" controls={controls} extraParams={{allocation_id:id,paper_source:source,event_snapshot:snapshot}} runBlockedReason={blocked}/>;
}
