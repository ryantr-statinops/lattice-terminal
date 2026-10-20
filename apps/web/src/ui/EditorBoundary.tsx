import {Component,type ReactNode} from 'react';
import {Button} from './buttons';
import {ErrorState} from './feedback';
export class EditorBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<div className="panel-content"><ErrorState error="Could not load the editor. If the app was just updated, reload the page. The browser will warn you before leaving with unsaved content."/><Button onClick={()=>window.location.reload()}>Reload app</Button></div>:this.props.children}
}
