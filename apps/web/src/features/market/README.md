# Market feature

Market view gồm BTC/ETH, nến 15m/1h/1d, chart Lightweight Charts và watchlist local. Candles và chart dùng synthetic fixtures. Binance WebSocket là opt-in, theo asset/interval đang chọn, chỉ báo trạng thái kết nối và không cập nhật chart/portfolio. Nhãn tuổi dữ liệu dựa timestamp nến đã đóng, không dựa trạng thái cache query.
