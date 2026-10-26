import {useState} from 'react';
import {useQuery,useQueryClient} from '@tanstack/react-query';
import {request,send,type IngestionJob} from './api';
import {DataTable,StatusLabel} from './ui/data';
import {Panel,PanelHeader} from './ui/layout';
import {Button} from './ui/buttons';
import {ErrorState,InlineNotice} from './ui/feedback';

function tone(status:IngestionJob['status']):'positive'|'warning'|'negative'|'info'{
 if(status==='completed')return 'positive';
 if(status==='failed')return 'negative';
 if(status==='interrupted'||status==='cancelled')return 'warning';
 return 'info';
}

export function IngestionJobs({canSyncSsiHoseEquity=false,canSyncSsiHoseIndices=false}:{canSyncSsiHoseEquity?:boolean;canSyncSsiHoseIndices?:boolean}){
 const client=useQueryClient();
 const [syncing,setSyncing]=useState(false);
 const [syncError,setSyncError]=useState<unknown>(null);
 const [syncMessage,setSyncMessage]=useState('');
 const jobs=useQuery({queryKey:['ingestion-jobs'],queryFn:()=>request<IngestionJob[]>('/ingestion/jobs')});
 const syncSsiCatalogue=async()=>{
  setSyncing(true);setSyncError(null);setSyncMessage('');
  try{
   const result=await send<{job:{status:string};snapshot_id:string}>('/ingestion/catalogues/ssi/hose-equity',{});
   setSyncMessage(`SSI HOSE catalogue saved as snapshot ${result.snapshot_id.slice(0,12)}.`);
   await Promise.all([client.invalidateQueries({queryKey:['ingestion-jobs']}),client.invalidateQueries({queryKey:['market-provider-datasets']})]);
  }catch(error){setSyncError(error);void client.invalidateQueries({queryKey:['ingestion-jobs']})}
  finally{setSyncing(false)}
 };
 const syncSsiIndices=async()=>{
  setSyncing(true);setSyncError(null);setSyncMessage('');
  try{
   const result=await send<{job:{status:string};snapshot_id:string}>('/ingestion/catalogues/ssi/hose-indices',{});
   setSyncMessage(`SSI HOSE index catalogue saved as snapshot ${result.snapshot_id.slice(0,12)}.`);
   await Promise.all([client.invalidateQueries({queryKey:['ingestion-jobs']}),client.invalidateQueries({queryKey:['market-provider-datasets']})]);
  }catch(error){setSyncError(error);void client.invalidateQueries({queryKey:['ingestion-jobs']})}
  finally{setSyncing(false)}
 };
 return <Panel>
  <PanelHeader title="INGESTION JOBS" actions={<div style={{display:'flex',gap:8}}>{canSyncSsiHoseEquity&&<Button pending={syncing} onClick={()=>void syncSsiCatalogue()}>Sync SSI HOSE stocks</Button>}{canSyncSsiHoseIndices&&<Button pending={syncing} onClick={()=>void syncSsiIndices()}>Sync SSI HOSE indices</Button>}<Button pending={jobs.isFetching} onClick={()=>void jobs.refetch()}>Refresh jobs</Button></div>}/>
  <div className="panel-content">
   <ErrorState error={jobs.error||syncError} onRetry={()=>{void jobs.refetch();setSyncError(null)}}/>
   {syncMessage&&<InlineNotice tone="positive">{syncMessage}</InlineNotice>}
   <DataTable caption="Provider ingestion jobs" rows={jobs.data??[]} loading={jobs.isPending} empty="No ingestion jobs have been recorded." rowKey={job=>job.id} columns={[
    {key:'dataset',label:'Dataset',render:job=><><strong>{job.provider_id}</strong> · {job.dataset}<div className="muted">{job.asset_class} · {job.venue||'venue not specified'}</div></>},
    {key:'status',label:'Status',render:job=><StatusLabel tone={tone(job.status)}>{job.status.toUpperCase()}</StatusLabel>},
    {key:'progress',label:'Progress',render:job=>job.total_records?`${job.processed_records} / ${job.total_records}`:`${job.processed_records} records`},
    {key:'checkpoint',label:'Resume checkpoint',render:job=>job.checkpoint?`${job.checkpoint.kind} ${job.checkpoint.value} · v${job.checkpoint.version}`:'—'},
    {key:'error',label:'Last error code',render:job=>job.error_code||'—'},
    {key:'updated',label:'Updated',render:job=>new Date(job.updated_at).toLocaleString()},
   ]}/>
   <p className="muted">Interrupted jobs keep their saved checkpoint. Manual catalogue sync starts a new job; this screen does not resume an interrupted request.</p>
  </div>
 </Panel>;
}
