import {Component,type ReactNode} from 'react';
import {Button} from './buttons';
import {ErrorState} from './feedback';
export class EditorBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<div className="panel-content"><ErrorState error="Không tải được editor. Nếu ứng dụng vừa được cập nhật, hãy tải lại trang. Nội dung chưa lưu sẽ được trình duyệt cảnh báo trước khi rời trang."/><Button onClick={()=>window.location.reload()}>Tải lại ứng dụng</Button></div>:this.props.children}
}
