// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {TabBar} from '@web/workspace/TabBar';

afterEach(cleanup);

it('renders tabs with active and dirty indicators, handles select and close', () => {
  const onSelect = vi.fn();
  const onClose = vi.fn();

  render(
    <TabBar
      files={['strategy.py', 'helpers/math.py']}
      active="strategy.py"
      buffers={{'strategy.py': 'edited', 'helpers/math.py': 'same'}}
      saved={{'strategy.py': 'original', 'helpers/math.py': 'same'}}
      onSelect={onSelect}
      onClose={onClose}
    />
  );

  const activeTab = screen.getByRole('tab', {name: /strategy\.py/});
  expect(activeTab.getAttribute('aria-selected')).toBe('true');
  expect(screen.getByTitle('Unsaved changes')).toBeDefined();

  const secondTab = screen.getByRole('tab', {name: /math\.py/});
  expect(secondTab.getAttribute('aria-selected')).toBe('false');

  fireEvent.click(secondTab);
  expect(onSelect).toHaveBeenCalledWith('helpers/math.py');

  const closeBtn = screen.getByRole('button', {name: 'Close strategy.py'});
  fireEvent.click(closeBtn);
  expect(onClose).toHaveBeenCalledWith('strategy.py');
});
