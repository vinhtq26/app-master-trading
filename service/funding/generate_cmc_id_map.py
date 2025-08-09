import requests
import json

LIMIT = 1000
OUTPUT_FILE = 'coin_cmc_id_map.py'

def fetch_top_coins(limit=1000):
    # Sử dụng endpoint public của CoinMarketCap (không cần API key)
    mapping = {}
    start = 1
    batch = 100  # API này chỉ cho tối đa 100/lần
    while len(mapping) < limit:
        url = f'https://api.coinmarketcap.com/data-api/v3/cryptocurrency/listing?start={start}&limit={batch}&sortBy=rank&sortType=desc&convert=USD%2CBTC%2CETH&cryptoType=all&tagType=all&audited=false&aux=ath%2Catl%2Chigh24h%2Clow24h%2Cnum_market_pairs%2Ccmc_rank%2Cdate_added%2Cmax_supply%2Ccirculating_supply%2Ctotal_supply%2Cvolume_7d%2Cvolume_30d%2Cself_reported_circulating_supply%2Cself_reported_market_cap'
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0',
            'platform': 'web',
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        coins = data['data']['cryptoCurrencyList']
        for coin in coins:
            symbol = coin['symbol']
            cmc_id = coin['id']
            mapping[symbol] = cmc_id
        if len(coins) < batch:
            break  # Không còn coin nào nữa
        start += batch
    return mapping

def write_map_to_file(mapping, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('# Auto-generated mapping from symbol to CoinMarketCap ID\n')
        f.write('SYMBOL_TO_CMC_ID = ')
        json.dump(mapping, f, indent=4, ensure_ascii=False)
        f.write('\n')

def main():
    mapping = fetch_top_coins(LIMIT)
    write_map_to_file(mapping, OUTPUT_FILE)
    print(f'Mapping for top {LIMIT} coins written to {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
