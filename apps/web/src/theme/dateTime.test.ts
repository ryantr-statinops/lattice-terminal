import {describe,it,expect} from 'vitest';
import {formatDate,formatDateTime} from './dateTime';

describe('date and time formatting',()=>{
 const timestamp='2026-01-02T12:34:00Z';
 it('formats dates using the selected locale',()=>{
  expect(formatDate(timestamp,'vietnam')).toBe('02/01/2026');
  expect(formatDate(timestamp,'united-states')).toBe('01/02/2026');
 });
 it('formats local times using the selected time zone and clock style',()=>{
  expect(formatDateTime(timestamp,'vietnam')).toContain('19:34');
  expect(formatDateTime(timestamp,'vietnam').endsWith('ICT')).toBe(true);
  expect(formatDateTime(timestamp,'united-states')).toContain('07:34 AM');
  expect(formatDateTime(timestamp,'united-states').endsWith('ET')).toBe(true);
 });
});
