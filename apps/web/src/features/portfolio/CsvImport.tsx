import { useEffect, useRef, useState } from "react";
import type { Holding } from "./types";
import { parseHoldingsCsv, type CsvPreviewRow } from "./csv";

interface Props {
  onImport: (rows: Omit<Holding, "id">[]) => boolean | void;
}

export function CsvImport({ onImport }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [rows, setRows] = useState<CsvPreviewRow[]>([]);
  const [fileName, setFileName] = useState<string | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const readerRef = useRef<FileReader | null>(null);
  const readGeneration = useRef(0);

  useEffect(() => () => {
    readGeneration.current += 1;
    readerRef.current?.abort();
  }, []);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    const generation = ++readGeneration.current;
    readerRef.current?.abort();
    setRows([]);
    setParseError(null);
    setFileName(file.name);
    const reader = new FileReader();
    readerRef.current = reader;
    reader.onload = () => {
      if (generation !== readGeneration.current) return;
      const text = String(reader.result ?? "");
      const parsed = parseHoldingsCsv(text);
      setRows(parsed.rows);
      setParseError(parsed.parseError);
    };
    reader.onerror = () => {
      if (generation === readGeneration.current) setParseError("Không đọc được file CSV.");
    };
    reader.readAsText(file);
  }

  const validRows = rows.filter((r) => !r.error);
  const hasErrors = rows.some((r) => r.error);

  function handleConfirm() {
    if (validRows.length === 0 || hasErrors) return;
    const accepted = onImport(validRows.map(({ instrument_id, amount, avg_cost }) => ({ instrument_id, amount, avg_cost })));
    if (accepted === false) return;
    setRows([]);
    setFileName(null);
    setParseError(null);
    readGeneration.current += 1;
    readerRef.current?.abort();
    if (inputRef.current) inputRef.current.value = "";
  }

  function handleCancel() {
    readGeneration.current += 1;
    readerRef.current?.abort();
    setRows([]);
    setFileName(null);
    setParseError(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div className="panel grid gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          aria-label="Chọn file CSV"
          accept=".csv,text/csv"
          onChange={handleFile}
          className="text-sm"
        />
        {fileName && <span className="text-xs text-muted-foreground">{fileName}</span>}
      </div>
      {parseError && <p role="alert" className="text-sm text-destructive">{parseError}</p>}

      {(rows.length > 0 || parseError) && (
        <>
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <caption className="sr-only">Xem trước dữ liệu CSV</caption>
              <thead className="bg-secondary text-left text-muted-foreground">
                <tr>
                  <th scope="col" className="px-3 py-2">Dòng</th>
                  <th className="px-3 py-2">Tài sản</th>
                  <th className="px-3 py-2">Số lượng</th>
                  <th className="px-3 py-2">Giá vốn</th>
                  <th className="px-3 py-2">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.lineNumber} className="border-t border-border">
                    <td className="px-3 py-2 text-xs text-muted-foreground">{r.lineNumber}</td>
                    <td className="px-3 py-2 font-mono">{r.instrument_id || "—"}</td>
                    <td className="px-3 py-2 font-mono">{r.amount || "—"}</td>
                    <td className="px-3 py-2 font-mono">{r.avg_cost || "—"}</td>
                    <td className={`px-3 py-2 text-xs ${r.error ? "text-destructive" : "text-primary"}`}>
                      {r.error ?? "OK"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={handleConfirm}
              disabled={validRows.length === 0 || hasErrors || Boolean(parseError)}
              className="rounded-lg bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              Nhập {validRows.length} dòng
            </button>
            <button
              type="button"
              onClick={handleCancel}
              className="rounded-lg border border-border px-3 py-2 text-sm text-foreground hover:bg-secondary"
            >
              Hủy
            </button>
          </div>
          {hasErrors && (
            <p className="text-sm text-destructive">
              Có lỗi trong CSV. Sửa file rồi thử lại.
            </p>
          )}
        </>
      )}
    </div>
  );
}
