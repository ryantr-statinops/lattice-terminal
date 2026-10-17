import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ModelLabPage } from "./ModelLabPage";

afterEach(cleanup);

describe("Model Lab placeholder", () => {
  it("labels placeholder results as simulated before and after running", async () => {
    render(<ModelLabPage />);

    expect(screen.getByText("Kết quả mẫu — chưa chạy training/backtest.")).toBeTruthy();
    expect(screen.getByText("Cấu hình hiện tại chưa được dùng để tính các chỉ số.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Chạy mô phỏng giao diện" }));
    await act(async () => new Promise((resolve) => setTimeout(resolve, 350)));

    expect(screen.getByText("simulated")).toBeTruthy();
    expect(screen.getByText("Nguồn kết quả: mock · không phải kết quả đánh giá mô hình.")).toBeTruthy();
    expect(screen.queryByText("completed")).toBeNull();
  });
});
