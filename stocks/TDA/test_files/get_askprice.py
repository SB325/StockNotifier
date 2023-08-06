import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
from tda_auth import tda_auth
from tda_market_data import tda_market_data
from posix_now import posix_now
import json

def get_askprice(askprice: float, ticker: str):
    auth = tda_auth()
    md = tda_market_data(auth)

    period_type = 'day'
    period = 1
    frequencyType = 'minute'
    frequency = '1'

    data = md.get_price_history((ticker,'periodType',period_type, \
                'frequencyType',frequencyType,'frequency',frequency, \
                'startDate',str(posix_now()-(3600*24*5))))
    if data.ok:
        candles = json.loads(data.text)
        if (not candles['candles'] or not candles['symbol']):
            print('The call for price history did not yield a value.')
            raise Exception
        # get second from last low price 
        low = candles.get('candles')[-2].get('low')
        delta = (askprice-low)/low
        if delta>0.1:
            sms=auth.send_sms(f"Buying {ticker} at askprice of {askprice} " + \
                f"is too expensive. Buying at {1.1*low}")
            return (1.1*low)
        else:
            return askprice
