from fastapi import FastAPI, Request

from service.long_short_detail_service import get_long_short_detail

app = FastAPI()
from pydantic import BaseModel

@app.post("/long_short_detail")
async def long_short_detail(request: Request):
    body = await request.json()
    exchange = body.get("exchange")
    timeframe = body.get("timeframe")
    symbol = body.get("symbol")
    result = get_long_short_detail(exchange, timeframe, symbol)
    return result

