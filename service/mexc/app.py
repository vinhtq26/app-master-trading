import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import List

import pandas as pd
import pytz
from fastapi import FastAPI, Query
import uvicorn
from binance.client import Client
from service import trading_signal_short, trading_signal_long
from service.binance import BinanceTradingSignals
from service.funding import fundingInfo
from service.mexc import trading_signal_long_mexc, trading_signal_short_mexc
from utils.DiscordUtils import send_discord_notification, DISCORD_WEBHOOK_URL_Funding
from service.mexc.MexcTradingSignals import MexcTradingSignals
from cache.CacheWithTTL import cache, PERIOD_TTL

executor = ThreadPoolExecutor(max_workers=10)
client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")
# Sửa lỗi chính tả "singal" -> "signal"
async def trading_long_signal_position_mexc(interval: str = Query('5m', description="Kline interval")):
    # Check cache for top symbols
    cache_key = f"top_symbols_{interval}"
    top_symbols = cache.get(cache_key)

    if not top_symbols:
        # Fetch top symbols if not in cache
        top_symbols = await MexcTradingSignals.getAllCoinMexc(limit=100)
        ttl = PERIOD_TTL.get(interval, 300)  # Default TTL is 5 minutes
        cache.set(cache_key, top_symbols, ttl)

    # Run tasks in parallel
    tasks = [process_symbol(symbol, interval) for symbol in top_symbols]
    results = await asyncio.gather(*tasks)

    # Filter out None results
    results = [r for r in results if r]

    return {"buy_signals": results}


# ====== PROCESS SYMBOL ======
async def process_symbol(symbol, interval):
    try:
        loop = asyncio.get_event_loop()

        # chạy trong threadpool để không block event loop
        data = await loop.run_in_executor(executor, get_coin_technical_data_fast, symbol, interval)
        signal = await loop.run_in_executor(executor, trading_signal_long_mexc.analyze_buy_signal, data, interval)

        if signal['percent'] != 60:
            candles = data["data_history"]
            if len(candles) >= 2:
                prev_candle = candles[-2]
                last_candle = candles[-1]
                open_prev = float(prev_candle["open"])
                close_prev = float(prev_candle["close"])
                price_now = float(last_candle["close"])
                time_now = last_candle.get("time")
                min_prev = min(open_prev, close_prev)

                if min_prev > price_now:
                    entry_price = price_now * 0.99
                else:
                    entry_price = (min_prev + price_now) / 2

                take_profit = entry_price * 1.05

                return {
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "time": time_now,
                    "signal": signal,
                    "current_price": price_now
                }
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
    return None

async def trading_long_detail_signal_position_mexc(
    interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m"),
    symbols: List[str] = Query(None, description="List of symbols to filter, e.g. BTCUSDT, ETHUSDT")
):

    top_symbols = symbols if symbols else []
    results = []
    for symbol in top_symbols:
        try:
            data = trading_signal_long_mexc.get_coin_technical_data(coin_symbol=symbol, interval=interval)
            signal = trading_signal_long.analyze_buy_signal(data, interval=interval)
            if signal['percent'] != 60:
                # Get last two candles
                candles = data["data_history"]
                if len(candles) >= 2:
                    prev_candle = candles[-2]
                    last_candle = candles[-1]
                    open_prev = float(prev_candle["open"])
                    close_prev = float(prev_candle["close"])
                    price_now = float(last_candle["close"])
                    time_now = last_candle.get("time")  # adjust key if needed
                    min_prev = min(open_prev, close_prev)
                    if min_prev > price_now:
                        entry_price = price_now * 0.99
                    else:
                        entry_price = (min_prev + price_now) / 2
                    take_profit = entry_price * 1.05

                    results.append({
                        "symbol": symbol,
                        "position": "Long",
                        "percent": signal['percent'],
                        "details": signal,
                        "current_price": price_now,
                        "current_time": time_now,
                        "entry_price": entry_price,
                        "take_profit": take_profit
                    })
        except Exception as e:
            continue  # Skip coins with errors

    top_results = sorted(results, key=lambda x: x['percent'], reverse=True)[:50]
    msg = "Top 5 buy signals:\n" + "\n".join(
        [f"{i + 1}. {r['symbol']} ({r['percent']}%)" for i, r in enumerate(top_results[:5])]
    )
    # send_discord_notification(msg)
    return {"buy_signals": top_results}
 # Sửa lỗi chính tả "singal" -> "signal"
