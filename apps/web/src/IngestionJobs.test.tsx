// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {IngestionJobs} from './IngestionJobs';
import {request,send} from './api';

vi.mock('./api',()=>({request:vi.fn(),send:vi.fn()}));
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
 expect(screen.getByText(/does not resume an interrupted request/)).toBeDefined();
 fireEvent.click(screen.getByRole('button',{name:'Refresh jobs'}));
 await waitFor(()=>expect(request).toHaveBeenCalledTimes(2));
});

it('shows an empty state when no provider ingestion has run',async()=>{
 vi.mocked(request).mockResolvedValue([]);
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><IngestionJobs/></QueryClientProvider>);
 expect(await screen.findByText('No ingestion jobs have been recorded.')).toBeDefined();
});

it('starts the supported SSI catalogue sync and refreshes its job list',async()=>{
 vi.mocked(request).mockResolvedValue([]);
 vi.mocked(send).mockResolvedValue({job:{status:'completed'},snapshot_id:'abcdefghijklmnop'});
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><IngestionJobs canSyncSsiHoseEquity/></QueryClientProvider>);
 fireEvent.click(await screen.findByRole('button',{name:'Sync SSI HOSE stocks'}));
 await waitFor(()=>expect(send).toHaveBeenCalledWith('/ingestion/catalogues/ssi/hose-equity',{}));
 expect(await screen.findByText('SSI HOSE catalogue saved as snapshot abcdefghijkl.')).toBeDefined();
});

it('starts the supported SSI HOSE index catalogue sync',async()=>{
 vi.mocked(request).mockResolvedValue([]);
 vi.mocked(send).mockResolvedValue({job:{status:'completed'},snapshot_id:'mnopqrstuvwx1234'});
 render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><IngestionJobs canSyncSsiHoseIndices/></QueryClientProvider>);
 fireEvent.click(await screen.findByRole('button',{name:'Sync SSI HOSE indices'}));
 await waitFor(()=>expect(send).toHaveBeenCalledWith('/ingestion/catalogues/ssi/hose-indices',{}));
 expect(await screen.findByText('SSI HOSE index catalogue saved as snapshot mnopqrstuvwx.')).toBeDefined();
});
