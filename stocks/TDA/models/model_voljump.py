#hldataframe Backtesting models
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\ticker_picker')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\screen_parser')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')

## Database import
from postgres_io import postgres_io
from tda_auth import tda_auth
from tda_market_data import tda_market_data

## Utility imports
import pdb
import time
import math
import pprint
import json
from datetime import datetime
from posix_now import posix_now
import pandas as pd
from spicy import spicy
from spicy_test import spicy_test
from os.path import exists
import pickle
from tqdm import tqdm
import numpy as np

import numpy as np
import scipy.stats

nrow_crop = []
re_run_file = False
if len(sys.argv)>1:
    if 'd' in sys.argv[1]:
        re_run_file = True
###########################################################
# accrue all technical data into a dictionary of numpy arrays according to
# ticker
###########################################################
if not exists('modeltest_voljump/full_technicals.pickle') or re_run_file:
    print(f"Collecting Model Data")
    #.......................... News
    pgio = postgres_io()
    table = 'techdata_mktd'
    startDate= int(posix_now())-(12*24*3600*1000)
    newsdata = pgio.custom_query(table,'Ticker, posixtime_ms, open,volume' + \
        ',high,close',['where','posixtime_ms','>',str(startDate)])
        #['where','Ticker','=','\'A_\''])
    
    if not len(newsdata):
        print(f"No data found for this time range.")
        exit()
    tick = [n[0].strip() for n in newsdata]
    time = [n[1] for n in newsdata]
    op = [n[2] for n in newsdata]
    vol = [n[3] for n in newsdata]
    hi = [n[4] for n in newsdata]
    cl = [n[5] for n in newsdata]
    # sort tick, time, op and vol by same indeces, by tick then by time
    sortind = np.lexsort((time,tick))
    tick = [tick[n] for n in sortind]
    time = [time[n] for n in sortind]
    op = [op[n] for n in sortind]
    hi = [hi[n] for n in sortind]
    cl = [cl[n] for n in sortind]
    vol = [vol[n] for n in sortind]
    print('First time point') 
    print(datetime.fromtimestamp(time[0]/1000).strftime('%Y-%m-%dT%H:%M:%SZ'))
    print('Last time point') 
    print(datetime.fromtimestamp(time[-1]/1000).strftime('%Y-%m-%dT%H:%M:%SZ'))
    ticker = np.array(tick)
    techdictionary = dict() #{None:{'time',None,'open':None,'volume':None}}
    first_ticker_index = np.unique(tick, return_index=True, return_inverse=True)
    for cnt,n in enumerate(tqdm(first_ticker_index[1].tolist(), desc = "Creating Tickerdictionary", \
                total=len(first_ticker_index[1]))):
        if cnt==first_ticker_index[1].size-1:
            last=-1
        else:    
            last=first_ticker_index[1].tolist()[cnt+1]-1
        techdictionary.update({ticker[n]:{'time':np.array(time[n:last]), \
            'open':np.array(op[n:last]),'high':np.array(hi[n:last]), \
            'close':np.array(cl[n:last]),'volume':np.array(vol[n:last])}})
   
    with open('modeltest_voljump/full_technicals.pickle', 'wb') as handle:
        pickle.dump({'Tech':techdictionary}, handle, protocol=pickle.HIGHEST_PROTOCOL)
    re_run_file = True   # even if model_out exists, allow it to be
                        #re-created since we have new technicals
else:
    print(f"Loading Saved Technicals Data")
    with open('modeltest_voljump/full_technicals.pickle', 'rb') as handle:
        handledict = pickle.load(handle)
    techdictionary = handledict['Tech']

