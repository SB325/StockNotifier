from tqdm import tqdm
import time
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\screen_parser')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA')
from get_ticker_list import get_ticker_list

from get_ticker_list import get_ticker_list
from postgres_io import postgres_io
from pprint import pprint
from tda_auth import tda_auth
from tda_market_data import tda_market_data
import json

auth = tda_auth()
md = tda_market_data(auth)

tickers, cname = get_ticker_list()
tickers = tickers[:3]
print(','.join(tickers))
print(f"tickers: {tickers}")
data = md.get_quotes(['FB'])
datajson = json.loads(data.text)
pprint(datajson)
