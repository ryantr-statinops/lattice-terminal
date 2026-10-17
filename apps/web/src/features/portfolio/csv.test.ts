import { describe, expect, it } from "vitest";
import { parseHoldingsCsv } from "./csv";

describe("portfolio CSV parser", () => {
  it("supports a BOM, CRLF, reordered columns, and quoted fields", () => {
    const result = parseHoldingsCsv(
      '\uFEFFavg_cost,note,instrument_id,amount\r\n"65000.50","spot, ""long""",binance:spot:BTCUSDT,0.125\r\n',
    );

    expect(result.parseError).toBeNull();
    expect(result.rows).toEqual([
      {
        lineNumber: 2,
        instrument_id: "binance:spot:BTCUSDT",
        amount: "0.125",
        avg_cost: "65000.50",
      },
    ]);
  });

  it("rejects duplicate or missing required headers", () => {
    expect(parseHoldingsCsv("instrument_id,amount,amount,avg_cost\n").parseError).toMatch(/trùng/);
    expect(parseHoldingsCsv("instrument_id,amount\n").parseError).toMatch(/Header phải có/);
  });

  it("rejects malformed quoting, mismatched row widths, and partially parsed numbers", () => {
    expect(parseHoldingsCsv('instrument_id,amount,avg_cost\n"binance:spot:BTCUSDT,1,2').parseError).toMatch(/chưa đóng/);

    const width = parseHoldingsCsv("instrument_id,amount,avg_cost\nbinance:spot:BTCUSDT,1,2,extra");
    expect(width.rows[0].error).toMatch(/Số cột/);

    const number = parseHoldingsCsv("instrument_id,amount,avg_cost\nbinance:spot:BTCUSDT,12abc,2");
    expect(number.rows[0].error).toMatch(/Số lượng/);
  });

  it("keeps all-or-nothing preview rows and preserves source line numbers", () => {
    const result = parseHoldingsCsv(
      "instrument_id,amount,avg_cost\nbinance:spot:BTCUSDT,1,2\nbinance:spot:ETHUSDT,0,3",
    );

    expect(result.rows).toHaveLength(2);
    expect(result.rows[0].lineNumber).toBe(2);
    expect(result.rows[0].error).toBeUndefined();
    expect(result.rows[1].lineNumber).toBe(3);
    expect(result.rows[1].error).toMatch(/Số lượng/);
  });
});
