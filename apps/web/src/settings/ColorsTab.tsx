import {Panel,PanelHeader} from '../ui/layout';
import {ColorControls} from '../appearance/ColorControls';

export function ColorsTab(){
  return (
    <div className="colors-tab" id="appearance-colors" aria-label="Role Colors">
      <Panel style={{border:'none',background:'transparent',margin:0}}>
        <PanelHeader title="ROLE COLORS & CONTRAST PROFILE"/>
        <div style={{padding:'8px 0'}}>
          <p className="muted" style={{margin:'0 0 12px'}}>
            Colors are shared across the terminal shell, candlestick charts, 3D surface plots, and Monaco editor. Custom changes apply and persist immediately.
          </p>
          <ColorControls/>
        </div>
      </Panel>
    </div>
  );
}
