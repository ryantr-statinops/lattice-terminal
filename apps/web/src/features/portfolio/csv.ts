import { validateHoldingDraft, type HoldingDraft } from "./validation";

export interface CsvPreviewRow extends HoldingDraft {
  lineNumber: number;
  error?: string;
}

interface CsvRecord {
  lineNumber: number;
  fields: string[];
}

interface CsvParseResult {
  rows: CsvPreviewRow[];
  parseError: string | null;
}

function readRecords(text: string): { records: CsvRecord[]; error: string | null } {
  const records: CsvRecord[] = [];
  let fields: string[] = [];
  let field = "";
  let inQuotes = false;
  let afterQuote = false;
  let lineNumber = 1;
  let rowStart = 1;

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    if (inQuotes) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i += 1;
      } else if (char === '"') {
        inQuotes = false;
        afterQuote = true;
      } else {
        field += char;
        if (char === "\n") lineNumber += 1;
      }
      continue;
    }

    if (afterQuote && char !== "," && char !== "\r" && char !== "\n" && !/\s/.test(char)) {
      return { records: [], error: `CSV sai cấu trúc tại dòng ${lineNumber}` };
    }
    if (afterQuote && /\s/.test(char) && char !== "\r" && char !== "\n") continue;

    if (char === '"') {
      if (field.trim() !== "" || afterQuote) {
        return { records: [], error: `CSV sai cấu trúc tại dòng ${lineNumber}` };
      }
      field = "";
      inQuotes = true;
    } else if (char === ",") {
      fields.push(field.trim());
      field = "";
      afterQuote = false;
    } else if (char === "\r" || char === "\n") {
      if (char === "\r" && text[i + 1] === "\n") i += 1;
      fields.push(field.trim());
      if (fields.some((value) => value !== "")) records.push({ lineNumber: rowStart, fields });
      fields = [];
      field = "";
      afterQuote = false;
      lineNumber += 1;
      rowStart = lineNumber;
    } else {
      field += char;
    }
  }

  if (inQuotes) return { records: [], error: `CSV chưa đóng dấu ngoặc kép tại dòng ${rowStart}` };
  fields.push(field.trim());
  if (fields.some((value) => value !== "")) records.push({ lineNumber: rowStart, fields });
  return { records, error: null };
}

export function parseHoldingsCsv(text: string): CsvParseResult {
  const { records, error } = readRecords(text.replace(/^\uFEFF/, ""));
  if (error) return { rows: [], parseError: error };
  if (records.length === 0) return { rows: [], parseError: null };

  const header = records[0].fields.map((value) => value.toLowerCase());
  if (new Set(header).size !== header.length) {
    return { rows: [], parseError: "Header CSV không được trùng tên cột" };
  }
  const instrumentIndex = header.indexOf("instrument_id");
  const amountIndex = header.indexOf("amount");
  const costIndex = header.indexOf("avg_cost");
  if (instrumentIndex < 0 || amountIndex < 0 || costIndex < 0) {
    return { rows: [], parseError: "Header phải có instrument_id,amount,avg_cost" };
  }

  const rows = records.slice(1).map(({ lineNumber, fields }): CsvPreviewRow => {
    const row: CsvPreviewRow = {
      lineNumber,
      instrument_id: fields[instrumentIndex] ?? "",
      amount: fields[amountIndex] ?? "",
      avg_cost: fields[costIndex] ?? "",
    };
    if (fields.length !== header.length) {
      return { ...row, error: `Số cột không khớp header tại dòng ${lineNumber}` };
    }
    const result = validateHoldingDraft(row);
    return result.valid ? { ...result.holding, lineNumber } : { ...row, error: result.error };
  });

  return { rows, parseError: null };
}
