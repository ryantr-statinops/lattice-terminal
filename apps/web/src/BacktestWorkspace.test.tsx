// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {BacktestWorkspace} from './BacktestWorkspace';
vi.mock('./Workspace',()=>({Workspace:({controls,runBlockedReason,extraParams}:{controls:React.ReactNode;runBlockedReason:string;extraParams:unknown})=><>{controls}<p data-testid="blocked">{runBlockedReason}</p><pre data-testid="params">{JSON.stringify(extraParams)}</pre></>}));
vi.mock('./RunComparison',()=>({RunComparison:()=>null}));
vi.mock('./api',()=>({request:vi.fn(async(path:string)=>path.includes('/data')?[{snapshot_id:'tape',source_id:'fixture',event_count:10}]:[{id:'train',status:'completed',file:'a.py',params:{stage:'train',capital:'9007199254740993.01',event_snapshot:'tape',train_start:'2026-10-01T00:00:00Z',train_end:'2026-10-01T23:59:00Z',test_start:'2026-10-02T00:00:00Z',test_end:'2026-10-02T23:59:00Z',custom_param:42}}])}));
afterEach(cleanup);
function show(){render(<QueryClientProvider client={new QueryClient()}><BacktestWorkspace/></QueryClientProvider>)}
it('clearing a date blocks Run without throwing during render',async()=>{show();await screen.findByText(/fixture · 10/);fireEvent.change(screen.getByLabelText('Train bắt đầu · UTC'),{target:{value:''}});expect(screen.getByTestId('blocked').textContent).toBe('Điền đủ thời gian hợp lệ.')});
it('loads and freezes the exact Train configuration including extra parameters',async()=>{show();await screen.findByText(/fixture · 10/);fireEvent.change(screen.getByLabelText('Train or Test'),{target:{value:'test'}});fireEvent.change(screen.getByLabelText('Frozen Train run'),{target:{value:'train'}});expect((screen.getByLabelText('Vốn VND') as HTMLInputElement).disabled).toBe(true);const params=JSON.parse(screen.getByTestId('params').textContent!);expect(params.capital).toBe('9007199254740993.01');expect(params.custom_param).toBe(42);expect(params.stage).toBe('test');expect(screen.getByTestId('blocked').textContent).toBe('')});
