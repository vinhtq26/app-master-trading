from fastapi import APIRouter
import logging

from fastapi import APIRouter
from pydantic import BaseModel

from service.long_short_ratio_service import fetch_long_short_ratio

router = APIRouter()

class LongShortRatioRequest(BaseModel):
    exchange: str
    timeframe: str
    symbol: str
    category: str

@router.post("/long-short-ratio")
async def get_long_short_ratio(req: LongShortRatioRequest):
    logging.info(json.dumps({"action": "Received request", "data": req.model_dump()}))

    result = await fetch_long_short_ratio(req.exchange, req.timeframe, req.symbol, req.category)

    if "error" in result:
        logging.error(json.dumps({"action": "Error fetching data", "error": result['error']}))
    else:
        logging.info(json.dumps({"action": "Fetched data", "exchange": req.exchange, "symbol": req.symbol, "result": result}))
    return result
