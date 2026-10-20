import {useSyncExternalStore} from 'react';
const subscribe=(callback:()=>void)=>{window.addEventListener('kestrel:theme',callback);return()=>window.removeEventListener('kestrel:theme',callback)};
const snapshot=()=>document.documentElement.dataset.theme==='light'?'light':'dark';
export const useTheme=()=>useSyncExternalStore(subscribe,snapshot);
export function setTheme(value:string){document.documentElement.dataset.theme=value==='light'?'light':'dark';try{localStorage.setItem('kestrel.theme',value)}catch{/* Preference storage may be disabled. */}window.dispatchEvent(new Event('kestrel:theme'))}
export function initTheme(){try{setTheme(localStorage.getItem('kestrel.theme')||'dark')}catch{setTheme('dark')}}
