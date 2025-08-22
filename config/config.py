import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# API Configuration
API_LIMIT_PER_SECOND = 40  # Binance Futures limit: ~1200 requests/min
REQUESTS_PER_SYMBOL = 2    # global + toptrader
MAX_RETRIES = 3
RETRY_DELAY = 3

# API Keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

# Other configurations can be added here as needed
