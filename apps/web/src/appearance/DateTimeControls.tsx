import {useAppearance,updateAppearance} from '../theme/store';
import {Field,Select} from '../ui/fields';

export function DateTimeControls(){
 const value=useAppearance();
 return <Field label="Date and time format" hint="Vietnam uses ICT. United States uses Eastern Time (ET).">
  <Select value={value.dateTimeRegion} onChange={event=>updateAppearance({dateTimeRegion:event.target.value as typeof value.dateTimeRegion})}>
   <option value="vietnam">Vietnam · DD/MM/YYYY · 24-hour</option>
   <option value="united-states">United States · MM/DD/YYYY · 12-hour · ET</option>
  </Select>
 </Field>;
}
