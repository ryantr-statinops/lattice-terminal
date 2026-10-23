// @vitest-environment jsdom
import {describe,expect,it} from 'vitest';
import type {Candle} from '../api';
import {buildChartOption} from './MarketChart';
import {calculateSMA} from './indicators';
import {presets} from '../theme/tokens';
import type {AppearancePreferences} from '../theme/preferences';

const mockCandles: Candle[] = [
  {open_time: '2026-10-19T02:00:00Z', close_time: '2026-10-19T09:00:00Z', available_at: '2026-10-19T09:00:00Z', open: '10', high: '12', low: '9', close: '11', volume: '100', is_closed: true},
  {open_time: '2026-10-20T02:00:00Z', close_time: '2026-10-20T09:00:00Z', available_at: '2026-10-20T09:00:00Z', open: '11', high: '14', low: '10', close: '13', volume: '200', is_closed: true},
  {open_time: '2026-10-21T02:00:00Z', close_time: '2026-10-21T09:00:00Z', available_at: '2026-10-21T09:00:00Z', open: '13', high: '15', low: '12', close: '14', volume: '150', is_closed: true},
];

const mockPref: AppearancePreferences = {
  version: 1,
  preset: 'terminal',
  font: 'plex',
  fontSize: 13,
  editorSize: 13,
  dateTimeRegion: 'vietnam',
  colors: {...presets.terminal.colors},
  density: 'compact',
};

describe('MarketChart indicators and dark theme', () => {
  it('calculates moving average correctly', () => {
    const sma2 = calculateSMA(mockCandles, 2);
    expect(sma2[0]).toBeNull();
    expect(sma2[1]).toBe(12); // (11 + 13) / 2
    expect(sma2[2]).toBe(13.5); // (13 + 14) / 2
  });

  it('builds chart option with candlestick and volume bar series', () => {
    const opt = buildChartOption(mockCandles, mockPref, {ma20: true, ma50: false, volume: true});
    const seriesList = Array.isArray(opt.series) ? opt.series : [];
    expect(seriesList).toHaveLength(3); // OHLC, MA20, Volume
    const ohlc = seriesList[0] as {type: string; name: string};
    expect(ohlc.type).toBe('candlestick');
    expect(ohlc.name).toBe('OHLC');

    const ma = seriesList[1] as {type: string; name: string};
    expect(ma.type).toBe('line');
    expect(ma.name).toBe('MA20');

    const vol = seriesList[2] as {type: string; name: string; yAxisIndex: number};
    expect(vol.type).toBe('bar');
    expect(vol.name).toBe('Volume');
    expect(vol.yAxisIndex).toBe(1);
  });

  it('preserves dark theme styling across palette updates', () => {
    const midnightPref: AppearancePreferences = {
      ...mockPref,
      preset: 'midnight',
      colors: {...presets.midnight.colors},
    };
    const opt = buildChartOption(mockCandles, midnightPref, {ma20: false, ma50: false, volume: false});
    expect(opt.backgroundColor).toBe(presets.midnight.colors.panel);
    const seriesList = Array.isArray(opt.series) ? opt.series : [];
    const ohlc = seriesList[0] as {itemStyle: {color: string; color0: string}};
    expect(ohlc.itemStyle.color).toBe(presets.midnight.colors.positive);
    expect(ohlc.itemStyle.color0).toBe(presets.midnight.colors.negative);
  });
});
