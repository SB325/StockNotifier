from tqdm import tqdm
import time
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\test_files')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
from get_ticker_list import get_ticker_list
#from pair_ticker_with_headline import pair_ticker_with_headline
from postgres_io import postgres_io
from pprint import pprint
import pandas as pd
from spicy import spicy
from spicy_test import spicy_test
from similarity import similarity
import numpy as np
import math
import json
from tda_auth import tda_auth
from tda_order_io import tda_order_io
from order_ticket import order_ticket
from tda_account import tda_account
from tda_market_data import tda_market_data
from datetime import datetime
from wait_start import wait_start
from posix_now import posix_now
from importlib import reload

auth = tda_auth()
md = tda_market_data(auth)
ot = order_ticket(auth)
acct = tda_account(auth)
order = tda_order_io(auth, acct)

resume=True
order_execution = False
allow_selling = True
debug = False
max_lookback_days = 3
# Only buy headlines that have arrived at the top of and half
# past any given hour
hour_half_time_block = False

def get_askprice(askprice: float, ticker: str):
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
            sms=auth.send_sms(f"Buying {ticker} at askprice " + 
            f"of {askprice} is too expensive. Buying at {1.1*low}")
            return (1.1*low)
        else:
            return askprice

table_name = 'real_time_news_data'
pgio = postgres_io()
column_names = ['time', 'headline', 'ticker']

# Remove repeated rows
pgio.remove_repeated_rows(table_name)

# Load "spicy" words to search headlines for
# spicy is a dictionary where terms and weights are key value pairs
# Each headline will recieve weights for each spicy word and the 
#   cumulative product weight for each headline will be calculated
#   to determine which headline is spicy enough to buy stock
spicy = spicy()
pprint(spicy)

# Start at desired time
#start_time = '08:00'
#wait_start(start_time)
old_ticks=[]
fst = True
lookback = 3600*24*3
if debug:
    lookback = 3600*24*max_lookback_days
