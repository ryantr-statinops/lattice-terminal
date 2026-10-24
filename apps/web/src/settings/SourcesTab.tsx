import {useQuery} from '@tanstack/react-query';
import {request} from '../api';
import {Panel,PanelHeader} from '../ui/layout';
import {DataTable,StatusLabel} from '../ui/data';
import {ErrorState,LoadingState} from '../ui/feedback';

export type Source = {
  id: string;
  documented: boolean;
  access_tested: boolean;
  rights_confirmed: boolean;
  approved: boolean;
  operating_state: string;
  reason: string;
};

export function SourcesTab(){
  const query = useQuery({
    queryKey: ['sources'],
    queryFn: () => request<Source[]>('/engine/sources'),
  });

  return (
    <div className="sources-tab" id="sources" aria-label="Source Evidence">
      <Panel style={{border:'none',background:'transparent',margin:0}}>
        <PanelHeader title="DATA SOURCES & CAPABILITY EVIDENCE"/>
        <div style={{padding:'8px 0'}}>
          {query.isPending && <LoadingState>Loading source evidence…</LoadingState>}
          <ErrorState error={query.error} onRetry={() => void query.refetch()} />
        </div>
        <DataTable
          loading={query.isPending}
          caption="Source capability evidence"
          rows={query.data ?? []}
          rowKey={v => v.id}
          columns={[
            {key: 'id', label: 'Capability', render: v => v.id},
            ...(['documented', 'access_tested', 'rights_confirmed', 'approved'] as const).map(key => ({
              key,
              label: key,
              render: (v: Source) => (
                <StatusLabel tone={v[key] ? 'positive' : 'warning'}>
                  {v[key] ? 'yes' : 'pending'}
                </StatusLabel>
              ),
            })),
            {key: 'state', label: 'Mode', render: v => v.operating_state},
            {key: 'reason', label: 'Reason', render: v => v.reason},
          ]}
        />
      </Panel>
    </div>
  );
}
