// @vitest-environment jsdom
import {expect,it} from 'vitest';
import {render,screen} from '@testing-library/react';
import {RunOutput} from '@web/workspace/RunOutput';

it('renders Strategy signal details in run history output',()=>{
  render(<RunOutput runID="run-1" events={[{
    seq:3,type:'signal',created_at:'2026-10-26T03:00:00Z',payload:{
      id:'signal-1',action:'buy',instrument_id:'vn-equity:HOSE:HPG',source:'replay',
      event_time:'2026-10-26T03:00:00Z',expires_at:'2026-10-26T03:05:00Z',
      logical_key:'breakout:HPG',correlation_id:'decision-1',reason:'Breakout confirmed',
      price_context:{bid:'25.10',ask:'25.15'},
    },
  }]}/>);

  expect(screen.getByRole('article',{name:'Strategy signal'})).toBeDefined();
  expect(screen.getByText('BUY · vn-equity:HOSE:HPG')).toBeDefined();
  expect(screen.getByText('Breakout confirmed')).toBeDefined();
  expect(screen.getByText('2026-10-26T03:05:00Z')).toBeDefined();
  expect(screen.getByText('breakout:HPG')).toBeDefined();
  expect(screen.getByText('decision-1')).toBeDefined();
  expect(screen.getByLabelText('Signal price context').textContent).toContain('25.15');
});
