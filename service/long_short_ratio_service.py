import logging

import aiohttp

from config.binance_config import ENDPOINTS as BINANCE_ENDPOINTS
from config.bybit_config import ENDPOINTS as BYBIT_ENDPOINTS
from config.mexc_config import ENDPOINTS as MEXC_ENDPOINTS

"""
bybit
{
  "exchange": "bybit",
  "timeframe": "15m",
  "symbol": "BTCUSDT",
  "category":"linear" 
}

binance: 
{
    "exchange": "binance",
    "timeframe": "15m",
    "symbol": "BTCUSDT",
    "category": "linear"
}
"""
async def fetch_long_short_ratio(exchange: str, timeframe: str, symbol: str, category: str = None):
    base_urls = {
        "binance": BINANCE_ENDPOINTS["global_long_short"],
        "mexc": MEXC_ENDPOINTS["long_short_ratio"],
        "bybit": BYBIT_ENDPOINTS["account_ratio"]
    }

    if exchange.lower() not in base_urls:
        return {"error": "Unsupported exchange. Supported exchanges: binance, mexc, bybit."}

    url = base_urls[exchange.lower()]
    params = {
        "symbol": symbol,
        "period": timeframe,
        "limit": 1
    }

    if exchange.lower() == "mexc":
        params["symbol"] = symbol.replace("_", "")  # Adjust symbol format for MEXC

    if exchange.lower() == "bybit" and category:
        params["category"] = category  # Use category only if provided

    logging.info(f"Fetching long-short ratio from {exchange} endpoint: {url} with params: {params}")

    if exchange.lower() == "bybit" and timeframe.endswith("m"):
        timeframe = timeframe.replace("m", "min")  # Convert '15m' to '15min' for Bybit
        params["period"] = timeframe

    if exchange.lower() == "binance":
        async with aiohttp.ClientSession() as session:
            # Fetch data from global long-short ratio endpoint
            async with session.get(BINANCE_ENDPOINTS["global_long_short"], params=params) as global_response:
                if global_response.status == 200:
                    global_data = await global_response.json()
                else:
                    return {"error": f"Failed to fetch global long-short data. HTTP status: {global_response.status}"}

            # Fetch data from top trader long-short ratio endpoint
            async with session.get(BINANCE_ENDPOINTS["top_trader"], params=params) as top_trader_response:
                if top_trader_response.status == 200:
                    top_trader_data = await top_trader_response.json()
                else:
                    return {"error": f"Failed to fetch top trader long-short data. HTTP status: {top_trader_response.status}"}

            # Merge data from both endpoints
            if isinstance(global_data, list) and len(global_data) > 0:
                global_result = global_data[0]
            else:
                return {"error": "Unexpected response format from global long-short endpoint."}

            if isinstance(top_trader_data, list) and len(top_trader_data) > 0:
                top_trader_result = top_trader_data[0]
            else:
                return {"error": "Unexpected response format from top trader endpoint."}

            return {
                "symbol": global_result["symbol"],
                "long_ratio": float(global_result["longAccount"]) * 100,
                "short_ratio": float(global_result["shortAccount"]) * 100,
                "toptrader_long_ratio": float(top_trader_result["longAccount"]) * 100,
                "toptrader_short_ratio": float(top_trader_result["shortAccount"]) * 100,
                "timestamp": global_result["timestamp"]
            }
