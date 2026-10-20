import {Select} from '../ui/fields';
import {useAppearance} from '../theme/store';
import {formatDateTime} from '../theme/dateTime';
export function RunHistory({runs,value,onChange}:{runs:{id:string;created_at:string;status:string}[];value:string;onChange:(id:string)=>void}){const appearance=useAppearance();return <Select aria-label="Run history" value={value} onChange={e=>onChange(e.target.value)}><option value="">Select a run for this file</option>{runs.map(v=><option key={v.id} value={v.id}>{formatDateTime(v.created_at,appearance.dateTimeRegion)} · {v.status}</option>)}</Select>}
