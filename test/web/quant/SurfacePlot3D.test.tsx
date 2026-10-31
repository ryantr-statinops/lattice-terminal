// @vitest-environment jsdom
import {afterEach,expect,it} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {SurfacePlot3D} from '@web/quant/SurfacePlot3D';

afterEach(cleanup);

it('renders 3D surface plot canvas and responds to view preset buttons', () => {
  const x = [5, 10, 15, 20];
  const y = [20, 40, 60, 80];
  const z = [
    [1.2, 1.5, 1.8, 1.4],
    [1.4, 2.1, 2.5, 1.9],
    [1.1, 1.9, 2.2, 1.6],
    [0.8, 1.2, 1.5, 1.1],
  ];

  render(
    <SurfacePlot3D
      x={x}
      y={y}
      z={z}
      xLabel="Fast MA"
      yLabel="Slow MA"
      zLabel="Sharpe"
      title="Parameter Surface Optimization"
    />
  );

  const canvas = screen.getByRole('img', {name: 'Parameter Surface Optimization'});
  expect(canvas).toBeDefined();

  const topViewBtn = screen.getByRole('button', {name: 'Top View'});
  fireEvent.click(topViewBtn);
  expect(topViewBtn.getAttribute('aria-pressed')).toBe('true');

  const isoBtn = screen.getByRole('button', {name: '3D Iso'});
  fireEvent.click(isoBtn);
  expect(isoBtn.getAttribute('aria-pressed')).toBe('true');

  const resetBtn = screen.getByRole('button', {name: 'Reset Zoom'});
  fireEvent.click(resetBtn);
});
