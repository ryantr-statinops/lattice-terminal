import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { CsvImport } from "./CsvImport";

class DeferredFileReader {
  static instances: DeferredFileReader[] = [];
  result: string | null = null;
  onload: ((event: ProgressEvent<FileReader>) => unknown) | null = null;
  onerror: ((event: ProgressEvent<FileReader>) => unknown) | null = null;
  onabort: ((event: ProgressEvent<FileReader>) => unknown) | null = null;
  abort = vi.fn();

  constructor() {
    DeferredFileReader.instances.push(this);
  }

  readAsText() {}

  complete(text: string) {
    this.result = text;
    this.onload?.({ target: this as unknown as FileReader } as ProgressEvent<FileReader>);
  }
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  DeferredFileReader.instances = [];
});

describe("CSV import UI", () => {
  it("replaces previews and ignores a stale read that finishes after the newer file", async () => {
    vi.stubGlobal("FileReader", DeferredFileReader);
    const onImport = vi.fn(() => true);
    render(<CsvImport onImport={onImport} />);
    const input = screen.getByLabelText("Chọn file CSV");

    fireEvent.change(input, {
      target: { files: [new File(["old"], "old.csv", { type: "text/csv" })] },
    });
    const oldReader = DeferredFileReader.instances[0];
    fireEvent.change(input, {
      target: { files: [new File(["new"], "new.csv", { type: "text/csv" })] },
    });
    const currentReader = DeferredFileReader.instances[1];

    act(() => {
      oldReader.complete("instrument_id,amount,avg_cost\nbinance:spot:BTCUSDT,1,2");
      currentReader.complete("instrument_id,amount,avg_cost\nbinance:spot:ETHUSDT,0.5,3000");
    });

    expect(screen.queryByText("binance:spot:BTCUSDT")).toBeNull();
    expect(screen.getByText("binance:spot:ETHUSDT")).toBeTruthy();
    await userClick(screen.getByRole("button", { name: "Nhập 1 dòng" }));
    expect(onImport).toHaveBeenCalledOnce();
    expect(onImport).toHaveBeenCalledWith([
      { instrument_id: "binance:spot:ETHUSDT", amount: "0.5", avg_cost: "3000" },
    ]);
  });

  it("does not import a preview that contains any invalid row", () => {
    vi.stubGlobal("FileReader", DeferredFileReader);
    const onImport = vi.fn();
    render(<CsvImport onImport={onImport} />);
    const input = screen.getByLabelText("Chọn file CSV");

    fireEvent.change(input, {
      target: { files: [new File(["rows"], "rows.csv", { type: "text/csv" })] },
    });
    act(() => {
      DeferredFileReader.instances[0].complete(
        "instrument_id,amount,avg_cost\nbinance:spot:BTCUSDT,1,2\nbinance:spot:ETHUSDT,0,3",
      );
    });

    expect(screen.getByRole("button", { name: "Nhập 1 dòng" }).hasAttribute("disabled")).toBe(true);
    expect(onImport).not.toHaveBeenCalled();
  });
});

async function userClick(button: HTMLElement) {
  fireEvent.click(button);
}
