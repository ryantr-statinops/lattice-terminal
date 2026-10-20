// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {request} from './api';
import {money} from './Assets';
import {programTemplate} from './templates';
afterEach(()=>vi.unstubAllGlobals());
it('does not round large decimal balances through Number',()=>expect(money('9007199254740993.01')).toBe('9.007.199.254.740.993,01'));
it('keeps the three program contracts separate',()=>{expect(programTemplate('research')).toContain('"research"');expect(programTemplate('backtest')).toContain('context.replay');expect(programTemplate('strategy')).toContain('def on_event');expect(programTemplate('strategy')).not.toContain('def run(')});
it('dispatches a lock on an expired private API session',async()=>{const listener=vi.fn();window.addEventListener('kestrel:locked',listener);vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response('session locked',{status:401})));await expect(request('/portfolio')).rejects.toThrow('session locked');expect(listener).toHaveBeenCalledOnce();window.removeEventListener('kestrel:locked',listener)});
it('sends same-origin credentials and preserves decimal JSON strings',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response('{"cash":"9007199254740993.01"}'));vi.stubGlobal('fetch',fetcher);expect(await request('/portfolio')).toEqual({cash:'9007199254740993.01'});expect(fetcher.mock.calls[0][1].credentials).toBe('same-origin')});
