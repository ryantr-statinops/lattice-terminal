// @vitest-environment jsdom
import type {ReactNode} from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter} from 'react-router-dom';
import {StrategiesWorkspace} from '@web/StrategiesWorkspace';

const tape={snapshot_id:'a'.repeat(64),source_id:'fixture',event_count:80};
vi.mock('@web/api',()=>({request:vi.fn(async(path:string)=>path==='/allocations'?[]:[tape])}));
vi.mock('@web/Workspace',()=>({Workspace:({controls,extraParams,runBlockedReason}:{controls:ReactNode;extraParams:Record<string,unknown>;runBlockedReason:string})=><>{controls}<p data-testid="blocked">{runBlockedReason}</p><pre data-testid="params">{JSON.stringify(extraParams)}</pre></>}));

afterEach(cleanup);
function show(){render(<MemoryRouter><QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><StrategiesWorkspace/></QueryClientProvider></MemoryRouter>)}

it('runs signal-only replay without an allocation while keeping paper mode gated',async()=>{
 show();
 fireEvent.change(screen.getByLabelText('Data source'),{target:{value:'fixture-replay'}});
 await screen.findByRole('option',{name:/fixture · 80 events/});
 fireEvent.change(screen.getByLabelText('Strategy mode'),{target:{value:'signal_only'}});
 expect(screen.getByTestId('blocked').textContent).toBe('');
 const params=JSON.parse(screen.getByTestId('params').textContent!);
 expect(params.strategy_mode).toBe('signal_only');
 expect(params.event_snapshot).toBe(tape.snapshot_id);
 expect(params).not.toHaveProperty('allocation_id');
 expect(screen.queryByLabelText('Strategy allocation')).toBeNull();
 fireEvent.change(screen.getByLabelText('Strategy mode'),{target:{value:'paper'}});
 expect(screen.getByTestId('blocked').textContent).toBe('Select a Strategy allocation in Assets.');
});
