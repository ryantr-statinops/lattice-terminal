import {useSyncExternalStore} from 'react';
import {appearanceKey,defaultAppearance,parseAppearance,type AppearancePreferences} from './preferences';
import {fontFamilies,presets,type ColorRole,type Preset} from './tokens';
let current={preferences:defaultAppearance(),sessionOnly:false};
const listeners=new Set<()=>void>();
const subscribe=(listener:()=>void)=>{listeners.add(listener);return()=>{listeners.delete(listener)}};
const notify=()=>listeners.forEach(fn=>fn());
function apply(value:AppearancePreferences){
 const root=document.documentElement;root.dataset.theme='dark';root.style.colorScheme='dark';root.dataset.density=value.density;
 for(const [key,color] of Object.entries(value.colors))root.style.setProperty('--'+key.replace(/[A-Z]/g,c=>'-'+c.toLowerCase()),color);
 root.style.setProperty('--surface',value.colors.panel);
 root.style.setProperty('--font-family',fontFamilies[value.font]);
 root.style.setProperty('--font-size',value.fontSize+'px');root.style.setProperty('--editor-font-size',value.editorSize+'px');
 if(value.density==='compact'){
  root.style.setProperty('--line-height','17px');
  root.style.setProperty('--control-height','24px');
  root.style.setProperty('--cell-padding','1px 6px');
  root.style.setProperty('--space-1','2px');
  root.style.setProperty('--space-2','6px');
  root.style.setProperty('--space-3','10px');
  root.style.setProperty('--space-4','12px');
 }else{
  root.style.setProperty('--line-height','20px');
  root.style.setProperty('--control-height','28px');
  root.style.setProperty('--cell-padding','3px 8px');
  root.style.setProperty('--space-1','4px');
  root.style.setProperty('--space-2','8px');
  root.style.setProperty('--space-3','12px');
  root.style.setProperty('--space-4','16px');
 }
}
export function initAppearance(){
 let preferences=defaultAppearance(),sessionOnly=false;
 try{preferences=parseAppearance(localStorage.getItem(appearanceKey))}catch{sessionOnly=true}
 current={preferences,sessionOnly};apply(preferences);notify();
}
export function updateAppearance(patch:Partial<AppearancePreferences>){
 const preferences=parseAppearance(JSON.stringify({...current.preferences,...patch,version:1}));
 let sessionOnly=false;try{localStorage.setItem(appearanceKey,JSON.stringify(preferences))}catch{sessionOnly=true}
 current={preferences,sessionOnly};apply(preferences);notify();
}
export const choosePreset=(preset:Preset)=>updateAppearance({preset,colors:{...presets[preset].colors}});
export const setColor=(key:ColorRole,color:string)=>updateAppearance({preset:'custom',colors:{...current.preferences.colors,[key]:color}});
export const resetAppearance=()=>updateAppearance(defaultAppearance());
export const useAppearance=()=>useSyncExternalStore(subscribe,()=>current.preferences);
export const useSessionOnly=()=>useSyncExternalStore(subscribe,()=>current.sessionOnly);
window.addEventListener('storage',event=>{if(event.key===appearanceKey||event.key===null)initAppearance()});
