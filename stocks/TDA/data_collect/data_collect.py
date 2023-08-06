import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
sys.path.append(r'C:\Users\sfb_s\src\genutils')
## TDAPI Authorization, Technical, Fundamentals and News
from tda_auth import tda_auth
from tda_market_data import tda_market_data
from tda_fundamental_data import tda_fundamental_data
from tda_preferences import tda_preferences
from techdata import techdata
from funddata import funddata
#from benzinga_api import benzinga_api

## Trading Execution imports
#from tda_order_io import tda_order_io
#from tda_transactions import tda_transactions
#from tda_account import tda_account

## Database import
from postgres_io import postgres_io

## Utility imports
import time
import math
import pprint
from datetime import datetime
from get_ticker_list import get_ticker_list
from posix_now import posix_now
import pdb
# start db instance
pgio = postgres_io()

#get current time
tcurr = posix_now()
# while (tcurr.Hour>=6) & (tcurr.Hour<=21)  # Run data collect from 6am to 9pm

# Load ticker list and put into cell array
tickers, cname = get_ticker_list()

# authorize
auth = tda_auth()

# get account values
pref = tda_preferences(auth)
# create market data object
md = tda_market_data(auth)
# create fundamental data object
fd = tda_fundamental_data(auth)

# create technical data object
tech = techdata(md,pgio)  
tablename=tech.table_name('lowcap') #techdata_<suffix>

## get fundamental data on each ticker
fund = funddata(fd,pgio) 
fund.table_name(suffix='lowcap') #funddata_<suffix>

n_up_to_date_tickers = 0
n_updated_tickers = 0
n_new_tickers = 0
missed_tickers = 0

#bapi = benzinga_api(auth,pgio)

techtoc = []
fundtoc = []

fulltic = time.perf_counter()
indstart = 0
starttime = 0 
indstart = 0 #tickers.index('AVCT')

for ind,i in enumerate(tickers):
    ind0 = ind+indstart
    endtime = str(posix_now()) 
    timedict = {'startDate':starttime,'endDate':endtime}
    
    techtic = time.perf_counter()
        
    timedict = {'startDate':str(starttime),'endDate':endtime}
    ttic = time.perf_counter()
    tech.get_technicals(i,False,timedict)
    timm = time.perf_counter() - ttic
    print(f"Elapsed Time: {timm}")
    techtoc.append(time.perf_counter() - techtic)
    
    timedict = {'startDate':starttime,'endDate':endtime}
    fundtic = time.perf_counter()
    fund.get_fundamentals(i)
    fundtoc.append(time.perf_counter() - fundtic)
    
    if ind0<len(tickers):
        print('Loading data for ' + i + ' {} of {}... {}%'.format(ind0, len(tickers), ind0/len(tickers)*100))
print('Remove ducplicate rows')
pgio.remove_repeated_rows(tech.table_name())
pgio.remove_repeated_rows(fund.table_name())
print('Data Download Complete!')

fulltoc = time.perf_counter() - fulltic

# Timing Stats:
techtime = sum(techtoc)
fundtime = sum(fundtoc)
print('Time elapsed collecting technical data: {} hrs. \n Percent of total: {}'.format(techtime/3600, \
                    techtime/fulltoc*100))
print('Time elapsed collecting fundamental data: {} hrs \n Percent of total: {}'.format(fundtime/3000, \
                    fundtime/fulltoc*100))
othertime = (fulltoc-(techtime+fundtime))
print('Other time elapsed: {} hrs. \nPercent of total: {}'.format( othertime/3600, \
                    othertime/fulltoc*100))
