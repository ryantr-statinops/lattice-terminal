import {useQuery} from '@tanstack/react-query';
import {request,type IngestionJob} from './api';
import {DataTable,StatusLabel} from './ui/data';
import {Panel,PanelHeader} from './ui/layout';
import {Button} from './ui/buttons';
import {ErrorState} from './ui/feedback';

function tone(status:IngestionJob['status']):'positive'|'warning'|'negative'|'info'{
 if(status==='completed')return 'positive';
 if(status==='failed')return 'negative';
 if(status==='interrupted'||status==='cancelled')return 'warning';
 return 'info';
}

export function IngestionJobs(){
 const jobs=useQuery({queryKey:['ingestion-jobs'],queryFn:()=>request<IngestionJob[]>('/ingestion/jobs')});
 return <Panel>
  <PanelHeader title="INGESTION JOBS" actions={<Button pending={jobs.isFetching} onClick={()=>void jobs.refetch()}>Refresh jobs</Button>}/>
  <div className="panel-content">
   <ErrorState error={jobs.error} onRetry={()=>void jobs.refetch()}/>
   <DataTable caption="Provider ingestion jobs" rows={jobs.data??[]} loading={jobs.isPending} empty="No ingestion jobs have been recorded." rowKey={job=>job.id} columns={[
    {key:'dataset',label:'Dataset',render:job=><><strong>{job.provider_id}</strong> · {job.dataset}<div className="muted">{job.asset_class} · {job.venue||'venue not specified'}</div></>},
    {key:'status',label:'Status',render:job=><StatusLabel tone={tone(job.status)}>{job.status.toUpperCase()}</StatusLabel>},
    {key:'progress',label:'Progress',render:job=>job.total_records?`${job.processed_records} / ${job.total_records}`:`${job.processed_records} records`},
    {key:'checkpoint',label:'Resume checkpoint',render:job=>job.checkpoint?`${job.checkpoint.kind} ${job.checkpoint.value} · v${job.checkpoint.version}`:'—'},
    {key:'error',label:'Last error code',render:job=>job.error_code||'—'},
    {key:'updated',label:'Updated',render:job=>new Date(job.updated_at).toLocaleString()},
   ]}/>
   <p className="muted">Interrupted jobs keep their saved checkpoint. This screen reports progress; it does not start or resume provider requests.</p>
  </div>
 </Panel>;
}
