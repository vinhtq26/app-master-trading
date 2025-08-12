import aiohttp
from fastapi import FastAPI
app = FastAPI()
from pydantic import BaseModel
class LongShortRatioRequest(BaseModel):
    exchange: str
    timeframe: str
    symbol: str

@app.post("/long-short-ratio")
async def get_long_short_ratio(req: LongShortRatioRequest):
    base_urls = {
        "binance": "https://fapi.binance.com/futures/data",
        "mexc": "https://contract.mexc.com/api/v1",
        "bybit": "https://api-testnet.bybit.com/v5/market"
    }

    if req.exchange.lower() not in base_urls:
        return {"error": "Unsupported exchange. Supported exchanges: binance, mexc, bybit."}

    base_url = base_urls[req.exchange.lower()]
    endpoints = {
        "binance": f"{base_url}/globalLongShortAccountRatio",
        "mexc": f"{base_url}/longShortRatio",
        "bybit": f"{base_url}/account-ratio",
        "binance_toptrader": f"{base_url}/topLongShortAccountRatio"
    }

    url = endpoints[req.exchange.lower()]
    toptrader_url = endpoints.get("binance_toptrader") if req.exchange.lower() == "binance" else None

    params = {
        "symbol": req.symbol,
        "period": req.timeframe,
        "limit": 1
    }

    if req.exchange.lower() == "mexc":
        params["symbol"] = req.symbol.replace("_", "")  # Adjust symbol format for MEXC

    if req.exchange.lower() == "bybit":
        params["category"] = "linear"  # Add category for Bybit
        # Map timeframe to Bybit's period format
        timeframe_map = {
            "5m": "5min",
            "15m": "15min",
            "1h": "1h",
            "4h": "4h",
            "1d": "1d"
        }
        params["period"] = timeframe_map.get(req.timeframe, req.timeframe)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    toptrader_data = None

                    if toptrader_url:
                        async with session.get(toptrader_url, params=params) as toptrader_resp:
                            if toptrader_resp.status == 200:
                                toptrader_data = await toptrader_resp.json()

                    if req.exchange.lower() == "binance":
                        if isinstance(data, list) and len(data) > 0:
                            latest = data[0]
                            toptrader_latest = toptrader_data[0] if toptrader_data and isinstance(toptrader_data, list) and len(toptrader_data) > 0 else {}

                            return {
                                "symbol": req.symbol,
                                "exchange": req.exchange,
                                "timeframe": req.timeframe,
                                "long_ratio": float(latest.get("longAccount", 0)) * 100,
                                "short_ratio": float(latest.get("shortAccount", 0)) * 100,
                                "toptrader_long_ratio": float(toptrader_latest.get("longAccount", 0)) * 100 if toptrader_latest else None,
                                "toptrader_short_ratio": float(toptrader_latest.get("shortAccount", 0)) * 100 if toptrader_latest else None
                            }
                    elif req.exchange.lower() == "bybit":
                        if isinstance(data, dict) and "result" in data and "list" in data["result"] and len(data["result"]["list"]) > 0:
                            latest = data["result"]["list"][0]
                            return {
                                "symbol": req.symbol,
                                "exchange": req.exchange,
                                "timeframe": req.timeframe,
                                "long_ratio": float(latest.get("buyRatio", 0)) * 100,
                                "short_ratio": float(latest.get("sellRatio", 0)) * 100
                            }
                    else:
                        return {"error": "No data available for the given parameters."}
                else:
                    return {"error": f"Failed to fetch data: HTTP {resp.status}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
