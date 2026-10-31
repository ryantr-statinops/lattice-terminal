// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {act,cleanup,render,waitFor} from '@testing-library/react';
import {Plot} from '@web/Plot';
import {resetAppearance,setColor} from '@web/theme/store';
const plotly=vi.hoisted(()=>({react:vi.fn<(element:HTMLElement,data:unknown,layout:Record<string,unknown>,config:unknown)=>Promise<void>>(async()=>{}),purge:vi.fn(),Plots:{resize:vi.fn()}}));
vi.mock('plotly.js-basic-dist-min',()=>({default:plotly}));
let resize:()=>void;
class Observer{constructor(callback:()=>void){resize=callback}observe(){}disconnect(){}}
afterEach(()=>{cleanup();resetAppearance();vi.clearAllMocks();vi.unstubAllGlobals()});
it('restyles a live Plotly graph without purging its view and purges only on unmount',async()=>{vi.stubGlobal('ResizeObserver',Observer);const data=[{x:[1,2],y:[2,3]}];const view=render(<Plot data={data} title="Research"/>);await waitFor(()=>expect(plotly.react).toHaveBeenCalledOnce());act(()=>setColor('series1','#ABCDEF'));await waitFor(()=>expect(plotly.react).toHaveBeenCalledTimes(2));expect(plotly.purge).not.toHaveBeenCalled();expect(plotly.react.mock.calls.at(-1)?.[2]).toMatchObject({uirevision:'Research',colorway:['#ABCDEF',expect.any(String),expect.any(String),expect.any(String)]});view.unmount();expect(plotly.purge).toHaveBeenCalledOnce()});

it('does not resize an uninitialized or unmounted plot when an observer callback is queued',async()=>{vi.stubGlobal('ResizeObserver',Observer);const view=render(<Plot data={[]} title="Queued resize"/>);act(()=>resize());expect(plotly.Plots.resize).not.toHaveBeenCalled();await waitFor(()=>expect(plotly.react).toHaveBeenCalledOnce());view.unmount();act(()=>resize());expect(plotly.Plots.resize).not.toHaveBeenCalled()});
