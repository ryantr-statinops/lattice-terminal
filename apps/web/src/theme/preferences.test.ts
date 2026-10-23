import {describe,it,expect} from 'vitest';
import {defaultAppearance,parseAppearance} from './preferences';
import {presets,contrast} from './tokens';
describe('Appearance preferences',()=>{
 it('recovers corrupt, missing and old preferences',()=>{for(const raw of [null,'bad','{}','{"version":0}'])expect(parseAppearance(raw)).toEqual(defaultAppearance())});
 it('validates each field and accepts only hex colors',()=>{const p=parseAppearance(JSON.stringify({version:1,preset:'unknown',fontSize:99,editorSize:7,colors:{text:'url(evil)',accent:'#abcdef'}}));expect(p.colors.accent).toBe('#ABCDEF');expect(p.colors.text).toBe('#EEEEEE');expect(p.fontSize).toBe(13);expect(p.editorSize).toBe(13)});
 it('roundtrips custom preferences',()=>{const value={...defaultAppearance(),preset:'custom',font:'jetbrains',editorSize:17};expect(parseAppearance(JSON.stringify(value))).toEqual(value)});
 it('defaults older preferences to Vietnam and validates the selected region',()=>{expect(parseAppearance('{"version":1}').dateTimeRegion).toBe('vietnam');expect(parseAppearance('{"version":1,"dateTimeRegion":"invalid"}').dateTimeRegion).toBe('vietnam');expect(parseAppearance('{"version":1,"dateTimeRegion":"united-states"}').dateTimeRegion).toBe('united-states')});
 it('defaults to compact density and validates comfortable setting',()=>{expect(parseAppearance('{"version":1}').density).toBe('compact');expect(parseAppearance('{"version":1,"density":"comfortable"}').density).toBe('comfortable');expect(parseAppearance('{"version":1,"density":"invalid"}').density).toBe('compact')});
 it('ships readable presets',()=>{for(const {colors:c} of Object.values(presets))for(const fg of [c.text,c.secondary,c.muted])for(const bg of [c.canvas,c.panel,c.raised,c.input])expect(contrast(fg,bg)).toBeGreaterThanOrEqual(4.5)});
});
