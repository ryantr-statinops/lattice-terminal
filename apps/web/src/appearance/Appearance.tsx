import {useSessionOnly} from '../theme/store';
import {Panel,PanelHeader} from '../ui/layout';
import {InlineNotice} from '../ui/feedback';
import {FontControls} from './FontControls';
import {DateTimeControls} from './DateTimeControls';
import {ColorControls} from './ColorControls';
import {AppearancePreview,AppearanceReset} from './AppearancePreview';
export function Appearance(){const sessionOnly=useSessionOnly();return <section id="appearance" aria-label="Appearance"><Panel><PanelHeader title="APPEARANCE" actions={<AppearanceReset/>}/><div className="panel-content"><p className="muted" role="status">{sessionOnly?'Applied for this session only — the browser cannot save preferences.':'Saved in this browser · applied immediately · works offline'}</p>{sessionOnly&&<InlineNotice tone="warning">You can keep customizing the interface; changes may be lost when the browser closes.</InlineNotice>}<FontControls/><DateTimeControls/></div></Panel><AppearancePreview/><Panel id="appearance-colors"><PanelHeader title="ROLE COLORS"/><div className="panel-content"><p className="muted">Colors are shared across the app, charts, and editor. Reset a color to its current preset value; custom colors reset to Terminal Black.</p><ColorControls/></div></Panel></section>}
