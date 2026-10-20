import {useEffect,type ReactNode} from 'react';
import {Button} from './buttons';
export function InlineNotice({children,tone='info'}:{children:ReactNode;tone?:'info'|'warning'|'negative'|'positive'}){return <div className={'notice tone-'+tone} role={tone==='negative'?'alert':'status'}>{children}</div>}
export const LoadingState=({children='Đang tải…'}:{children?:ReactNode})=><p className="loading-state" role="status">{children}</p>;
export const EmptyState=({children='Chưa có dữ liệu.'}:{children?:ReactNode})=><p className="empty-state">{children}</p>;
export function ErrorState({error,onRetry}:{error:unknown;onRetry?:()=>void}){if(!error)return null;return <InlineNotice tone="negative">{error instanceof Error?error.message:String(error)}{onRetry&&<Button onClick={onRetry}>Thử lại</Button>}</InlineNotice>}
export function Toast({message,onDismiss}:{message:string;onDismiss:()=>void}){useEffect(()=>{if(!message)return;const timer=setTimeout(onDismiss,5000);return()=>clearTimeout(timer)},[message,onDismiss]);return message?<div className="toast" role="status">{message}<Button aria-label="Đóng thông báo" onClick={onDismiss}>×</Button></div>:null}
