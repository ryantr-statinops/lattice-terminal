import {useSessionOnly} from '../theme/store';
import {Panel,PanelHeader} from '../ui/layout';
import {InlineNotice} from '../ui/feedback';
import {FontControls} from '../appearance/FontControls';
import {DateTimeControls} from '../appearance/DateTimeControls';
import {AppearancePreview,AppearanceReset} from '../appearance/AppearancePreview';

export function AppearanceTab(){
  const sessionOnly=useSessionOnly();

  return (
    <div className="appearance-tab" id="appearance" aria-label="Appearance">
      <Panel style={{border:'none',background:'transparent',margin:0}}>
        <PanelHeader title="APPEARANCE & TYPOGRAPHY" actions={<AppearanceReset/>}/>
        <div style={{padding:'8px 0'}}>
          {sessionOnly&&<InlineNotice tone="warning">Session-only: preferences will not be saved.</InlineNotice>}
          <div className="settings-list">
            <FontControls/>
            <DateTimeControls/>
          </div>
        </div>
      </Panel>

      <div style={{marginTop:8}}>
        <AppearancePreview/>
      </div>
    </div>
  );
}
