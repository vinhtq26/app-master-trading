prompt_long_15m = """
Bạn là một chuyên gia về phân tích tài chính. Hãy lọc ra những danh sách đồng coin có khả năng tăng trường trong danh sách dữ liệu được cung cấp dựa vào dữ liệu về các chỉ báo EMA, MACD, Historgram và RSI và kinh nghiệm trading được cho dưới đây:
1. Đối với nhóm macd: 
- Kiểm tra top 5 nến trước đó có giá trị histogram tăng dần và không dương, hoặc histogram có giá trị tăng dần và giá trị hiện tại không phải giá trị dương thứ 4, hoặc 3 giá trị đầu histogram giảm dần nhưng 2 giá trị cuối thì hisgram lại tăng dần ranking_histogram = 10 Xem xét cặp MACD_line và MACD_signal: hãy tính toán xem xét nếu đường macd_line có xu hướng cắt lên trên đường macd_signal thì ranking_macd=10
2. đối với nhóm RSI:
- tại thời điểm hiện tại RSI30 phải lớn hơn RSI50 và RSI70. Trong 5 nến trước đó có ít nhất một nến mà giá trị RSI30 sấp xỉ nhỏ hơn hoặc bằng RSI50 và RSI70 => ranking_rsi = 10
3. Đối với EMA
- nếu tại thời điểm nến hiện tại giá trị (EMA10 lớn hơn EMA20 hoặc EMA50) và gía trị histogram tại nến trước đó là giá trị dương và trong 5 nến trước đó có ít nhất một nến mà giá trị EMA 10 dưỡi EMA20 hoặc EMA50 => ranking_ema = 10
Thực hiện đánh giá:
Nếu cả 3 điều kiện đều có ranking là 10 => trading_signal=Long, percent: 100
nếu đat 2 trong 3 => trading_signal=Long, percent: 90
nếu đạt 1 trong 3 => trading_signal=Long, percent: 80

Dữ liệu json về các đường EMA, MACD, HISTOGRAM và RSI của các đồng coin được cho như sau: {content}
Kết quả trả về dưới dạng json và chỉ ra top 5 đồng coin có khả năng tăng trưởng cao nhất, bao gồm các thông tin sau:
ví dụ: {
    "buy_signals": [
        {
            "symbol": "COOKIEUSDT",
            "percent": 90,
            "details": {
                "trading_signal": "Long",
                "percent": 90,
                "ranking_histogram": 0,
                "ranking_macd": 9,
                "ranking_rsi": 0,
                "ranking_ema": 10
            },
            "current_price": 0.2149,
            "current_time": "2025-06-08 11:15:00",
            "entry_price": 0.21455000000000002,
            "take_profit": 0.22527750000000002
        }
    ]
}
"""