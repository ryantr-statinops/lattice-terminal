const DB_NAME = 'kestrel_drafts';
const DB_VERSION = 1;
const STORE_NAME = 'file_drafts';

let dbPromise: Promise<IDBDatabase | null> | null = null;
const memoryFallback = new Map<string, string>();

function openDB(): Promise<IDBDatabase | null> {
  if (typeof indexedDB === 'undefined') {
    return Promise.resolve(null);
  }
  if (!dbPromise) {
    dbPromise = new Promise(resolve => {
      try {
        const req = indexedDB.open(DB_NAME, DB_VERSION);
        req.onupgradeneeded = () => {
          const db = req.result;
          if (!db.objectStoreNames.contains(STORE_NAME)) {
            db.createObjectStore(STORE_NAME, {keyPath: 'key'});
          }
        };
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => resolve(null);
      } catch {
        resolve(null);
      }
    });
  }
  return dbPromise;
}

export async function saveDraft(kind: string, path: string, content: string): Promise<void> {
  const key = `${kind}:${path}`;
  const db = await openDB();
  if (!db) {
    memoryFallback.set(key, content);
    return;
  }
  return new Promise(resolve => {
    try {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.put({key, kind, path, content, updatedAt: Date.now()});
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    } catch {
      memoryFallback.set(key, content);
      resolve();
    }
  });
}

export async function getDraft(kind: string, path: string): Promise<string | null> {
  const key = `${kind}:${path}`;
  const db = await openDB();
  if (!db) {
    return memoryFallback.get(key) ?? null;
  }
  return new Promise(resolve => {
    try {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.get(key);
      req.onsuccess = () => {
        const result = req.result as {content: string} | undefined;
        resolve(result ? result.content : (memoryFallback.get(key) ?? null));
      };
      req.onerror = () => resolve(memoryFallback.get(key) ?? null);
    } catch {
      resolve(memoryFallback.get(key) ?? null);
    }
  });
}

export async function deleteDraft(kind: string, path: string): Promise<void> {
  const key = `${kind}:${path}`;
  memoryFallback.delete(key);
  const db = await openDB();
  if (!db) return;
  return new Promise(resolve => {
    try {
      const tx = db.transaction(STORE_NAME, 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      store.delete(key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => resolve();
    } catch {
      resolve();
    }
  });
}

export async function loadAllDrafts(kind: string): Promise<Record<string, string>> {
  const db = await openDB();
  const result: Record<string, string> = {};
  for (const [k, v] of memoryFallback.entries()) {
    if (k.startsWith(`${kind}:`)) {
      result[k.slice(kind.length + 1)] = v;
    }
  }
  if (!db) return result;

  return new Promise(resolve => {
    try {
      const tx = db.transaction(STORE_NAME, 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();
      req.onsuccess = () => {
        const items = req.result as Array<{key: string; kind: string; path: string; content: string}>;
        for (const item of items) {
          if (item.kind === kind) {
            result[item.path] = item.content;
          }
        }
        resolve(result);
      };
      req.onerror = () => resolve(result);
    } catch {
      resolve(result);
    }
  });
}
