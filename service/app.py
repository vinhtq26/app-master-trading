from typing import List
import time
import asyncio
import aiohttp

from fastapi import Query, Request
from binance.client import Client

from service import trading_signal_short, trading_signal_long
from service.funding import fundingInfo
from utils.DiscordUtils import send_discord_notification, DISCORD_WEBHOOK_URL_Funding
from service.funding.coin_cmc_id_map import SYMBOL_TO_CMC_ID

client = Client("ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ",
                "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA")
# Sửa lỗi chính tả "singal" -> "signal"
# https://fapi.binance.com/fapi/v1/klines đầy đủ hơn https://api.binance.com/api/v3/klines?s
async def fetch_batch_klines_optimized(symbols, interval, limit):
    base_url = "https://fapi.binance.com/fapi/v1/klines"
    try:
        async with aiohttp.ClientSession() as session:
            tasks = [
                session.get(base_url, params={"symbol": symbol, "interval": interval, "limit": limit})
                for symbol in symbols
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

            valid_results = {}
            for symbol, response in zip(symbols, responses):
                if isinstance(response, aiohttp.ClientResponse):
                    async with response:
                        if response.status == 200:
                            valid_results[symbol] = await response.json()
                        else:
                            print(f"Error fetching data for {symbol}: HTTP {response.status}")
                else:
                    print(f"Error fetching data for {symbol}: {response}")

            return valid_results
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

async def trading_long_signal_position(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m")):
    start_time = time.time()

    tickers = client.futures_ticker()
    sorted_tickers = sorted(
        tickers, key=lambda x: float(x['quoteVolume']), reverse=True
    )
    top_symbols = [t['symbol'] for t in sorted_tickers if t['symbol'].endswith('USDT')][:100]

    klines_data = await fetch_batch_klines_optimized(top_symbols, interval, 500)

    results = []
    for symbol, klines in klines_data.items():
        try:
            data = trading_signal_long.process_klines(klines)
            if not data.get("data_history"):
                print(f"Missing data_history for {symbol}")
                continue

            signal = trading_signal_long.analyze_buy_signal(data, interval=interval)
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
                    entry_price = price_now * 0.99 if min_prev > price_now else (min_prev + price_now) / 2
                    take_profit = entry_price * 1.05

                    results.append({
                        "symbol": symbol,
                        "position": "Long",
                        "percent": signal['percent'],
                        "details": signal,
                        "current_price": price_now,
                        "current_time": time_now,
                        "entry_price": entry_price,
                        "take_profit": take_profit,
                        "url_image": get_coin_image_url(symbol)
                    })
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    top_results = sorted(results, key=lambda x: x['percent'], reverse=True)[:50]

    print(f"Execution time: {time.time() - start_time} seconds")
    return {"buy_signals": top_results}


async def trading_long_detail_signal_position(
    interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m"),
    symbols: List[str] = Query(None, description="List of symbols to filter, e.g. BTCUSDT, ETHUSDT")
):

    top_symbols = symbols if symbols else []
    results = []
    for symbol in top_symbols:
        try:
            data = trading_signal_long.get_coin_technical_data(coin_symbol=symbol, interval=interval)
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
                        "take_profit": take_profit,
                        "url_image": get_coin_image_url(symbol)
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
async def trading_short_signal_position(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m")):
    start_time = time.time()

    tickers = client.futures_ticker()
    sorted_tickers = sorted(
        tickers, key=lambda x: float(x['quoteVolume']), reverse=True
    )
    top_symbols = [t['symbol'] for t in sorted_tickers if t['symbol'].endswith('USDT')][:100]

    klines_data = await fetch_batch_klines_optimized(top_symbols, interval, 500)

    results = []
    for symbol, klines in klines_data.items():
        try:
            data = trading_signal_short.process_klines(klines)
            if not data.get("data_history"):
                print(f"Missing data_history for {symbol}")
                continue

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
                    entry_price = price_now * 1.01 if max_prev < price_now else (max_prev + price_now) / 2
                    take_profit = entry_price * 0.95

                    results.append({
                        "symbol": symbol,
                        "position": "Short",
                        "percent": signal['ranking_short'] * 10,
                        "details": signal,
                        "current_price": price_now,
                        "current_time": time_now,
                        "entry_price": entry_price,
                        "take_profit": take_profit,
                        "url_image": get_coin_image_url(symbol)
                    })
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    top_results = sorted(results, key=lambda x: x['percent'], reverse=True)[:50]

    print(f"Execution time: {time.time() - start_time} seconds")
    return {"short_signals": top_results}
async def trading_short_detail_signal_position(interval: str = Query('5m', description="Kline interval, e.g. 1m, 5m, 15m"), symbols: List[str] = Query(None, description="List of symbols to filter, e.g. BTCUSDT, ETHUSDT")):

    # Get top 1000 symbols
    top_symbols = symbols if symbols else []

    results = []
    for symbol in top_symbols:
        try:
            data = trading_signal_long.get_coin_technical_data(coin_symbol=symbol, interval=interval)
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
    funding_summary = await fundingInfo.fundingRate()
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

# Helper to get coin symbol and image url
def get_coin_image_url(symbol):
    # Remove _ and USDT suffix
    base = symbol.replace('_', '').replace('USDT', '').replace('USD', '')
    # Special case: if symbol starts with A_ (e.g. A_UST), remove _
    if '_' in symbol:
        base = symbol.split('_')[0]
    cmc_id = SYMBOL_TO_CMC_ID.get(base)
    if cmc_id:
        return f"https://s2.coinmarketcap.com/static/img/coins/64x64/{cmc_id}.png"
    return None

