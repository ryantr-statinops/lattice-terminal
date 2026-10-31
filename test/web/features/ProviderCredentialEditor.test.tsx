// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {ProviderCredentialEditor} from '@web/ProviderCredentialEditor';
import {send} from '@web/api';

vi.mock('@web/api',()=>({send:vi.fn()}));
afterEach(()=>{cleanup();vi.clearAllMocks();localStorage.clear()});

it('saves write-only credentials without persisting them in browser storage',async()=>{
  localStorage.setItem('existing-setting','kept');
  vi.mocked(send).mockResolvedValue(null);
  const onSaved=vi.fn();
  render(<ProviderCredentialEditor providerId="ssi" onCancel={vi.fn()} onSaved={onSaved}/>);
  fireEvent.change(screen.getByLabelText('Credential field 1'),{target:{value:'consumer_secret'}});
  fireEvent.change(screen.getByLabelText('Credential value 1'),{target:{value:'private-secret'}});
  fireEvent.click(screen.getByRole('button',{name:'Save credentials'}));
  await waitFor(()=>expect(send).toHaveBeenCalledWith('/providers/ssi/credentials',{
    service:'market-data',credential:{consumer_secret:'private-secret'},
  },'PUT'));
  expect(onSaved).toHaveBeenCalledOnce();
  expect(localStorage.getItem('existing-setting')).toBe('kept');
  expect(localStorage.length).toBe(1);
  expect((screen.getByLabelText('Credential value 1') as HTMLInputElement).value).toBe('');
});

it('rejects duplicate credential field names before sending',async()=>{
  const writer=vi.mocked(send);
  render(<ProviderCredentialEditor providerId="dnse" onCancel={vi.fn()} onSaved={vi.fn()}/>);
  fireEvent.change(screen.getByLabelText('Credential field 1'),{target:{value:'api_key'}});
  fireEvent.change(screen.getByLabelText('Credential value 1'),{target:{value:'first'}});
  fireEvent.click(screen.getByRole('button',{name:'Add field'}));
  fireEvent.change(screen.getByLabelText('Credential field 2'),{target:{value:'api_key'}});
  fireEvent.change(screen.getByLabelText('Credential value 2'),{target:{value:'second'}});
  fireEvent.click(screen.getByRole('button',{name:'Save credentials'}));
  expect((await screen.findByRole('alert')).textContent).toContain('Credential field names must be unique.');
  expect(writer).not.toHaveBeenCalled();
});
