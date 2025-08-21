import aiohttp
import logging
from config.binance_config import ENDPOINTS as BINANCE_ENDPOINTS
from config.mexc_config import ENDPOINTS as MEXC_ENDPOINTS
from config.bybit_config import ENDPOINTS as BYBIT_ENDPOINTS
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

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()

                # Normalize output for Bybit
                if exchange.lower() == "bybit":
                    if data.get("retCode") == 0 and "list" in data.get("result", {}):
                        result = data["result"]["list"][0]
                        return {
                            "symbol": result["symbol"],
                            "longRatio": result["buyRatio"],
                            "shortRatio": result["sellRatio"],
                            "timestamp": result["timestamp"]
                        }

                # Normalize output for Binance
                elif exchange.lower() == "binance":
                    if isinstance(data, list) and len(data) > 0:
                        result = data[0]
                        return {
                            "symbol": result["symbol"],
                            "longRatio": result["longAccount"],
                            "shortRatio": result["shortAccount"],
                            "timestamp": result["timestamp"]
                        }

                return {"error": "Unexpected response format from exchange."}
            else:
                return {"error": f"Failed to fetch data from {exchange}. Status code: {response.status}"}