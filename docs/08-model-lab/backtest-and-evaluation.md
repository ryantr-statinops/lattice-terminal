# Backtest và evaluation

**Trạng thái:** protocol mục tiêu; chưa có dataset, scores hoặc tuyên bố lợi nhuận đã kiểm chứng.

**Scope note (2026-10-18):** this file describes a Model Lab/model-evaluation proposal and remains deferred. First-MVP portfolio backtesting is a separate deterministic simulator with Vietnam market/SSI contracts; do not reuse Binance/USDT/model defaults below as active requirements. See [Portfolio](../../07-portfolio/README.md) and [roadmap](../../task/next-plan.md).

## Splits và baselines

Chia theo thời gian, không shuffle. Walk-forward dùng train quá khứ, validation sau train và test sau validation; holdout cuối chỉ mở sau khi khóa preset/features. Purge mọi train sample có label interval giao validation/test; gap/embargo ít nhất bao phủ horizon thực tế và latency, không cố định một số bars cho mọi target. Nếu tái dùng fold sau làm train, loại các sample còn overlap theo interval. Scaler, imputer, feature selection và calibration chỉ fit train của fold.

Price-only/news-only/combined so sánh trên cùng intersection sample, timestamps, splits, costs và seeds; báo cáo riêng số rows bị mất vì coverage. Nếu news point-in-time chưa đủ thì hoãn so sánh, không thay bằng published-at backfill. Báo cáo từng asset/timeframe/horizon, không gộp để che khác biệt.

| Target | Model đầu tiên | Baseline phù hợp |
|---|---|---|
| Direction | Logistic regression | Train class frequency/constant probability; momentum direction |
| Return | Ridge | Zero/no-change; trailing momentum |
| Volatility | Ridge | Constant train mean; trailing realized volatility |

Regularization/preset được chọn trên validation. Không tối ưu trực tiếp trên holdout hoặc thử vô hạn rồi chỉ công bố lần tốt nhất. Lưu tất cả experiment IDs được so sánh, số trials và cảnh báo selection bias. Output volatility âm bị clip 0 theo model version, báo tỷ lệ clipping và metric trước/sau clipping.

## Execution và portfolio simulation

Backtest là spot long/cash với vốn khởi đầu USDT, không short/leverage. Default strategy chuyển long khi direction probability > 0,5 hoặc predicted return > 0; otherwise cash; volatility target chỉ báo risk, không tự tạo strategy. Threshold tùy chỉnh là experiment config được khóa trước test. Không cộng return của các positions chồng horizon như các khoản độc lập.

Simulator một vị thế trên mỗi instrument: entry khi đủ điều kiện, giữ h bars, exit ở executable proxy đã định nghĩa rồi mới xem signal mới. Hai asset có sleeves vốn bằng nhau cố định trong preset so sánh, không chi tiêu cùng một cash hai lần. Fee và slippage tính trên từng lần mua/bán, initial/final liquidation policy hiển thị; zero-cost chỉ là sensitivity case. Không có fee schedule đã xác minh thì người dùng nhập giả định và báo cáo ghi assumed.

Dùng [label/execution timestamps](features-and-targets.md) và giá quan sát tiếp theo. Nến OHLCV không chứng minh order-book fill, spread hoặc capacity; chạy sensitivity theo costs/latency và không diễn giải đây là execution simulator chính xác. USDT là đơn vị kết quả; không mặc định đổi USD/VND. Có benchmark cash và buy-and-hold cùng thời kỳ/vốn/cost conventions.

## Báo cáo tách prediction và strategy

- Direction: class balance, confusion matrix, balanced accuracy, log loss, Brier/calibration bins; accuracy không đủ.
- Return/volatility: MAE, RMSE, error theo regime/fold; return thêm sign accuracy, volatility thêm clipping diagnostics.
- Strategy: net P&L/return, equity, max drawdown, exposure, turnover, trade count và cost breakdown, so với cash/hold. Annualized metrics phải ghi sample duration/convention; quá ít observations thì không công bố như kết luận ổn định.
- Ghi train/validation/test ranges, excluded samples, fit warnings và kết quả từng fold. Không chỉ hiển thị trung bình hoặc cherry-pick một asset.

Prediction tốt hơn baseline không tự chứng minh giao dịch sinh lời; net backtest tốt không bảo đảm alpha tương lai. Không gọi result browser là server-verified.

## Scenarios nghiệm thu P08

Synthetic fixtures có outcome biết trước cho phí, round-trip, hold/cash, gap bars và position overlap. Adversarial fixture chèn future news/bar phải bị chặn; split có horizon overlap bị purge. Test class chỉ có một nhãn, zero variance, dataset quá ngắn, solver fail và holdout rỗng phải báo lỗi hợp lệ. Chạy lại cùng snapshot/runtime/seed trong tolerance đã ghi; so browser output với reference fixture do dự án kiểm soát, không nâng mọi kết quả user thành trusted.
