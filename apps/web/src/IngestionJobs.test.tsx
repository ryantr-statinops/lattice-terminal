// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {IngestionJobs} from './IngestionJobs';
import {request} from './api';

vi.mock('./api',()=>({request:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks()});

it('shows durable ingestion progress, restart checkpoint and safe error code',async()=>{
 vi.mocked(request).mockResolvedValue([{
  id:'job-ssi-eod',provider_id:'ssi',capability_id:'ssi:market-data:candles.1d:equity:HOSE',dataset:'candles.1d',asset_class:'equity',venue:'HOSE',
  status:'interrupted',processed_records:250,total_records:1000,error_code:'process_restarted',
  checkpoint:{version:4,kind:'page',value:'5'},created_at:'2026-10-27T01:00:00Z',updated_at:'2026-10-27T02:00:00Z',
 }]);
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><IngestionJobs/></QueryClientProvider>);
 expect(await screen.findByText('250 / 1000')).toBeDefined();
 expect(screen.getByText('page 5 · v4')).toBeDefined();
 expect(screen.getByText('process_restarted')).toBeDefined();
 expect(screen.getByText(/does not start or resume provider requests/)).toBeDefined();
 fireEvent.click(screen.getByRole('button',{name:'Refresh jobs'}));
 await waitFor(()=>expect(request).toHaveBeenCalledTimes(2));
});

it('shows an empty state when no provider ingestion has run',async()=>{
 vi.mocked(request).mockResolvedValue([]);
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><IngestionJobs/></QueryClientProvider>);
 expect(await screen.findByText('No ingestion jobs have been recorded.')).toBeDefined();
});
