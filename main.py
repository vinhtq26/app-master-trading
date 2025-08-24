import json
import logging
import threading
import time

import schedule
from binance import Client
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv
from pydantic import BaseModel

import uvicorn
from routes.funding_api import router as funding_router
from routes.binance_long_short_api import router as binance_long_short_router
from routes.long_short_ratio_api import router as long_short_ratio_router
from routes.signal_api import router as signal_router
from routes.long_short_detail import router as long_short_detail_router
from routes.long_short_detail_llm import router as long_short_detail_llm_router

API_LIMIT_PER_SECOND = 40   # Binance Futures limit: ~1200 requests/min
REQUESTS_PER_SYMBOL = 2     # global + toptrader
MAX_RETRIES = 3
RETRY_DELAY = 3

semaphore = None
load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đảm bảo các router được đăng ký chính xác
app.include_router(funding_router) # đã test
app.include_router(long_short_ratio_router) # đã test chi tiết long short một coin
app.include_router(binance_long_short_router)  # đã test danh sách tỉ lệ long short cao
app.include_router(signal_router)
app.include_router(long_short_detail_router)
app.include_router(long_short_detail_llm_router)

@app.get("/")  # Thêm endpoint GET mặc định để test
async def root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080)