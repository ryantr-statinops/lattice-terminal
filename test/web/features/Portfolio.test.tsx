// @vitest-environment jsdom
import {afterEach,describe,it,expect,vi} from 'vitest';
import {render,screen,cleanup,fireEvent,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Portfolio} from '@web/Portfolio';
import {request,send} from '@web/api';
vi.mock('@web/api',()=>({request:vi.fn(),send:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks()});
const data={funds:[{id:'f',name:'Tracking test',kind:'tracking',currency:'VND',unallocated_cash:'800',known_subtotal:'800',nav:null,pnl:null,net_external_flows:'1000',missing_prices:['SYN01'],allocations:[]}],positions:[]};
function show(){vi.mocked(request).mockResolvedValue(data);return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Portfolio/></QueryClientProvider>)}
describe('Portfolio',()=>{
 it('shows unavailable valuation instead of a zero NAV',async()=>{show();await screen.findByText('Tracking test',{selector:'td'});expect(screen.getAllByText('Unavailable')).toHaveLength(2);expect(screen.getByText(/Missing prices/)).toBeTruthy()});
 it('keeps invalid CSV preview out of apply',async()=>{show();await screen.findByText('Tracking test',{selector:'td'});vi.mocked(send).mockResolvedValue({hash:'abc',rows:[],errors:['row 2: invalid']});fireEvent.change(screen.getByLabelText('CSV input'),{target:{value:'bad'}});fireEvent.click(screen.getByText('Preview CSV'));await screen.findByText('row 2: invalid');expect((screen.getByText('Import all') as HTMLButtonElement).disabled).toBe(true);expect(send).toHaveBeenCalledWith('/portfolio/import/preview',{fund_id:'f',csv:'bad'})});
 it('invalidates preview when the CSV changes',async()=>{show();await screen.findByText('Tracking test',{selector:'td'});vi.mocked(send).mockResolvedValue({hash:'abc',rows:[{trade_id:'a'}],errors:[]});fireEvent.change(screen.getByLabelText('CSV input'),{target:{value:'first'}});fireEvent.click(screen.getByText('Preview CSV'));await waitFor(()=>expect((screen.getByText('Import all') as HTMLButtonElement).disabled).toBe(false));fireEvent.change(screen.getByLabelText('CSV input'),{target:{value:'changed'}});expect((screen.getByText('Import all') as HTMLButtonElement).disabled).toBe(true)});
});
