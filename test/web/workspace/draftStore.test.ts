import {afterEach,expect,it} from 'vitest';
import {deleteDraft,getDraft,loadAllDrafts,saveDraft} from '@web/workspace/draftStore';

afterEach(async () => {
  await deleteDraft('research', 'test.py');
  await deleteDraft('research', 'other.py');
});

it('saves, retrieves, lists, and deletes drafts using store', async () => {
  await saveDraft('research', 'test.py', 'print("draft content")');
  const content = await getDraft('research', 'test.py');
  expect(content).toBe('print("draft content")');

  await saveDraft('research', 'other.py', 'print("other")');
  const all = await loadAllDrafts('research');
  expect(all['test.py']).toBe('print("draft content")');
  expect(all['other.py']).toBe('print("other")');

  await deleteDraft('research', 'test.py');
  const deleted = await getDraft('research', 'test.py');
  expect(deleted).toBeNull();
});
