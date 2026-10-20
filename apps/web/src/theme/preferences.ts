import {presets, terminalColors, type Colors, type Preset} from './tokens';
export type AppearancePreferences = {version:1;preset:Preset|'custom';colors:Colors;font:'plex'|'jetbrains';fontSize:12|13|14;editorSize:number};
export const appearanceKey='kestrel.appearance.v1';
export const defaultAppearance=():AppearancePreferences=>({version:1,preset:'terminal',colors:{...terminalColors},font:'plex',fontSize:13,editorSize:13});
export function parseAppearance(raw:string|null):AppearancePreferences {
  const fallback=defaultAppearance();
  try {
    const value=JSON.parse(raw||'null');
    if(!value||value.version!==1)return fallback;
    const colors={...fallback.colors};
    for(const key of Object.keys(colors) as (keyof Colors)[])if(typeof value.colors?.[key]==='string'&&/^#[0-9a-f]{6}$/i.test(value.colors[key]))colors[key]=value.colors[key].toUpperCase();
    return {...fallback,colors,preset:value.preset==='custom'||Object.hasOwn(presets,value.preset)?value.preset:'custom',font:value.font==='jetbrains'?'jetbrains':'plex',fontSize:[12,13,14].includes(value.fontSize)?value.fontSize:13,editorSize:Number.isInteger(value.editorSize)&&value.editorSize>=12&&value.editorSize<=18?value.editorSize:13};
  }catch{return fallback}
}
