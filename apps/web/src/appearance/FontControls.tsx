import {useAppearance,choosePreset,updateAppearance} from '../theme/store';
import {presets,type Preset} from '../theme/tokens';
import {Select} from '../ui/fields';
import {SettingRow} from '../ui/SettingRow';

export function FontControls(){
  const value=useAppearance();
  return (
    <>
      <SettingRow id="setting-preset" label="Preset">
        <Select
          id="setting-preset"
          aria-label="Preset"
          value={value.preset}
          onChange={e=>choosePreset(e.target.value as Preset)}
        >
          {value.preset==='custom'&&<option value="custom" disabled>Custom</option>}
          {Object.entries(presets).map(([key,preset])=>(
            <option key={key} value={key}>{preset.name}</option>
          ))}
        </Select>
      </SettingRow>

      <SettingRow id="setting-density" label="Layout density / Scale">
        <Select
          id="setting-density"
          aria-label="Layout density / Scale"
          value={value.density}
          onChange={e=>updateAppearance({density:e.target.value as typeof value.density})}
        >
          <option value="compact">Compact (90% Terminal density)</option>
          <option value="comfortable">Comfortable (100% Standard)</option>
        </Select>
      </SettingRow>

      <SettingRow id="setting-app-font" label="App font">
        <Select
          id="setting-app-font"
          aria-label="App font"
          value={value.font}
          onChange={e=>updateAppearance({font:e.target.value as typeof value.font})}
        >
          <option value="plex">IBM Plex Mono</option>
          <option value="jetbrains">JetBrains Mono</option>
        </Select>
      </SettingRow>

      <SettingRow id="setting-ui-font-size" label="UI font size">
        <Select
          id="setting-ui-font-size"
          aria-label="UI font size"
          value={value.fontSize}
          onChange={e=>updateAppearance({fontSize:Number(e.target.value) as typeof value.fontSize})}
        >
          {[12,13,14].map(size=>(
            <option key={size} value={size}>{size}px</option>
          ))}
        </Select>
      </SettingRow>

      <SettingRow id="setting-editor-font-size" label="Editor font size">
        <Select
          id="setting-editor-font-size"
          aria-label="Editor font size"
          value={value.editorSize}
          onChange={e=>updateAppearance({editorSize:Number(e.target.value)})}
        >
          {[12,13,14,15,16,17,18].map(size=>(
            <option key={size} value={size}>{size}px</option>
          ))}
        </Select>
      </SettingRow>
    </>
  );
}
