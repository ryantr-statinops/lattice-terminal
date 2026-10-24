import {Panel,PanelHeader} from '../ui/layout';
import {ColorControls} from '../appearance/ColorControls';

export function ColorsTab(){
  return (
    <div className="colors-tab" id="appearance-colors" aria-label="Role Colors">
      <Panel style={{border:'none',background:'transparent',margin:0}}>
        <PanelHeader title="ROLE COLORS & CONTRAST PROFILE"/>
        <div style={{padding:'8px 0'}}>
          <ColorControls/>
        </div>
      </Panel>
    </div>
  );
}
