// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import {EditorBoundary} from './EditorBoundary';
afterEach(()=>{cleanup();vi.restoreAllMocks()});
it('contains a failed lazy editor without blanking the surrounding workspace',()=>{vi.spyOn(console,'error').mockImplementation(()=>{});function Broken():null{throw Error('chunk unavailable')}render(<><h1>Research</h1><EditorBoundary><Broken/></EditorBoundary></>);expect(screen.getByRole('heading',{name:'Research'})).toBeTruthy();expect(screen.getByRole('alert').textContent).toContain('Không tải được editor');expect(screen.getByRole('button',{name:'Tải lại ứng dụng'})).toBeTruthy()});
