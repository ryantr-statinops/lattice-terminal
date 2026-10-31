// @vitest-environment jsdom
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {act,cleanup,fireEvent,render,screen,within} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {Assets} from '@web/Assets';
import {request,send} from '@web/api';
vi.mock('@web/api',()=>({request:vi.fn(),send:vi.fn()}));
const funds=[{id:'paper',name:'Paper A',kind:'paper',unallocated_cash:'1000'},{id:'reserve',name:'Paper B',kind:'paper',unallocated_cash:'500'},{id:'tracking',name:'Tracking C',kind:'tracking',unallocated_cash:'500'}];
beforeEach(()=>{HTMLDialogElement.prototype.showModal=function(){this.setAttribute('open','')};HTMLDialogElement.prototype.close=function(){this.removeAttribute('open')};vi.mocked(request).mockImplementation(async path=>path==='/funds'?funds:[])});
afterEach(()=>{cleanup();vi.clearAllMocks()});
function show(){render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><Assets/></QueryClientProvider>)}
it('offers only compatible destination funds in the transfer dialog',async()=>{show();await screen.findByText('Paper A · paper');fireEvent.click(screen.getByText('Transfer capital'));const options=within(screen.getByRole('dialog')).getAllByRole('option').map(v=>v.textContent);expect(options).toContain('Paper B');expect(options).not.toContain('Paper A');expect(options).not.toContain('Tracking C')});
it('retains the entered amount after a rejected ledger mutation',async()=>{show();await screen.findByText('Paper A · paper');vi.mocked(send).mockRejectedValue(Error('cash insufficient'));fireEvent.click(screen.getByText('Withdraw'));fireEvent.change(screen.getByLabelText('Amount · VND'),{target:{value:'5000'}});fireEvent.click(screen.getByText('Confirm'));await screen.findByText('cash insufficient');expect((screen.getByLabelText('Amount · VND') as HTMLInputElement).value).toBe('5000');expect(send).toHaveBeenCalledWith('/funds/paper/cash',expect.objectContaining({kind:'withdraw',amount:'5000'}));expect(screen.getByRole('dialog')).toBeTruthy()});
it('plays and pauses the selected paper replay one event at a time',async()=>{
 const allocation={id:'manual-a',fund_id:'paper',name:'Manual A',mode:'manual',cash:'1000',reserved:'0',unsettled:'0',net_contributed:'1000',status:'stopped',controller_run_id:''};
 let sequence=0;
 vi.mocked(request).mockImplementation(async path=>{
  if(path==='/funds')return funds;
  if(path==='/allocations')return [allocation];
  if(path==='/engine/backtest/data')return [{snapshot_id:'tape-a'}];
  if(path==='/allocations/manual-a/paper')return {sequence,snapshot:sequence?'tape-a':'',orders:[]};
  return [];
 });
 vi.mocked(send).mockImplementation(async path=>{if(path==='/allocations/manual-a/paper/advance')sequence++;return {}});
 show();await screen.findByText('Paper A · paper');fireEvent.click(screen.getByRole('button',{name:'Manual'}));
 await screen.findByRole('button',{name:'Advance synthetic quote →'});
 fireEvent.click(screen.getByLabelText('I understand this is a synthetic fixture replay'));
 vi.useFakeTimers();fireEvent.click(screen.getByRole('button',{name:'Play replay'}));
 await act(async()=>{await vi.advanceTimersByTimeAsync(1000)});
 expect(send).toHaveBeenCalledWith('/allocations/manual-a/paper/advance',{snapshot:'tape-a',source:'fixture-replay',after:0});
 fireEvent.click(screen.getByRole('button',{name:'Pause replay'}));
 expect(screen.getByRole('button',{name:'Play replay'}).getAttribute('aria-pressed')).toBe('false');
 vi.useRealTimers();
});