async def trading_short_signal_position_mexc(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m")):
    # Check cache for top symbols
    cache_key = f"short_top_symbols_{interval}"
    top_symbols = cache.get(cache_key)

    if not top_symbols:
        # Fetch top symbols if not in cache
        tickers = client.futures_ticker()
        sorted_tickers = sorted(
            tickers, key=lambda x: float(x['quoteVolume']), reverse=True
        )
        top_symbols = [t['symbol'].replace('_', '') for t in sorted_tickers if t['symbol'].endswith('USDT')][:100]
        ttl = PERIOD_TTL.get(interval, 300)  # Default TTL is 5 minutes
        cache.set(cache_key, top_symbols, ttl)

    # Run tasks in parallel
    tasks = [process_short_symbol(symbol, interval) for symbol in top_symbols]
    results = await asyncio.gather(*tasks)

    # Filter out None results
    results = [r for r in results if r]

    return {"short_signals": results}


async def process_short_symbol(symbol, interval):
    try:
        loop = asyncio.get_event_loop()

        # Run in threadpool to avoid blocking event loop
        data = await loop.run_in_executor(executor, get_coin_technical_data_fast, symbol, interval)
        signal = await loop.run_in_executor(executor, trading_signal_short_mexc.analyze_short_signal, data, interval)

        if signal['ranking_short'] != 0:
            candles = data["data_history"]
            if len(candles) >= 2:
                prev_candle = candles[-2]
                last_candle = candles[-1]
                open_prev = float(prev_candle["open"])
                close_prev = float(prev_candle["close"])
                price_now = float(last_candle["close"])
                time_now = last_candle.get("time")
                max_prev = max(open_prev, close_prev)

                entry_price = price_now * 1.01 if max_prev < price_now else (max_prev + price_now) / 2
                take_profit = entry_price * 0.95

                return {
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "take_profit": take_profit,
                    "time": time_now,
                    "signal": signal
                }
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
    return None

async def trading_short_detail_signal_position_mexc(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m"), symbols: List[str] = Query(None, description="List of symbols to filter, e.g. BTCUSDT, ETHUSDT")):

    # Get top 1000 symbols
    top_symbols = symbols if symbols else []

    results = []
    for symbol in top_symbols:
        try:
            data = trading_signal_long_mexc.get_coin_technical_data(coin_symbol=symbol, interval=interval)
            signal = trading_signal_short.analyze_short_signal(data, interval=interval)
            if signal['ranking_short'] != 0:
                candles = data["data_history"]
                if len(candles) >= 2:
                    prev_candle = candles[-2]
                    last_candle = candles[-1]
                    open_prev = float(prev_candle["open"])
                    close_prev = float(prev_candle["close"])
                    price_now = float(last_candle["close"])
                    time_now = last_candle.get("time")

                    max_prev = max(open_prev, close_prev)
                    if max_prev < price_now:
                        entry_price = price_now * 1.01
                    else:
                        entry_price = (max_prev + price_now) / 2
                    take_profit = entry_price * 0.95

                    results.append({
                        "symbol": symbol,
                        "position": "Short",
                        "percent": signal['ranking_short'] * 10,
                        "details": signal,
                        "current_price": price_now,
                        "current_time": time_now,
                        "entry_price": entry_price,
                        "take_profit": take_profit
                    })
        except Exception as e:
            continue  # Skip coins with errors

    top_results = sorted(results, key=lambda x: x['percent'], reverse=True)[:50]
    # msg = "Top 5 buy signals:\n" + "\n".join(
    #     [f"{i + 1}. {r['symbol']} ({r['percent']}%)" for i, r in enumerate(top_results[:5])]
    # )
    # send_discord_notification(msg)
    return {"short_signals": top_results}
async def getFunding():
    funding_summary = fundingInfo.fundingRate()
    msg = "Funding Rates:\n"
    msg += "\nBinance:\n" + "\n".join(
        [f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})" for item in funding_summary['binance']]
    )
    msg += "\n\nMEXC:\n" + "\n".join(
        [f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})" for item in funding_summary['mexc']]
    )
    msg += "\n\nBybit:\n" + "\n".join(
        [f"{item['symbol']}: {item['fundingRatePercent']}% Price: {item['markPrice']} (Trend: {item['fundingTrend']})" for item in funding_summary['bybit']]
    )
    send_discord_notification(msg, DISCORD_WEBHOOK_URL_Funding)
    return funding_summary
def get_coin_technical_data_fast(coin_symbol='BTCUSDT', interval='5m', limit=500):
    df = trading_signal_long_mexc.calculate_technical_indicators(coin_symbol, interval, limit)

    # chỉ lấy 10 nến cuối
    recent = df.tail(10)
    vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')

    data_history = []
    for _, row in recent.iterrows():
        ts = row['timestamp']
        if not hasattr(ts, 'tzinfo') or ts.tzinfo is None:
            ts = pd.to_datetime(ts, unit='ms', utc=True)
        ts = ts.tz_convert(vn_timezone)

        data_history.append({
            "time": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "open": str(row['open']),
            "close": str(row['close']),
            "high": str(row['high']),
            "low": str(row['low']),
            "volume": str(row['volume']),
            "macd": {
                "MACD": str(row['MACD_line']),
                "Signal": str(row['Signal_line']),
                "Histogram": str(row['Histogram'])
            },
            "ema": {
                "EMA_10": str(row['EMA_10']),
                "EMA_20": str(row['EMA_20']),
                "EMA_50": str(row['EMA_50'])
            },
            "rsi": {
                "RSI30": str(row['RSI_30']),
                "RSI50": str(row['RSI_50']),
                "RSI70": str(row['RSI_70'])
            }
        })

    return {
        "symbol": coin_symbol,
        "interval": interval,
        "data_history": data_history,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }