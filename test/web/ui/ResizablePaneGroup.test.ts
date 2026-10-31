import {expect,it} from 'vitest';
import {fitPanes} from '@web/ui/ResizablePaneGroup';
it('bounds panes and reserves editor space at desktop and tablet widths',()=>{for(const width of [589,845,1051,1680]){const result=fitPanes({left:800,right:800},width);expect(result.left).toBeGreaterThanOrEqual(150);expect(result.right).toBeGreaterThanOrEqual(150);expect(result.left+result.right+296).toBeLessThanOrEqual(Math.max(596,width))}});
