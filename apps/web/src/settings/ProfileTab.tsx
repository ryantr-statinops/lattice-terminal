import {useQuery} from '@tanstack/react-query';
import {request} from '../api';
import {Panel,PanelHeader} from '../ui/layout';

export function ProfileTab(){
  const local = useQuery({
    queryKey: ['local-config'],
    queryFn: () => request<{data_dir: string; account_source: string}>('/local/config'),
  });

  return (
    <div className="profile-tab" id="profile" aria-label="Local Profile">
      <Panel style={{border:'none',background:'transparent',margin:0}}>
        <PanelHeader title="LOCAL PROFILE & STORAGE"/>
        <div style={{padding:'8px 0'}}>
          <div className="settings-list" style={{margin:'0 0 16px'}}>
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-label">Data Directory</span>
              </div>
              <div className="setting-control">
                <code>{local.data?.data_dir ?? 'Loading…'}</code>
              </div>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-label">Auth Source</span>
              </div>
              <div className="setting-control">
                <code>{local.data?.account_source ?? '.env'}</code>
              </div>
            </div>
          </div>

          <pre style={{padding:8,background:'var(--input)',border:'1px solid var(--border)',borderRadius:2,fontSize:12}}>
            go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials set{'\n'}
            go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials status
          </pre>
        </div>
      </Panel>
    </div>
  );
}
