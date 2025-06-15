import requests

DISCORD_WEBHOOK_URL_Long_5m = "https://discord.com/api/webhooks/1377249390544031825/3yvx-jVhYlCFqC17V0GS17b8UX11SwsYbxDtLVddgA5JfEBHvi_jXt80tKgIZrrnNRp4"
DISCORD_WEBHOOK_URL_Long_15m = "https://discord.com/api/webhooks/1377526587104428122/Rgwrg4DOdZjbilY8BBHSV9vayCIBbRKYU5TNJYx7pooKAJsVwowTYtw02UKUKbE_StgV"
DISCORD_WEBHOOK_URL_Long_4h = "https://discord.com/api/webhooks/1377527112109391962/MxYdtbMAWtiZrmn3QEhRlJGyedlk-eJYSWUrLI2crqvfIA4k8n2GrDs9cUPARrkf8A5p"

DISCORD_WEBHOOK_URL_Short_5m = "https://discord.com/api/webhooks/1377606959200604261/V15u-ZpQCK0RL_Ez3snmCSP9Iki4BV6LKT9o1uF_Iq_JUOj4BnAwqXbax-l7_YF6I07H"
DISCORD_WEBHOOK_URL_Short_15m = "https://discord.com/api/webhooks/1377607060648231032/bG8OhYkn__zvqbgoPBgZLtkRkHQYKPSBApARFWr6Cbv-slpLtHmmC3pfT-DSKoUwoPxi"
DISCORD_WEBHOOK_URL_Short_4h = "https://discord.com/api/webhooks/1377607141451497536/vklYpIoNAzHzuxp6ijnw82XEElztyCQYfvhZNa6lKbOJ1vzZHiMbCvMUGp5Zgtqnq2PD"
DISCORD_WEBHOOK_URL_Short_1d = "https://discord.com/api/webhooks/1379233846087651449/gMuR1AQrLLDgfU6dbqX5LCNeGoNvlLPUEc55wv8bsbgvsLYkJxVxdF9vwl4JJ1Y5gb9A"

DISCORD_WEBHOOK_URL_Funding = "https://discord.com/api/webhooks/1380815243067920474/pK2AZzTsRFd3TnSrXyTS2VZIqejyWyuKRKWa47TcLEKcH5NzKklcKm6zv0hGJB8crHv-"
def send_discord_notification(message, webhook_url):
    data = {"content": message}
    requests.post(webhook_url, json=data)