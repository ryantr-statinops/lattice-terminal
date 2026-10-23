import {useEffect,useRef} from 'react';
import {init,use,type EChartsType} from 'echarts/core';
import type {EChartsOption,SeriesOption} from 'echarts';
import {BarChart,CandlestickChart,LineChart} from 'echarts/charts';
import {AxisPointerComponent,DataZoomInsideComponent,GridComponent,TooltipComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
import type {Candle} from '../api';
import {useAppearance} from '../theme/store';
import {fontFamilies} from '../theme/tokens';
import type {AppearancePreferences} from '../theme/preferences';
import {formatDate} from '../theme/dateTime';
import {calculateSMA,type IndicatorConfig} from './indicators';

use([
  CandlestickChart,
  LineChart,
  BarChart,
  AxisPointerComponent,
  DataZoomInsideComponent,
  GridComponent,
  TooltipComponent,
  CanvasRenderer,
]);

const vietnamPrice = new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 2});
const vietnamVol = new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 0});

export function buildChartOption(
  candles: Candle[],
  appearance: AppearancePreferences,
  indicators: IndicatorConfig = {ma20: true, ma50: false, volume: true}
): EChartsOption {
  const c = appearance.colors;
  const labels = candles.map(candle => formatDate(candle.open_time, appearance.dateTimeRegion));
  const ohlcValues = candles.map(candle => [
    Number(candle.open),
    Number(candle.close),
    Number(candle.low),
    Number(candle.high),
  ]);

  const series: SeriesOption[] = [
    {
      type: 'candlestick',
      name: 'OHLC',
      data: ohlcValues,
      itemStyle: {
        color: c.positive,
        color0: c.negative,
        borderColor: c.positive,
        borderColor0: c.negative,
        borderWidth: 1,
      },
    },
  ];

  if (indicators.ma20) {
    series.push({
      type: 'line',
      name: 'MA20',
      data: calculateSMA(candles, 20),
      smooth: true,
      showSymbol: false,
      lineStyle: {color: c.warning, width: 1.5},
    });
  }

  if (indicators.ma50) {
    series.push({
      type: 'line',
      name: 'MA50',
      data: calculateSMA(candles, 50),
      smooth: true,
      showSymbol: false,
      lineStyle: {color: c.info, width: 1.5},
    });
  }

  if (indicators.volume) {
    const volData = candles.map(candle => {
      const isUp = Number(candle.close) >= Number(candle.open);
      return {
        value: Number(candle.volume ?? 0),
        itemStyle: {color: isUp ? c.positive : c.negative, opacity: 0.6},
      };
    });

    series.push({
      type: 'bar',
      name: 'Volume',
      yAxisIndex: 1,
      data: volData,
    });
  }

  return {
    animation: false,
    textStyle: {fontFamily: fontFamilies[appearance.font], fontSize: appearance.fontSize},
    backgroundColor: c.panel,
    grid: {left: 64, right: 24, top: 24, bottom: 36, containLabel: false},
    tooltip: {
      trigger: 'axis',
      axisPointer: {type: 'cross', lineStyle: {color: c.secondary}},
      backgroundColor: c.raised,
      borderColor: c.border,
      textStyle: {color: c.text},
      formatter: raw => {
        const items = Array.isArray(raw) ? raw : [raw];
        let out = '';
        for (const item of items) {
          if (!item || typeof item !== 'object') continue;
          if ('axisValueLabel' in item && typeof item.axisValueLabel === 'string' && !out) {
            out += `<b>${item.axisValueLabel}</b><br/>`;
          }
          const name = 'seriesName' in item ? String(item.seriesName) : '';
          const val = 'value' in item ? item.value : undefined;
          if ((name === 'OHLC' || !name) && Array.isArray(val) && val.length >= 4) {
            const [open, close, low, high] = val.map(Number);
            out += `Open: ${vietnamPrice.format(open)}<br/>High: ${vietnamPrice.format(high)}<br/>Low: ${vietnamPrice.format(low)}<br/>Close: ${vietnamPrice.format(close)}<br/>`;
          } else if (name === 'Volume' && typeof val === 'number') {
            out += `Volume: ${vietnamVol.format(val)}<br/>`;
          } else if (name.startsWith('MA') && typeof val === 'number') {
            out += `${name}: ${vietnamPrice.format(val)}<br/>`;
          }
        }
        return out;
      },
    },
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: true,
      axisLine: {lineStyle: {color: c.borderStrong}},
      axisTick: {show: false},
      axisLabel: {color: c.muted, hideOverlap: true},
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        axisLine: {show: false},
        axisTick: {show: false},
        axisLabel: {color: c.muted, formatter: (val: number) => vietnamPrice.format(val)},
        splitLine: {lineStyle: {color: c.border}},
      },
      {
        type: 'value',
        scale: true,
        show: false,
        splitLine: {show: false},
        max: (val: {max: number}) => Math.max(1, val.max * 4),
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        zoomOnMouseWheel: true,
        moveOnMouseMove: true,
        moveOnMouseWheel: false,
      },
    ],
    series,
  };
}

export function MarketChart({candles, indicators}: {candles: Candle[]; indicators: IndicatorConfig}) {
  const container = useRef<HTMLDivElement>(null);
  const instance = useRef<EChartsType | null>(null);
  const configured = useRef(false);
  const appearance = useAppearance();

  useEffect(() => {
    const element = container.current;
    if (!element) return;
    const chart = init(element, undefined, {renderer: 'canvas'});
    instance.current = chart;
    configured.current = false;
    const resize = new ResizeObserver(([entry]) => {
      if (entry.contentRect.width > 0) chart.resize({width: entry.contentRect.width});
    });
    resize.observe(element);
    return () => {
      resize.disconnect();
      chart.dispose();
      instance.current = null;
    };
  }, []);

  useEffect(() => {
    if (!instance.current) return;
    let alive = true;
    const {dataZoom, ...option} = buildChartOption(candles, appearance, indicators);
    instance.current.setOption(configured.current ? option : {...option, dataZoom});
    configured.current = true;
    void document.fonts?.load(`${appearance.fontSize}px ${fontFamilies[appearance.font]}`).then(() => {
      if (alive) instance.current?.resize();
    });
    return () => {
      alive = false;
    };
  }, [candles, appearance, indicators]);

  return (
    <div
      role="img"
      aria-label="Synthetic candlestick chart; data table below"
      ref={container}
      style={{height: 360, width: '100%'}}
    />
  );
}
