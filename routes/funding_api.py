from fastapi import APIRouter
import aiohttp
from service.funding import fundingInfo
from cache.CacheWithTTL import cache
import logging
router = APIRouter()

@router.get("/funding")
async def get_funding():
    logging.info("Fetching funding rates")
    funding_rate = await fundingInfo.fundingRate()
    all_funding = funding_rate.get("binance", []) + funding_rate.get("mexc", []) + funding_rate.get("bybit", [])

    logging.info("Fetching price map from cache")
    cache_key = "binance_futures_ticker_price"
    price_map = cache.get(cache_key)

    if not price_map:
        logging.info("Price map not found in cache, fetching from Binance API")
        # Fetch prices from Binance Futures API using aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://fapi.binance.com/fapi/v1/ticker/price") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        price_map = {item['symbol']: float(item['price']) for item in data}
                        logging.info("Price map fetched successfully, caching for 5 minutes")
                        # Cache the result for 5 minutes (300 seconds)
                        cache.set(cache_key, price_map, 300)
        except Exception as e:
            logging.error(f"Error fetching prices: {e}")
            price_map = {}

    filtered = []
    logging.info("Filtering funding rates with criteria")
    for item in all_funding:
        if float(item["fundingRatePercent"]) <= -0.2:
            # Normalize symbol to fetch price
            symbol_norm = item["symbol"].replace('_', '').replace('-', '')
            price = price_map.get(symbol_norm)
            filtered.append({
                "symbol": symbol_norm,
                "fundingRatePercent": item["fundingRatePercent"],
                "exchange": item.get("exchange", "unknown"),
                "image_url": item.get("image_url") or item.get("url"),
                "price": price
            })
    logging.info(f"Filtered funding rates: {filtered}")
    return filtered