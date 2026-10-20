// @vitest-environment jsdom
import {afterEach,describe,expect,it,vi} from 'vitest';
import {choosePreset,initAppearance,resetAppearance,setColor,updateAppearance} from './store';
import {appearanceKey} from './preferences';
afterEach(()=>{vi.restoreAllMocks();localStorage.clear();resetAppearance()});
describe('Appearance store',()=>{
 it('applies and persists appearance before rendering',()=>{choosePreset('midnight');setColor('accent','#123456');updateAppearance({font:'jetbrains',fontSize:14});initAppearance();expect(document.documentElement.style.getPropertyValue('--accent')).toBe('#123456');expect(JSON.parse(localStorage.getItem(appearanceKey)!).font).toBe('jetbrains')});
 it('persists and restores the date and time region',()=>{updateAppearance({dateTimeRegion:'united-states'});initAppearance();expect(JSON.parse(localStorage.getItem(appearanceKey)!).dateTimeRegion).toBe('united-states')});
 it('resets and migrates old light preference to dark',()=>{localStorage.setItem('kestrel.theme','light');localStorage.removeItem(appearanceKey);initAppearance();expect(document.documentElement.dataset.theme).toBe('dark');resetAppearance();expect(document.documentElement.style.getPropertyValue('--canvas')).toBe('#000000')});
 it('still applies when storage fails',()=>{vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw Error('blocked')});setColor('accent','#123456');expect(document.documentElement.style.getPropertyValue('--accent')).toBe('#123456')});
 it('synchronizes external storage updates',()=>{localStorage.setItem(appearanceKey,JSON.stringify({version:1,colors:{accent:'#ABCDEF'}}));window.dispatchEvent(new StorageEvent('storage',{key:appearanceKey}));expect(document.documentElement.style.getPropertyValue('--accent')).toBe('#ABCDEF')});
});
