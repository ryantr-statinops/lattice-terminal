import {useSessionOnly} from '../theme/store';
import {Panel,PanelHeader} from '../ui/layout';
import {InlineNotice} from '../ui/feedback';
import {FontControls} from './FontControls';
import {ColorControls} from './ColorControls';
import {AppearancePreview,AppearanceReset} from './AppearancePreview';
export function Appearance(){const sessionOnly=useSessionOnly();return <section id="appearance" aria-label="Appearance"><Panel><PanelHeader title="APPEARANCE" actions={<AppearanceReset/>}/><div className="panel-content"><p className="muted" role="status">{sessionOnly?'Chỉ áp dụng trong phiên này — trình duyệt không cho lưu tùy chỉnh.':'Tự lưu trên trình duyệt này · áp dụng ngay · dùng offline'}</p>{sessionOnly&&<InlineNotice tone="warning">Bạn có thể tiếp tục chỉnh giao diện; lựa chọn có thể mất khi đóng trình duyệt.</InlineNotice>}<FontControls/></div></Panel><AppearancePreview/><Panel id="appearance-colors"><PanelHeader title="MÀU THEO VAI TRÒ"/><div className="panel-content"><p className="muted">Màu dùng chung toàn ứng dụng, biểu đồ và editor. Đặt lại từng màu dùng giá trị preset hiện tại; ở chế độ Tùy chỉnh dùng Terminal Black.</p><ColorControls/></div></Panel></section>}
