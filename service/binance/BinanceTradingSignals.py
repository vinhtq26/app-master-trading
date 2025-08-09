import json
import asyncio
from binance import Client, AsyncClient

client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                    "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")

async def fetch_klines_for_symbol(symbol, interval, limit=100):
    async with AsyncClient("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                          "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA") as async_client:
        klines = await async_client.get_klines(symbol=symbol, interval=interval, limit=limit)
        return symbol, klines

async def analyze_long_signals_multi(symbols, interval='5m', limit=100):
    tasks = [fetch_klines_for_symbol(symbol, interval, limit) for symbol in symbols]
    results = await asyncio.gather(*tasks)
    analyzed = {}
    for symbol, klines in results:
        # Chuyển đổi dữ liệu nến sang định dạng bạn cần, ví dụ:
        coin_json = {"data_history": klines}  # Bạn cần chuyển đổi đúng format cho analyze_buy_signal
        try:
            score = analyze_buy_signal(coin_json, interval)
        except Exception as e:
            score = f"Error: {e}"
        analyzed[symbol] = score
    return analyzed

def analyze_buy_signal(coin_json, interval='5m'):
    data = coin_json["data_history"][-5:]  # last 5 candles
    # Convert all needed fields to float for calculation
    for d in data:
        d["macd"]["MACD"] = float(d["macd"]["MACD"])
        d["macd"]["Signal"] = float(d["macd"]["Signal"])
        d["macd"]["Histogram"] = float(d["macd"]["Histogram"])
        d["ema"]["EMA_10"] = float(d["ema"]["EMA_10"])
        d["ema"]["EMA_20"] = float(d["ema"]["EMA_20"])
        d["ema"]["EMA_50"] = float(d["ema"]["EMA_50"])
        d["rsi"]["RSI30"] = float(d["rsi"]["RSI30"])
        d["rsi"]["RSI50"] = float(d["rsi"]["RSI50"])
        d["rsi"]["RSI70"] = float(d["rsi"]["RSI70"])
    # Ensure we have exactly 5 candles
    if interval in ['4h', '4H']:
        # --- RSI condition ---
        rsi30_now = data[-1]["rsi"]["RSI30"]
        rsi50_now = data[-1]["rsi"]["RSI50"]
        rsi70_now = data[-1]["rsi"]["RSI70"]
        rsi_cond = rsi30_now > rsi50_now and rsi30_now > rsi70_now
        rsi_past = any(
            data[i]["rsi"]["RSI30"] < data[i]["rsi"]["RSI50"] or data[i]["rsi"]["RSI30"] < data[i]["rsi"]["RSI70"]
            for i in range(-2, -5, -1)
        )
        rsi_ok = rsi_cond and rsi_past

        # --- MACD condition ---
        macd_now = data[-1]["macd"]["MACD"]
        signal_now = data[-1]["macd"]["Signal"]
        hist_now = data[-1]["macd"]["Histogram"]
        macd_cross = macd_now > signal_now and data[-2]["macd"]["MACD"] <= data[-2]["macd"]["Signal"]
        hist_pos = hist_now > -0.01  # dương hoặc gần bằng 0
        # Check if the last positive histogram is not older than 4 candles
        hist_list = [d["macd"]["Histogram"] for d in data]
        last_pos_idx = next((i for i in range(4, -1, -1) if hist_list[i] > 0), None)
        hist_recent = last_pos_idx is not None and (4 - last_pos_idx) <= 3
        macd_ok = macd_cross and hist_pos and hist_recent

        # --- EMA condition ---
        ema10_now = data[-1]["ema"]["EMA_10"]
        ema20_now = data[-1]["ema"]["EMA_20"]
        ema_cond = ema10_now > ema20_now
        ema_past = any(data[i]["ema"]["EMA_10"] < data[i]["ema"]["EMA_20"] for i in range(-2, -5, -1))
        ema_ok = ema_cond and ema_past

        # --- Ranking ---
        count = sum([rsi_ok, macd_ok, ema_ok])
        if count == 3:
            ranking_long = 10
        elif count >= 1:
            ranking_long = 9
        else:
            ranking_long = 0

        return {
            "time": interval,
            "trading_signal": "Long",
            "percent": 100 if ranking_long == 10 else (90 if ranking_long == 9 else 0),
            "ranking_long": ranking_long,
            "rsi_ok": rsi_ok,
            "macd_ok": macd_ok,
            "ema_ok": ema_ok
        }

    elif interval in ['1d', '1D']:
        ema10_now = data[-1]["ema"]["EMA_10"]
        ema20_now = data[-1]["ema"]["EMA_20"]
        ema50_now = data[-1]["ema"]["EMA_50"]
        cond1 = ema10_now > ema20_now
        cond2 = ema10_now > ema50_now

        # --- MACD condition ---
        macd_now = data[-1]["macd"]["MACD"]
        signal_now = data[-1]["macd"]["Signal"]
        hist_now = data[-1]["macd"]["Histogram"]
        macd_cross = macd_now > signal_now and data[-2]["macd"]["MACD"] <= data[-2]["macd"]["Signal"]
        hist_list = [d["macd"]["Histogram"] for d in data]
        last_pos_idx = next((i for i in range(4, -1, -1) if hist_list[i] > 0), None)
        hist_recent = last_pos_idx is not None and (4 - last_pos_idx) <= 3
        hist_pos = hist_now > -20
        macd_ok = macd_cross and hist_pos and hist_recent

        if cond1 and cond2:
            ranking_long = 10
        elif cond1 or cond2 or macd_ok:
            ranking_long = 9
        else:
            ranking_long = 0
        return {
            "time": interval,
            "trading_signal": "Long",
            "percent": 100 if ranking_long == 10 else (90 if ranking_long == 9 else 0),
            "ranking_long": ranking_long,
            "ema10_gt_ema20": cond1,
            "ema10_gt_ema50": cond2,
            "macd_ok": macd_ok
        }


    # --- MACD Histogram group ---
    hist = [d["macd"]["Histogram"] for d in data]
    hist_increasing = all(hist[i] < hist[i+1] for i in range(4))
    hist_non_positive = all(h <= 0 for h in hist)
    hist_increasing_any = all(hist[i] < hist[i+1] for i in range(4))
    hist_positive_count = sum(h > 0 for h in hist)
    hist_current_positive = hist[-1] > 0
    hist_current_positive_5th = hist_positive_count == 5 and hist_current_positive
    hist_3down_2up = all(hist[i] > hist[i+1] for i in range(2)) and hist[2] < hist[3] < hist[4]

    histogram_long = False
    ranking_histogram = 0
    if (hist_increasing and hist_non_positive) or \
       (hist_increasing_any and not hist_current_positive_5th) or \
       hist_3down_2up:
        histogram_long = True
        ranking_histogram = 10

    # --- MACD group ---
    macd = [d["macd"]["MACD"] for d in data]
    signal = [d["macd"]["Signal"] for d in data]
    macd_signal_pairs = list(zip(macd, signal))
    macd_diff = [m - s for m, s in macd_signal_pairs]
    macd_long = False
    ranking_macd = 0

    macd_now, signal_now = macd[-1], signal[-1]
    hist_now = hist[-1]
    # TH1
    if macd_now < 0 and signal_now < 0 and macd_now < signal_now:
        if macd_diff[-2] > macd_diff[-1]:
            ranking_macd = 8
    # TH2
    elif macd_now < 0 and signal_now < 0 and macd_now >= signal_now:
        ranking_macd = 9
    # TH3
    elif macd_now > 0 and signal_now < 0 and not hist_current_positive_5th:
        ranking_macd = 9
    # TH4
    elif macd_now > 0 and signal_now > 0 and macd_now < signal_now:
        if macd_diff[-2] > macd_diff[-1]:
            ranking_macd = 8
    # TH5
    elif macd_now > 0 and signal_now > 0 and macd_now > signal_now and not hist_current_positive_5th:
        ranking_macd = 10

    # --- RSI group ---
    rsi30 = [d["rsi"]["RSI30"] for d in data]
    rsi50 = [d["rsi"]["RSI50"] for d in data]
    rsi70 = [d["rsi"]["RSI70"] for d in data]
    rsi_check = rsi30[-1] > rsi50[-1] and rsi30[-1] > rsi70[-1]
    ranking_rsi = 0
    if all(rsi30[i] > rsi50[i] and rsi30[i] > rsi70[i] for i in range(5)):
        ranking_rsi = 10
    elif rsi30[-1] > rsi50[-1] and rsi30[-1] > rsi70[-1] and rsi30[-2] > rsi50[-2] and rsi30[-2] > rsi70[-2]:
        ranking_rsi = 9

    # --- EMA group ---
    ema10 = [d["ema"]["EMA_10"] for d in data]
    ema20 = [d["ema"]["EMA_20"] for d in data]
    ema50 = [d["ema"]["EMA_50"] for d in data]
    ema_check = ema10[-1] > ema20[-1] and ema10[-1] > ema50[-1]
    ranking_ema = 0
    if ema_check:
        # Find how many candles from the end where ema10 > ema20 and ema50
        count = 0
        for i in range(4, -1, -1):
            if ema10[i] > ema20[i] and ema10[i] > ema50[i]:
                count += 1
            else:
                break
        if count in [1, 2, 3]:
            ranking_ema = 10
        else:
            ranking_ema = 9
    elif ema10[-1] > ema20[-1]:
        ranking_ema = 9

    # --- Final decision ---
    percent = 60
    trading_signal = "Long"
    if ranking_histogram == 10 and ranking_macd == 10 and ranking_ema == 10:
        percent = 100
    elif ranking_ema == 10 and ranking_macd == 10:
        percent = 90
    elif ranking_rsi == 10 and ranking_macd == 10:
        percent = 80
    elif ranking_ema == 10 and ranking_rsi == 10:
        percent = 90
    elif ranking_ema == 10 and ranking_macd < 10 and ranking_rsi < 10:
        percent = 90
    elif ranking_macd == 10 and ranking_ema < 10 and ranking_rsi < 10:
        percent = 90

    return {
        "time": interval,
        "trading_signal": trading_signal,
        "percent": percent,
        "ranking_histogram": ranking_histogram,
        "ranking_macd": ranking_macd,
        "ranking_rsi": ranking_rsi,
        "ranking_ema": ranking_ema
    }


async def getAllCoinUSDT():
    try:
        exchange_info = client.futures_exchange_info()
        usdt_symbols = [
            s["symbol"] for s in exchange_info["symbols"]
            if s["contractType"] == "PERPETUAL" and s["quoteAsset"] == "USDT"
        ]
        return usdt_symbols
    except Exception as e:
        return {"error": str(e)}