###########################################################
# Apply model to technical data
###########################################################
if not exists('modeltest_voljump/model_out.pickle') or True: #re_run_file:
    # For each ticker, obtain index of volume jump corresponding to price jump
    #   Jump is defined as increase from baseline, baseline=max value in last n
    #   days
    # calculate max $ gain for next hour after said jump
    n_day_max_baseline = [90]
    volume_thresh_mult = [5]
    price_jump_thresh_pct = [5]
    starttime = []
    pricejump = []
    falsecase = []
   
    for n in tqdm(list(techdictionary.keys())[:], desc = "backtesting models",\
                total=len(techdictionary)):
        indsort = np.argsort(techdictionary[n]['time'])
        time = techdictionary[n]['time'][indsort]
        vol = techdictionary[n]['volume'][indsort]
        op = techdictionary[n]['open'][indsort]
        hi = techdictionary[n]['high'][indsort]
        cl = techdictionary[n]['close'][indsort]
        for w in n_day_max_baseline:
            if len(vol)<=(w-1):
                continue
            # discrete volume array as ratio of moving window average volume
            # (excludes first w-1 elements)
            try:
                volratio = vol/(np.convolve(vol, np.ones(w), 'same') / w)
            except:
                pdb.set_trace()
            for vtm in volume_thresh_mult:
                # ratios greater than threshold are flagged as events
                dvind = np.where(volratio >= vtm) 
                for pjt in price_jump_thresh_pct:
                    # indeces of price jumps greater than thresh
                    do = (100*(cl-op)/op)
                    doind = np.where(do > pjt)
                    if len(doind[0]):
                        # indeces of vol and price where both have jumped above respective
                        # thresholds (called an event)
                        ind = np.intersect1d(dvind[0],doind[0], assume_unique=True, return_indices=True)
                        # for each event, calculate the max price migration/denigration within
                        # an hour
                        pricejump = []
                        starttime = []
                        falsecase = []
                        if ind[0].size:
                            #print('price and volume jumps have intersected.')
                            print(f"indeces: {ind[0]}")
                            for i in ind[0]:
                                minprice = 1000
                                if i==(len(time)-1):
                                    continue
                                starttime.append(time[i+1])
                                endtime = starttime[-1]+60*60*1000 #3600*1000
                                startprice = cl[i]
                                indmask = \
                                np.where(np.logical_and(time>=starttime[-1], time<=endtime))
                                indmask = indmask[0]
                                if not len(indmask):
                                    #print(f"voljump {vtm}, pricejump {pjt}, n_day_baseline {w}")
                                    continue
                                maxprice = max(np.take(hi,indmask).tolist())
                                indmax = np.take(hi,indmask).tolist().index(maxprice)
                                if indmax:
                                    minprice = min(np.take(op,indmask).tolist()[:indmax])
                                hourjumppct = 100*(maxprice-startprice)/startprice
                                pricejump.append(hourjumppct)
                                if (startprice > minprice) and indmax:
                                    falsecase.append(False)
                                else: 
                                    falsecase.append(True)
                            if pricejump:
                                techdictionary[n].update({'baseline_win':w,'pricejumpthreshpct':pjt, \
                                    'volthreshmult':vtm,'timearray': \
                                    [datetime.fromtimestamp(b/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
                                    \
                                    for b in starttime], 'pricejumparray':pricejump, \
                                    'falsecase':falsecase})

    with open('modeltest_voljump/model_out.pickle', 'wb') as handle:
        pickle.dump(techdictionary, handle, protocol=pickle.HIGHEST_PROTOCOL)

else:
    print(f"Loading Saved Gains Data")
    with open('modeltest_voljump/model_out.pickle', 'rb') as handle:
        techdictionary = pickle.load(handle)

    
print(f"Results:")
jumps = [n[1]['pricejumparray'][:][0] for n in techdictionary.items() if 'pricejumparray' \
    in n[1].keys()]
orders_unfulfilled = [n[1]['falsecase'][:][0] for n in techdictionary.items() \
    if 'falsecase' in n[1].keys()]

hist = np.histogram(jumps,bins=20)
histpct = hist[0]/sum(hist[0])
#print(hist[1])
cumsum = np.cumsum(histpct[::-1])*100
#print(f"cumsum: {cumsum[::-1]}")
#print(f"len jumps: {len(jumps)}")
data = {'maxjumps':hist[1][1:],'histpct':histpct, 'cumsum':cumsum[::-1]} #,'falsecase':orders_unfulfilled}
print(orders_unfulfilled)
print(f"NFalse executions: {sum(orders_unfulfilled)}")
print(f"% false executions: {100*sum(orders_unfulfilled)/len(jumps)}")
df=pd.DataFrame(data=data)
print(df)

'''
for tik in techdictionary.keys():
    tech = techdictionary[tik]
    if 'baseline_win' in tech.keys():
        print(f"{tik}: " + \
        f"win-{techdictionary[tik]['baseline_win']} " + \
        f"$jumpthresh-{techdictionary[tik]['pricejumpthreshpct']} " + \
        f"volthreshmult-{techdictionary[tik]['volthreshmult']}\n" + \
        f"time-{techdictionary[tik]['timearray']}\n" + \
        f"$jump-{techdictionary[tik]['pricejumparray']}\n")
'''
