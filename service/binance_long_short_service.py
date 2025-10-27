import asyncio
import logging
import time

import aiohttp

from cache.CacheWithTTL import PERIOD_TTL, cache
from service.app import get_coin_image_url

API_LIMIT_PER_SECOND = 40
REQUESTS_PER_SYMBOL = 2
MAX_RETRIES = 3
RETRY_DELAY = 3

async def fetch_with_retry(session, url, params, semaphore):
    total_requests = 0
    total_retries = 0
    for attempt in range(MAX_RETRIES):
        try:
            async with semaphore:
                async with session.get(url, params=params, timeout=10) as resp:
                    total_requests += 1
                    if resp.status == 429:
                        total_retries += 1
                        logging.warning(f"429 Too Many Requests → Retry {attempt+1}")
                        await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                        continue
                    return await resp.json()
        except Exception as e:
            total_retries += 1
            logging.error(f"{e} → Retry {attempt+1}")
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))
    return None

async def fetch_symbol_data(session, symbol, endpoints, period, semaphore):
    results = {}
    for key, url in endpoints.items():
        params = {
            "symbol": symbol,
            "period": period,
            "limit": 1
        }
        data = await fetch_with_retry(session, url, params, semaphore)
        if data and isinstance(data, list):
            latest = data[0]
            results[key] = {
                "long_pct": float(latest["longAccount"]) * 100,
                "short_pct": float(latest["shortAccount"]) * 100
            }
    return symbol, results

async def fetch_all_symbols(symbols, endpoints, period, batch_size, batch_delay):
    semaphore = asyncio.Semaphore(batch_size)
    async with aiohttp.ClientSession() as session:
        results = {}
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            tasks = [fetch_symbol_data(session, sym, endpoints, period, semaphore) for sym in batch]
            batch_results = await asyncio.gather(*tasks)
            results.update(dict(batch_results))
            if i + batch_size < len(symbols):
                await asyncio.sleep(batch_delay)
        return results

async def filter_symbols(period, top_symbols, endpoints):
    cache_key = f"filter_symbols_{period}"

    logging.info(f"[FILTER_SYMBOLS] Period: {period}, Endpoints: {endpoints}")

    # Lấy từ cache nếu có
    cached_result = cache.get(cache_key)
    if cached_result:
        logging.info(f"[CACHE] Dùng dữ liệu cache cho period {period}")
        return cached_result

    # Nếu không có cache → fetch từ Binance
    max_symbols_per_second = API_LIMIT_PER_SECOND / REQUESTS_PER_SYMBOL
    batch_size = int(max_symbols_per_second)
    batch_delay = 1

    fetched_data = await fetch_all_symbols(top_symbols, endpoints, period, batch_size, batch_delay)
    result_long_high = []
    result_short_high = []

    for sym, ratios in fetched_data.items():
        global_data = ratios.get("global")
        top_data = ratios.get("toptrader")
        if not global_data or not top_data:
            continue

        # Long cao
        if (global_data["long_pct"] > 60 and global_data["short_pct"] < 40 and
                top_data["long_pct"] > 60 and top_data["short_pct"] < 40):
            result_long_high.append({
                "symbol": sym,
                "image_url": get_coin_image_url(sym),
                "global": global_data,
                "toptrader": top_data
            })

        # Short cao
        if (global_data["long_pct"] < 40 and global_data["short_pct"] > 60 and
                top_data["long_pct"] < 40 and top_data["short_pct"] > 60):
            result_short_high.append({
                "symbol": sym,
                "image_url": get_coin_image_url(sym),
                "global": global_data,
                "toptrader": top_data
            })

    # Sắp xếp
    result_long_high.sort(key=lambda x: x["global"]["long_pct"], reverse=True)
    result_short_high.sort(key=lambda x: x["global"]["short_pct"], reverse=True)

    final_result = (result_long_high, result_short_high)

    # Lưu cache
    cache.set(cache_key, final_result, PERIOD_TTL.get(period, 300))

    return final_result

async def get_binance_long_short(period, client):
    start_time = time.time()

    # Lấy danh sách top 400 coin USDT
    tickers = client.futures_ticker()
    sorted_tickers = sorted(
        tickers, key=lambda x: float(x['quoteVolume']), reverse=True
    )
    top_symbols = [t['symbol'] for t in sorted_tickers if t['symbol'].endswith('USDT')][:400]

    base_url = "https://fapi.binance.com/futures/data"
    endpoints = {
        "global": f"{base_url}/globalLongShortAccountRatio",
        "toptrader": f"{base_url}/topLongShortAccountRatio"
    }

    result_long_high, result_short_high = await filter_symbols(period, top_symbols, endpoints)

    elapsed_time = round(time.time() - start_time, 2)
    logging.info(f"[DONE] Hoàn tất sau {elapsed_time}s")

    return {
        "long_high": result_long_high,
        "short_high": result_short_high,
        "stats": {
            "time_seconds": elapsed_time
        }
    }
