import { useCallback, useState } from "react";
import type { Holding, PortfolioState } from "./types";
import { validateHoldingDraft, validateStoredHolding } from "./validation";

const STORAGE_KEY = "rt:portfolio";
const EMPTY_STATE: PortfolioState = { holdings: [], updatedAt: null };
const SAVE_ERROR = "Không lưu được danh mục trên thiết bị này; dữ liệu vẫn còn trong phiên hiện tại.";

interface PortfolioLoad {
  state: PortfolioState;
  warning: string | null;
}

function read(): PortfolioLoad {
  let raw: string | null;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch {
    return { state: EMPTY_STATE, warning: "Không đọc được danh mục đã lưu trên thiết bị này." };
  }
  if (!raw) return { state: EMPTY_STATE, warning: null };

  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return { state: EMPTY_STATE, warning: "Dữ liệu danh mục đã lưu bị lỗi; chưa thay đổi dữ liệu gốc." };
  }
  if (!parsed || typeof parsed !== "object") {
    return { state: EMPTY_STATE, warning: "Dữ liệu danh mục đã lưu không hợp lệ; chưa thay đổi dữ liệu gốc." };
  }

  const record = parsed as Record<string, unknown>;
  if (!Array.isArray(record.holdings)) {
    return { state: EMPTY_STATE, warning: "Dữ liệu danh mục đã lưu không hợp lệ; chưa thay đổi dữ liệu gốc." };
  }
  const holdings: Holding[] = [];
  for (const item of record.holdings) {
    const result = validateStoredHolding(item);
    if (result.valid) holdings.push(result.holding);
  }

  const updatedAt =
    typeof record.updatedAt === "string" && Number.isFinite(Date.parse(record.updatedAt))
      ? record.updatedAt
      : null;
  const skipped = record.holdings.length - holdings.length;
  return {
    state: { holdings, updatedAt },
    warning: skipped > 0 ? `Đã bỏ qua ${skipped} holding lỗi; dữ liệu gốc vẫn được giữ nguyên.` : null,
  };
}

function write(state: PortfolioState): boolean {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    return true;
  } catch {
    return false;
  }
}

export function usePortfolio() {
  const [initial] = useState(read);
  const [state, setState] = useState<PortfolioState>(initial.state);
  const [storageWarning, setStorageWarning] = useState<string | null>(initial.warning);
  const [validationError, setValidationError] = useState<string | null>(null);

  const commit = useCallback((next: PortfolioState) => {
    setState(next);
    if (write(next)) {
      setStorageWarning(null);
      setValidationError(null);
    } else {
      setStorageWarning(SAVE_ERROR);
    }
  }, []);

  const addMany = useCallback((values: readonly unknown[]) => {
    const drafts = values.map((value) => validateHoldingDraft(value));
    const invalid = drafts.find((result) => !result.valid);
    if (invalid && !invalid.valid) {
      setValidationError(invalid.error);
      return false;
    }

    const holdings = drafts
      .filter((result): result is Extract<typeof result, { valid: true }> => result.valid)
      .map(({ holding }) => ({ ...holding, id: crypto.randomUUID() }));
    if (holdings.length === 0) return false;

    commit({
      holdings: [...state.holdings, ...holdings],
      updatedAt: new Date().toISOString(),
    });
    return true;
  }, [commit, state.holdings]);

  const add = useCallback((holding: Omit<Holding, "id">) => addMany([holding]), [addMany]);

  const remove = useCallback((id: string) => {
    commit({
      holdings: state.holdings.filter((holding) => holding.id !== id),
      updatedAt: new Date().toISOString(),
    });
  }, [commit, state.holdings]);

  const clear = useCallback(() => {
    commit({ holdings: [], updatedAt: new Date().toISOString() });
  }, [commit]);

  return { state, add, addMany, remove, clear, storageWarning, validationError };
}
