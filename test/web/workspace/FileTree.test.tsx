// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {FileTree} from '@web/workspace/FileTree';
afterEach(cleanup);
it('preserves a keyboard entry point after the focused file is renamed',()=>{const props={width:210,active:'a.py',selected:'a.py',buffers:{},saved:{},collapsed:new Set<string>(),busy:false,onSelect:vi.fn(),onDirectory:vi.fn(),onCreate:vi.fn(),onRename:vi.fn(),onDelete:vi.fn()};const view=render(<FileTree {...props} files={[{path:'a.py',directory:false},{path:'b.py',directory:false}]}/>);screen.getByRole('treeitem',{name:/a.py/}).focus();fireEvent.keyDown(screen.getByRole('tree'),{key:'ArrowDown'});expect(document.activeElement).toBe(screen.getByRole('treeitem',{name:/b.py/}));view.rerender(<FileTree {...props} active="a.py" files={[{path:'a.py',directory:false},{path:'renamed.py',directory:false}]}/>);expect(screen.getByRole('treeitem',{name:/a.py/}).tabIndex).toBe(0)});
