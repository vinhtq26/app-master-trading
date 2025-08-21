from fastapi import APIRouter, Body
from service.binance_long_short_service import get_binance_long_short
from binance import Client
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

client = Client(
    os.getenv("BINANCE_API_KEY"),
    os.getenv("BINANCE_API_SECRET")
)

@router.post("/binance/long-short")
async def get_binance_long_short_api(req: dict = Body(...)):
    period = req.get("period", "5m")
    result = await get_binance_long_short(period, client)
    return result