sms=auth.send_sms('Ticker_Picker app has begun.')
loopcnt=0
try:
    while resume:
        if loopcnt>30:
            import spicy
            reload(spicy)
            from spicy  import spicy
            spicy = spicy()
            loopcnt=0
        loopcnt+=1
        earliest = math.floor(time.time()) - lookback  # one week ago 
        datasql = pgio.custom_query(table_name,'time, headline, ticker', \
        ['where','time','>',str(earliest)])
        datasql = [[n[0],n[1].strip(),n[2].strip()] for n in datasql]
        
        if not len(datasql):
            print(f"no headlines have arrived in past {lookback/(24*3600)} days.")
            time.sleep(5)
            continue

        if fst:
            fst = False
            data = [{'Time':n[0], 'Headline':n[1], 'Ticker':n[2], \
                'Delay_min':86400} for n in datasql]
        
        # Append new headlines to 'data' if it doesn't already exist in the list
        data_headlines = [m['Headline'] for m in data]
        datasql_headlines = [n[1] for n in datasql]
        
        newheadline=[]
        for cnt,q in enumerate(datasql_headlines):
            if data_headlines.count(q)==0:
                newheadline.append(datasql[cnt][1])
                data.append({'Time':datasql[cnt][0],'Headline':datasql[cnt][1], \
                    'Ticker':datasql[cnt][2], 'Delay_min':(math.floor(time.time()) \
                    - datasql[cnt][0])/60})

        df = pd.DataFrame(data=data)
        #pd.set_option('display.max_columns', None)
        #pd.set_option('display.max_rows', None)
        #pd.options.display.width = 0
        times = df['Time'].values.tolist()
        #print(type(times))
        dt = [datetime.fromtimestamp(n) for n in times]

        dat = pd.DatetimeIndex(dt,tz='US/Eastern')
        df.insert(3,"Date",dat,True)
        df = df[['Ticker','Headline','Date','Time','Delay_min']]
        # Cluster headlines, keeping oldest one in cluster
        df=df.loc[df['Time']<=math.floor(time.time())]
        
        df.sort_values('Time',inplace=True)
        #print(df.tail(10).to_string())
        unique_tick = df['Ticker'].unique()
        thresh=0.3
        df_sub2 = pd.DataFrame({'Ticker':'', 'Headline':'', 'Date':'', 'Time':[], \
            'Delay_min':[]})
        for n in unique_tick:
            cos=[True]
            df_sub = df[df['Ticker']==n]
            if len(df_sub.index)>1:
                # omit similar headlines
                for i in [*range(len(df_sub))][1:]:
                    sim=similarity(df_sub['Headline'].values.tolist()[i-1], \
                                     df_sub['Headline'].values.tolist()[i])
                    cos.append(sim<thresh)
                #print(f"Cos: {cos}")
                #print(f"sub:\n{df_sub.to_string()}, " + \
                #f"\nsub2:\n{df_sub.loc[cos].to_string()}")
                df_sub2 = pd.concat([df_sub2, df_sub.loc[cos]], \
                                        ignore_index=True) #unique headlines
            else:
                # This is the only headline of ticker n in list, unique by default
                df_sub2 = pd.concat([df_sub2, df_sub.loc[cos]], \
                                        ignore_index=True) #unique headlines
        print('---------------------------------')
        # Remove headlines with missing tickers
        not_empty_bool = [('{}' not in n) for n in \
            df_sub2['Ticker'].values.tolist()] 
        df_sub3 = df_sub2.loc[not_empty_bool].reset_index()
        #print(df_sub3.to_string())
        quotevals = ['askPrice','askSize','assetType', \
            'bidPrice','bidSize','closePrice', \
            'highPrice','netPercentChangeInDouble', \
            'realimeEntitled','totalVolume',
            'tradeTimeInLong']

        now = math.floor(time.time())
        latency_sec = 60
        if debug:
            latency_sec = 3600*24*max_lookback_days*2*60
        spicy_score_thresh = 7
        df_now = df_sub3
        latencies = now - np.array(df_sub3['Time'].values.tolist())
        latencies[latencies<0] = 1000000
        #print(f"latency thresh: {latency_sec}")
        #print(f"latencies: {latencies}")
        #print(f"now-lat_thresh: {np.array(latencies)<(latency_sec)}")
        df_now = df_sub3[np.array(latencies)<(latency_sec)].reset_index()
        df_old = df_sub3[np.array(latencies)>(latency_sec)].reset_index()
        df_old = df_old[df_old['Headline'].isin(newheadline)]

        if (not df_now.empty) or (not df_old.empty):
            print(f"A new news headline has arrived!")
            # append df_now and df_old
            if df_now.empty:
                # late headline has appeared and no new headline has. pass df_old
                # to df_now
                df_now = df_old
            elif (not df_now.empty) and (not df_old.empty):
                # There is both a new headline and a late arrival, pass both to
                # df_now
                df_now.append(df_old)
            found=[]
            # see if headline passes word screen (does headline look spicy?)
            print('Recent Headlines')
            print(df_now.to_string())
            print('Dated Headlines')
            print(df_old.to_string())
            scores = []
            print(f"Type of df_now: {type(df_now)}")
            print(f"df_now iteritems: {df_now.iteritems()}")
            [scores.append(spicy_test(row['Headline'],spicy,False)['score']) \
                for indd,row in df_now.iterrows()]
            print(scores)
            #print(f"Max Spicy Headline: {scores.index(max(scores))}")
            #print(f"{df_now.loc[scores.index(max(scores))]}")
            #print(f"{df_now['Ticker'].loc[scores.index(max(scores))]}")
            passthresh = np.array(scores)>=spicy_score_thresh
            if not any(passthresh):
               print(f"The headline(s) aren't good enough. Skipping")
               df_now = pd.DataFrame({'Ticker':'', 'Headline':'', 'Date':'', 'Time':[], \
                'Delay_min':[]})
            else:
                df_now=df_now.loc[passthresh]
                print(df_now.to_string())
            
            for cnt,n in enumerate(df_now['Headline']):
                print(f"A spicy headline has been found!")
                found.append(cnt)
                tik = df_now['Ticker'].iloc[cnt]
                if old_ticks.count(tik)>0:
                    print('Ticker already used. Continuing.')
                    continue
                if 'None' in tik:
                    print('Ticker symbol undefined.')
                    continue
                data_ = md.get_quote(tik)
                datajson = json.loads(data_.text)
                #print(tik)
                quote=datajson[tik]
                quote_downselect= {k: v for k, v in quote.items() if k in quotevals}
               
                askprice = quote_downselect['askPrice'] 
                # If the ask price is SIGNIFICANTLY higher than that of the
                # last time tick, could be a delta spike. Limit askprice to no
                # more than 10% higher than the last time tick.
                askprice = get_askprice(askprice, tik)
                nshares = acct.calc_nshares(askprice, 0, 10000)
                
                if df_now['Delay_min'].iloc[cnt]>(latency_sec/60):
                    # Headline is seen for the first time, but not without
                    # significant delay since timestamp. 
                    # Send text and continue rather than create an order.
                    sms=auth.send_sms('Received Late notice of \'' + tik + '\': ' + \
                        spicy_test(df_now['Headline'].iloc[cnt], \
                        spicy,False)['modified_headline'] + 'delay: ' + \
                        str(latency_sec/60) + 'minutes')
                    old_ticks.append(tik)
                    print(f"Delayed timestamp ({df_now['Delay_min'].iloc[cnt]})")
                    continue

                print(f"iteritems: {int(df_now['Time'].iloc[cnt])}")
                # Only buy headlines that have arrived at the top of and half
                # past any given hour
                
                if hour_half_time_block:
                    print('Time check!')
                    post_semi_hr_window = 1 # minutes beyond each hour/30 minute 
                    mins=datetime.fromtimestamp(int(df_now['Time'].iloc[cnt])).minute
                    print(f"MINS= {mins}")
                    if (mins % 30 ) > post_semi_hr_window:
                        txt='Received Headline during off-time. Skipping'
                        #sms=auth.send_sms(txt)
                        print(txt)
                        continue

                if nshares>0:
                    sms=auth.send_sms('Buying \'' + tik + '\': ' + \
                        spicy_test(df_now['Headline'].iloc[cnt],spicy,False)['modified_headline']
                        + '. Delay=' + str(df_now['Delay_min'].iloc[cnt]) + ' minutes')
                    if ot.set_default_buy_ticket(nshares, askprice, tik, 5):
                        print(f"Getting ready to buy {nshares} shares of {tik}")
                        a=datetime.now()
                        if (a.hour <9) or (a.hour==9 and a.minute<30):
                            ot.set_session('SEAMLESS')
                        elif a.hour > 15:
                            ot.set_session('SEAMLESS')
                        order_tick = ot.single_buy_order()
                        pprint(order_tick) 
                        
                        # Place BUY order
                        if order_execution:
                            response = order.place_order(order_tick)
                        
                            if allow_selling:
                                if response.ok:
                                    # pre-emptively set LIMIT sell order
                                    time.sleep(2)
                                    nsharesdict = acct.get_quantity_held()
                                    if tik not in nsharesdict.keys():
                                        msg = 'Buy order probably did not go though.' + \
                                        'ticker not found in list of positions'
                                        print(msg)
                                        sms=auth.send_sms(msg)
                                        continue
                                    nshares=nsharesdict[tik]
                                    if nshares>0:
                                        a=datetime.now()
                                        ot.set_quantity(nshares)
                                        ot.set_price(askprice*1.5)
                                        if (a.hour <9) or \
                                        (a.hour==9 and a.minute<30):
                                            ot.set_session('SEAMLESS')
                                        elif a.hour > 15:
                                            ot.set_session('SEAMLESS')
                                            # If news came after hours, consider holding
                                            # overnight, if not sell manually.
                                            continue
                                        else:
                                            ot.set_session('SEAMLESS')
                                        order_tick = ot.single_sell_order()
                                        print(f"Getting ready to sell {nshares} shares of {tik}")
                                        pprint(order_tick) 
                                        
                                        # Place SELL order
                                        response = order.place_order(order_tick)
                        else:
                            # send text message containing ticker, headline, price and
                            # number of shares to purchase
                            hl = spicy_test(df_now['Headline'].iloc[cnt],spicy,False)['headline']
                            sms=auth.send_sms('\'' + tik + '\': ' + hl + \
                            'ASK: $' + askprice + ', NShares: ' + nshares)

                    old_ticks.append(tik)    
                else:
                    sms=auth.send_sms('Spicy ticker (non-buy) \'' + tik + '\': ' + \
                        spicy_test(df_now['Headline'].iloc[cnt],spicy,False)['modified_headline'])

                # exit after first iteration
                #resume=False
                #break 

        time.sleep(2)
except BaseException as err:
    print(f"Unexpected {err=}, {type(err)=}")
    sms=auth.send_sms('Ticker_Picker app has stopped.')
    
