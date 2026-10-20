import type {HTMLAttributes,ReactNode} from 'react';
export function PageHeader({eyebrow,title,actions}:{eyebrow?:string;title:string;actions?:ReactNode}){return <div className="page-title"><div>{eyebrow&&<small>{eyebrow}</small>}<h1>{title}</h1></div>{actions}</div>}
export function Panel({children,className='',...props}:HTMLAttributes<HTMLElement>){return <section className={'panel '+className} {...props}>{children}</section>}
export function PanelHeader({title,actions}:{title:ReactNode;actions?:ReactNode}){return <div className="panel-heading"><strong>{title}</strong>{actions&&<div className="panel-actions">{actions}</div>}</div>}
export function Toolbar({className='',...props}:HTMLAttributes<HTMLDivElement>){return <div className={'toolbar '+className} {...props}/>}
