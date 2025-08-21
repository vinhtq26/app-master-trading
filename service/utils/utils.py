from service.funding.coin_cmc_id_map import SYMBOL_TO_CMC_ID


def get_coin_image_url(symbol):
    # Remove _ and USDT suffix
    base = symbol.replace('_', '').replace('USDT', '').replace('USD', '')
    # Special case: if symbol starts with A_ (e.g. A_UST), remove _
    if '_' in symbol:
        base = symbol.split('_')[0]
    cmc_id = SYMBOL_TO_CMC_ID.get(base)
    if cmc_id:
        return f"https://s2.coinmarketcap.com/static/img/coins/64x64/{cmc_id}.png"
    return None