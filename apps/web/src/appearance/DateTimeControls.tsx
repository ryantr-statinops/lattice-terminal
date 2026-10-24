import {useAppearance,updateAppearance} from '../theme/store';
import {Select} from '../ui/fields';
import {SettingRow} from '../ui/SettingRow';

export function DateTimeControls(){
  const value=useAppearance();
  return (
    <SettingRow id="setting-datetime" label="Date and time format">
      <Select
        id="setting-datetime"
        aria-label="Date and time format"
        value={value.dateTimeRegion}
        onChange={event=>updateAppearance({dateTimeRegion:event.target.value as typeof value.dateTimeRegion})}
      >
        <option value="vietnam">Vietnam · DD/MM/YYYY · 24-hour · ICT</option>
        <option value="united-states">United States · MM/DD/YYYY · 12-hour · ET</option>
      </Select>
    </SettingRow>
  );
}
