import json
from datetime import datetime

import service.trading_signal_long as long_signal
import service.binance.BinanceTradingSignals as binance_signals
import service.trading_signal_short as short_signal
from model.long_ai_binance import analyze_candle_patterns, analyze_support_resistance, analyze_volume
from model.Gemini import Gemini
def get_long_short_detail_llm_binance(exchange, timeframe, symbol):
    # Lấy dữ liệu từ các module long/short
    long_data = long_signal.get_long_signal(exchange, timeframe, symbol)
    short_data = short_signal.get_short_signal(exchange, timeframe, symbol)

    # Phân tích thêm
    support_resistance = analyze_support_resistance(exchange, timeframe, symbol)
    volume_analysis = analyze_volume(exchange, timeframe, symbol)
    candle_patterns = analyze_candle_patterns(exchange, timeframe, symbol)

    # Tổng hợp dữ liệu thành phân tích dạng string tự nhiên
    analysis = []
    analysis.append(f"Phân tích tín hiệu LONG cho {symbol} trên sàn {exchange}, khung {timeframe}:")
    if long_data['signal'].get('percent', 0) > 0:
        analysis.append(f"- Tín hiệu LONG mạnh với xác suất {long_data['signal'].get('percent', 0)}%. Lý do: {long_data['signal'].get('reason', 'Không rõ lý do.')}")
    else:
        analysis.append("- Không có tín hiệu LONG mạnh.")

    analysis.append(f"Phân tích tín hiệu SHORT cho {symbol}:")
    if short_data['signal'].get('ranking_short', 0) > 0:
        analysis.append(f"- Tín hiệu SHORT mạnh với ranking {short_data['signal'].get('ranking_short', 0)}. Lý do: {short_data['signal'].get('reason', 'Không rõ lý do.')}")
    else:
        analysis.append("- Không có tín hiệu SHORT mạnh.")

    sr = support_resistance
    analysis.append(f"Vùng hỗ trợ: {sr.get('support')}, vùng kháng cự: {sr.get('resistance')}, vùng pivot: {sr.get('pivot_zone')}")
    if sr.get('support_zones') or sr.get('resistance_zones'):
        analysis.append(f"Các vùng hỗ trợ mạnh: {sr.get('support_zones')}, vùng kháng cự mạnh: {sr.get('resistance_zones')}")

    vol = volume_analysis
    analysis.append(f"Volume trung bình: {vol.get('avg_volume')}, volume lớn nhất: {vol.get('max_volume')}, breakout volume: {vol.get('breakout')}")

    patterns = candle_patterns
    if patterns:
        analysis.append(f"Phát hiện các mô hình nến: {[p['pattern'] for p in patterns]}")
    else:
        analysis.append("Không phát hiện mô hình nến đảo chiều đặc biệt.")

    # Tổng hợp dữ liệu kỹ thuật dạng dict để truyền vào prompts
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Lấy giá hiện tại từ dữ liệu long_data (ưu tiên), nếu không có thì để None
    current_price = None
    if 'data' in long_data and 'data_history' in long_data['data'] and long_data['data']['data_history']:
        current_price = long_data['data']['data_history'][-1].get('close')
    data_for_prompt = {
        "symbol": symbol,
        "current_price": current_price,
        "exchange": exchange,
        "timeframe": timeframe,
        "current_time": now,
        "long_signal": long_data['signal'],
        "short_signal": short_data['signal'],
        "support_resistance": support_resistance,
        "volume": volume_analysis,
        "candle_patterns": candle_patterns
    }

    # Prompt chuyên sâu cho LLM, yêu cầu trả về đúng định dạng JSON mẫu, KHÔNG được thêm bất kỳ ký tự nào như ```json hoặc ``` ở đầu/cuối
    prompt_single_coin = f'''
Bạn là một chuyên gia phân tích tài chính chuyên nghiệp với nhiều năm kinh nghiệm thực chiến. Hãy phân tích kỹ thuật cho đồng coin sau dựa trên các dữ liệu kỹ thuật (tín hiệu long/short, vùng hỗ trợ/kháng cự, volume, mô hình nến) và trả về kết quả dưới đúng định dạng JSON mẫu bên dưới.

YÊU CẦU:
- Đây là thông tin giao dịch cho cặp {symbol} trên sàn {exchange}, khung {timeframe}, thời gian hiện tại là {now}.
- Phân tích tổng quan, điểm mạnh/yếu, khuyến nghị giao dịch, entry, stoploss, takeprofit, rủi ro, cảnh báo, disclaimer.
- Trả về đúng định dạng JSON mẫu, KHÔNG thêm bất kỳ text nào ngoài JSON, KHÔNG thêm ```json hay ``` ở đầu/cuối.
- Nếu thiếu dữ liệu, hãy để giá trị null hoặc chuỗi rỗng.

Định dạng JSON mẫu:
{{
  "analysis": {{
    "symbol": "SUIUSDT",
    "exchange": "binance",
    "timeframe": "1h",
    "overview": "...",
    "strengths": ["..."],
    "weaknesses": ["..."],
    "recommendation": "...",
    "entry_price": "...",
    "stoploss": "...",
    "takeprofit": "...",
    "risks": ["..."],
    "disclaimer": "Đây chỉ là phân tích kỹ thuật dựa trên dữ liệu hiện tại, không phải lời khuyên đầu tư. Nhà đầu tư cần tự chịu trách nhiệm cho quyết định của mình."
  }},
  "buy_signals": [
    {{
      "symbol": "SUIUSDT",
      "percent": 60,
      "details": {{
        "trading_signal": "Long",
        "percent": 60,
        "ranking_histogram": 0,
        "ranking_macd": 0,
        "ranking_rsi": 10,
        "ranking_ema": 9
      }},
      "current_price": 3.86,
      "current_time": "2025-08-13 10:00:00",
      "entry_price": 3.86,
      "take_profit": 3.9333
    }}
  ]
}}

Dữ liệu kỹ thuật:
{{content}}
'''
    prompt_text = prompt_single_coin.replace("{content}", str(data_for_prompt))
    llm_result = Gemini.analyze(prompt_text)
    # Loại bỏ phần ```json hoặc ``` nếu có ở đầu/cuối kết quả (phòng trường hợp LLM vẫn sinh ra)
    import re
    if llm_result.strip().startswith("```json"):
        llm_result = re.sub(r"^```json\s*|\s*```$", "", llm_result.strip())
    elif llm_result.strip().startswith("```"):
        llm_result = re.sub(r"^```\s*|\s*```$", "", llm_result.strip())
    return json.loads(llm_result)
