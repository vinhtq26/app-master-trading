from binance.client import Client

# Binance API Configuration
BINANCE_API_KEY = "ASdfASakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27Ajasd245FAHJ"
BINANCE_API_SECRET = "JAdsfgakKdajNsjdf82JCL8IocUd9hdmmfnSJHAN89dHfnasNN27elAjda221ASA"

# Global Binance Client
binance_client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

# Binance Configuration
BASE_URL = "https://fapi.binance.com/futures/data"
ENDPOINTS = {
    "global_long_short": f"{BASE_URL}/globalLongShortAccountRatio",
    "top_trader": f"{BASE_URL}/topLongShortAccountRatio"
}
