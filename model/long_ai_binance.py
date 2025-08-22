from fastapi import Query

from service.llm.trading_signal_long_llm import get_coin_technical_data_llm
from service.trading_signal_long import analyze_buy_signal
from binance.client import Client

from service.trading_signal_short import analyze_short_signal

client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")

def trading_long_signal_ai_position(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m")):
    # Get all tickers with 24h
    global data
    tickers = client.futures_ticker()
    # Sort by quoteVolume (as float), descending
    sorted_tickers = sorted(
        tickers, key=lambda x: float(x['quoteVolume']), reverse=True
    )
    # Get top 1000 symbols
    top_symbols = [t['symbol'] for t in sorted_tickers if t['symbol'].endswith('USDT')][:50]
    results = []
    for symbol in top_symbols:
        try:
            data = get_coin_technical_data_llm(coin_symbol=symbol, interval=interval)
            results.append(data)
        except Exception as e:
            continue  # Skip coins with errors

    return data

def analyze_candle_patterns(exchange, timeframe, symbol):
    """
    Phân tích mô hình nến nâng cao từ dữ liệu lịch sử giá.
    """
    data = get_coin_technical_data_llm(coin_symbol=symbol, interval=timeframe)
    candles = data.get("data_history", [])
    patterns = []
    for i in range(2, len(candles)):
        prev = candles[i - 1]
        curr = candles[i]

        # Bullish Engulfing
        if float(curr["open"]) < float(prev["close"]):
            if float(curr["close"]) > float(prev["open"]) and float(curr["open"]) < float(prev["close"]):
                patterns.append({"index": i, "pattern": "Bullish Engulfing", "time": curr.get("time")})

        # Shooting Star
        if float(curr["close"]) > float(curr["open"]) and (float(curr["low"]) < float(curr["open"])) and (float(curr["high"]) > float(curr["open"]) * 1.02):
            patterns.append({"index": i, "pattern": "Shooting Star", "time": curr.get("time")})

        # Doji
        if abs(float(curr["open"]) - float(curr["close"])) < (float(curr["high"]) - float(curr["low"])) * 0.1:
            patterns.append({"index": i, "pattern": "Doji", "time": curr.get("time")})

    return patterns

def analyze_support_resistance(exchange, timeframe, symbol):
    """
    Phân tích các vùng kháng cự/hỗ trợ mạnh dựa trên swing high/low, volume và đa khung thời gian.
    """
    data = get_coin_technical_data_llm(coin_symbol=symbol, interval=timeframe)
    candles = data.get("data_history", [])
    closes = [float(c["close"]) for c in candles]
    highs = [float(c["high"]) for c in candles]
    lows = [float(c["low"]) for c in candles]
    volumes = [float(c["volume"]) for c in candles]
    if not closes:
        return {}
    # Xác định swing high/low
    swing_highs = []
    swing_lows = []
    for i in range(1, len(highs)-1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            swing_highs.append(highs[i])
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            swing_lows.append(lows[i])
    # Các vùng kháng cự/hỗ trợ mạnh
    resistance_zones = [h for h in swing_highs if volumes[highs.index(h)] > sum(volumes)/len(volumes)]
    support_zones = [l for l in swing_lows if volumes[lows.index(l)] > sum(volumes)/len(volumes)]
    # Pivot zone như cũ
    from collections import Counter
    rounded = [round(c, -int(len(str(int(c)))/2)) for c in closes]
    freq = Counter(rounded)
    pivot_zone = [k for k, v in freq.items() if v > 2]
    return {
        "support": min(support_zones) if support_zones else min(closes),
        "resistance": max(resistance_zones) if resistance_zones else max(closes),
        "pivot_zone": pivot_zone,
        "support_zones": support_zones,
        "resistance_zones": resistance_zones
    }

def analyze_volume(exchange, timeframe, symbol):
    """
    Phân tích volume breakout, phân kỳ, volume tăng đột biến.
    """
    data = get_coin_technical_data_llm(coin_symbol=symbol, interval=timeframe)
    volumes = [float(c["volume"]) for c in data.get("data_history", [])]
    closes = [float(c["close"]) for c in data.get("data_history", [])]
    if not volumes:
        return {}
    avg_volume = sum(volumes) / len(volumes)
    max_volume = max(volumes)
    min_volume = min(volumes)
    # Tìm volume breakout
    breakout = []
    for i in range(1, len(volumes)):
        if volumes[i] > avg_volume * 2 and abs(closes[i] - closes[i-1]) > closes[i-1]*0.01:
            breakout.append({"index": i, "volume": volumes[i], "price_move": closes[i]-closes[i-1]})
    return {
        "avg_volume": avg_volume,
        "max_volume": max_volume,
        "min_volume": min_volume,
        "breakout": breakout
    }

def analyze_trade_suggestion(exchange, timeframe, symbol):
    """
    Đưa ra gợi ý vào lệnh, stoploss, takeprofit, cảnh báo rủi ro dựa trên phân tích kỹ thuật tổng hợp.
    """
    candle_patterns = analyze_candle_patterns(exchange, timeframe, symbol)
    sr = analyze_support_resistance(exchange, timeframe, symbol)
    vol = analyze_volume(exchange, timeframe, symbol)
    # Xác định điểm vào lệnh: Nếu có mô hình nến đảo chiều gần vùng hỗ trợ/kháng cự và volume breakout
    entry = None
    stoploss = None
    takeprofit = None
    risk_warning = []
    if candle_patterns and vol['breakout']:
        # Ưu tiên mô hình đảo chiều gần vùng hỗ trợ
        for p in candle_patterns:
            if sr['support_zones'] and abs(p.get('time', 0) - sr['support']) < sr['support']*0.01:
                entry = sr['support']
                stoploss = entry * 0.98
                takeprofit = sr['resistance']
                break
        # Nếu không có, ưu tiên breakout volume
        if not entry and vol['breakout']:
            entry = vol['breakout'][-1]['price_move'] + sr['support']
            stoploss = entry * 0.98
            takeprofit = sr['resistance']
    # Cảnh báo rủi ro nếu volume thấp hoặc không có mô hình nến đảo chiều
    if not candle_patterns:
        risk_warning.append('Không có mô hình nến đảo chiều rõ ràng, nên thận trọng.')
    if vol['avg_volume'] < vol['max_volume']*0.3:
        risk_warning.append('Volume thấp, thị trường có thể không đủ động lực.')
    return {
        'entry': entry,
        'stoploss': stoploss,
        'takeprofit': takeprofit,
        'risk_warning': risk_warning,
        'candle_patterns': candle_patterns,
        'support_resistance': sr,
        'volume': vol
    }


def get_long_signal(exchange, timeframe, symbol, limit=150):
    """
    Lấy tín hiệu long cho một symbol cụ thể với số lượng nến tuỳ chọn (mặc định 150 cho phân tích sâu).
    """
    data = get_coin_technical_data(coin_symbol=symbol, interval=timeframe, limit=limit)
    signal = analyze_buy_signal(data, interval=timeframe)
    return {
        "symbol": symbol,
        "signal": signal,
        "data": data
    }

def get_short_signal(exchange, timeframe, symbol, limit=150):
    """
    Lấy tín hiệu short cho một symbol cụ thể với số lượng nến tuỳ chọn (mặc định 150 cho phân tích sâu).
    """
    data = get_coin_technical_data(coin_symbol=symbol, interval=timeframe, limit=limit)
    signal = analyze_short_signal(data, interval=timeframe)
    return {
        "symbol": symbol,
        "signal": signal,
        "data": data
    }