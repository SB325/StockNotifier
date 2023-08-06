import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\screen_parser')
sys.path.append(r'C:\Users\sfb_s\src\genutils')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
from tda_auth import tda_auth
from tda_order_io import tda_order_io
from order_ticket import order_ticket
from tda_account import tda_account
from pprint import pprint
from tda_market_data import tda_market_data
import json
import time
import requests
from pprint import pprint
from get_askprice import get_askprice


auth = tda_auth()
#md = tda_market_data(auth)
ot = order_ticket(auth)
acct = tda_account(auth)
#acct.get_positions(True)

# Open long position (test)
order = tda_order_io(auth, acct)
tik='FNGR'
if ot.set_default_buy_ticket(80,1.80, tik):
    ot.set_session('NORMAL')
    ot.set_duration('DAY')
    ot.set_orderType('TRAILING_STOP')
    ot.set_orderStrategyType('SINGLE')
    ot.set_stopPriceLinkType('PERCENT')
    ot.set_stopPriceOffset(5)
    order_tick = ot.single_sell_order()
    pprint(order_tick) 
    order.place_order(order_tick)

'''    time.sleep(2)
    nshares = 1
    ot.set_quantity(nshares)
    ot.set_price(0.29*1.1)
    ot.set_session('NORMAL')
    ot.set_duration('DAY')
    order_tick = ot.single_sell_order()
    print(f"Getting ready to sell {nshares} shares of {tik}")
    pprint(order_tick)
    response = order.place_order(order_tick)
'''
#order.cancel_all_orders()

