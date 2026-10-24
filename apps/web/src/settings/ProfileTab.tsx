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
        <PanelHeader title="LOCAL PROFILE & CREDENTIAL CONFIGURATION"/>
        <div style={{padding:'8px 0'}}>
          <p>A single local account is loaded from <code>.env</code> at startup.</p>
          <div className="settings-list" style={{margin:'12px 0'}}>
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-label">Data Directory</span>
                <span className="setting-desc">Host directory for workspaces, SQLite database and artifacts</span>
              </div>
              <div className="setting-control">
                <code>{local.data?.data_dir ?? 'Loading…'}</code>
              </div>
            </div>
            <div className="setting-row">
              <div className="setting-info">
                <span className="setting-label">Authentication Source</span>
                <span className="setting-desc">Local credentials provider</span>
              </div>
              <div className="setting-control">
                <code>{local.data?.account_source ?? '.env'}</code>
              </div>
            </div>
          </div>

          <p style={{marginTop:16}}>
            Edit the username/password in the project <code>.env</code> file, then restart Compose to apply changes.
          </p>
          <pre style={{padding:8,background:'var(--input)',border:'1px solid var(--border)',borderRadius:2,fontSize:12}}>
            go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials set{'\n'}
            go -C services/gateway run ./cmd/kestrel -root ../.. -ssi-credentials status
          </pre>
          <p className="muted" style={{fontSize:11,marginTop:8}}>
            The CLI only shows instructions for editing the account in .env; SSI credentials remain protected in Windows Credential Manager.
          </p>
        </div>
      </Panel>
    </div>
  );
}
