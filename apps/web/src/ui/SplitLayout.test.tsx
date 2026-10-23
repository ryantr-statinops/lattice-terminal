// @vitest-environment jsdom
import {afterEach,expect,it} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {SplitLayout} from './SplitLayout';

afterEach(cleanup);

it('renders split layout with first and second panes', () => {
  render(
    <SplitLayout
      first={<div data-testid="first-pane">Editor</div>}
      second={<div data-testid="second-pane">Terminal</div>}
      initialRatio={0.6}
    />
  );

  expect(screen.getByTestId('first-pane')).toBeDefined();
  expect(screen.getByTestId('second-pane')).toBeDefined();
  const separator = screen.getByRole('separator');
  expect(separator).toBeDefined();
  expect(separator.getAttribute('aria-valuenow')).toBe('60');

  // Double click resets to 50
  fireEvent.doubleClick(separator);
  expect(separator.getAttribute('aria-valuenow')).toBe('50');

  // Arrow keys resize ratio
  fireEvent.keyDown(separator, {key: 'ArrowRight'});
  expect(separator.getAttribute('aria-valuenow')).toBe('55');
});
