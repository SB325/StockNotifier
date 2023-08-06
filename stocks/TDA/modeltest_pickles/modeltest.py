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
import pdb
nrow_crop = []
re_run_file = False
if len(sys.argv)>1:
    if 'd' in sys.argv[1]:
        re_run_file = True

# Key constants
news_lookback_days=300
startDate= int(posix_now()/1000-(news_lookback_days*24*3600))

if not exists('modeltest_pickels/model_technicals.pickle') or re_run_file:
    print(f"Collecting Model Data")
    #.......................... News
    pgio = postgres_io()
    table = 'real_time_news_data'
    newsdata = pgio.custom_query(table,'time, headline, ticker', \
        ['where','time','>',str(startDate)])
    if not len(newsdata):
        print(f"No news found for this time range.")
        exit()
    times = [n[0] for n in newsdata]
    headlines = [n[1].strip() for n in newsdata]
    ticker = [n[2].strip() for n in newsdata]
    hldata = {'Time':times,'Headline':headlines,'Ticker':ticker}
    hldataframe=pd.DataFrame(data=hldata)
     
    # check each headline against the news model
    spicy = spicy()
    scores = [spicy_test(n,spicy,False)['score'] for n in \
        hldataframe['Headline'].values.tolist()]
    mod_headl = [spicy_test(n,spicy,False)['modified_headline'] for n in \
        hldataframe['Headline'].values.tolist()]
    hldataframe['Modified_Headline']=mod_headl
    hldataframe['Scores']=scores
   
    # remove rows with missing tickers
    hldataframe = hldataframe.iloc[[cnt for cnt,n in \
            enumerate(hldataframe['Ticker'].values.tolist()) if '{}' not in n]]

    if nrow_crop:
        hldataframe = hldataframe.iloc[0:nrow_crop]
    #.......................... Technicals
    auth = tda_auth()
    md = tda_market_data(auth)

    period_type = 'day'
    frequencyType = 'minute'
    frequency = '1'
    
    tech={}
    for tik in tqdm(hldataframe['Ticker'].values.tolist(), \
            desc ="Loading Technicals"):
        val = md.get_price_history((tik,'periodType',period_type, \
                    'frequencyType',frequencyType,'frequency',frequency, \
                    'startDate','0'))
        if val.ok:
            valjson = json.loads(val.text)
            if (not valjson['candles'] or not valjson['symbol']):
                #print('The price history call did not yield a value.')
                continue
            candl= valjson['candles']
            tech.update({tik:{'datetime':[int(n['datetime']/1000) for n in candl], \
                'volume':[n['volume'] for n in candl], \
                'open':[n['open'] for n in candl], \
                'high':[n['high'] for n in candl], \
                'low':[n['low'] for n in candl], \
                'close':[n['close'] for n in candl]}})

    with open('modeltest_pickels/model_technicals.pickle', 'wb') as handle:
        pickle.dump({'DataFrame':hldataframe,'Tech':tech}, handle, protocol=pickle.HIGHEST_PROTOCOL)
    re_run_file = True   # even if model_gains exists, allow it to be
                        #re-created since we have new technicals
else:
    print(f"Loading Saved Technicals Data")
    with open('modeltest_pickels/model_technicals.pickle', 'rb') as handle:
        handledict = pickle.load(handle)
    hldataframe = handledict['DataFrame']
    tech = handledict['Tech']

if not exists('modeltest_pickels/model_gains.pickle') or True: #re_run_file:
    # Calculate max price increase since 1 hour after headline
    volgain=[]
    gain=[]
    prenews_gain=[]
    for row in tqdm(hldataframe.iterrows(), desc = "Calculating Gains",\
            total=hldataframe.shape[0]):
        start = row[1]['Time']
        end = start+600
        tik=row[1]['Ticker']
        if tik not in tech.keys():
            #print(f"{tik} missing.")
            volgain.append(None)
            gain.append(None)
            prenews_gain.append(None)
            continue
        if tech[tik]['datetime'][-1] < end:
            #print(f"Last ticker time {tech[tik]['datetime'][-1]} " + \
            #f"is less than end of window {end}")
            volgain.append(None)
            gain.append(None)
            prenews_gain.append(None)
            continue
        ind = [cnt for cnt,n in enumerate(tech[tik]['datetime']) if \
            (n>=start and n<=end)]
        ind2 = [cnt for cnt,n in enumerate(tech[tik]['datetime']) if \
            (n>=(start-300) and n<=end)]
        if len(ind)>1:
            endvol = tech[tik]['volume'][ind[-1]]
            startvol = tech[tik]['volume'][ind[0]]
            endprice = max([nn for cnt,nn in enumerate(tech[tik]['open']) if cnt \
            in ind])
            startprice = tech[tik]['open'][ind[0]]
            oldprice = tech[tik]['open'][ind2[0]]
            volgain.append((endvol-startvol)/startvol)
            gain.append(100*(endprice-startprice)/startprice)
            prenews_gain.append(100*(startprice-oldprice)/oldprice)
        else:
            #print(f"Technicals do not contain Headline window. lenind={len(ind)}")
            volgain.append(None)
            gain.append(None)
            prenews_gain.append(None)

    hldataframe['Volgain']=volgain
    hldataframe['Gain']=gain
    hldataframe['Pre-Gain']=prenews_gain
    hldataframe = hldataframe.iloc[hldataframe['Gain'].notna().tolist()]
    hldataframe.drop_duplicates(inplace=True)
    hldataframe.reset_index(drop=True)
    print(hldataframe.sort_values(by='Gain',ascending=False).to_string())
    pdb.set_trace()
    with open('modeltest_pickels/model_gains.pickle', 'wb') as handle:
        pickle.dump(hldataframe, handle, protocol=pickle.HIGHEST_PROTOCOL)

else:
    print(f"Loading Saved Gains Data")
    with open('modeltest_pickels/model_gains.pickle', 'rb') as handle:
        hldataframe = pickle.load(handle)

hldataframe['Time'] = [datetime.fromtimestamp(n) for n in \
    hldataframe['Time'].values.tolist()]
hldataframe.reset_index(drop=True)
#............................. print dataframe
#pd.set_option('display.max_colwidth', True)

#............................. model performance
spicy_threshold=6
gain_threshold=[1,2] #percent
volgain_threshold=10 #multiples of growth
post_semi_hr_window = 2 # minutes beyond each hour/30 minute
windowtest = True
found=None
tp = []
tn = []
fp = []
fn = []
for cnt,n in enumerate(hldataframe.iterrows()):
    found=1
    if n[1]['Gain'] is None:
        continue
    dstr=str(n[1]['Time'])
    dtim = datetime.strptime(dstr,'%Y-%m-%d %H:%M:%S')
    mins=dtim.minute
    #print(f"score:{n[1]['Scores']}, gain: {n[1]['Gain']}, " + \
    #    f"datestring: {dstr}, datetime: {dtim}, minutes: {mins}")
    # true positive
    if (n[1]['Scores']>=spicy_threshold and n[1]['Gain']>gain_threshold[1]) \
        and (mins % 30 <= post_semi_hr_window and windowtest):
        tp.append(cnt)
    # true negative
    if (n[1]['Scores']<spicy_threshold and n[1]['Gain']<=gain_threshold[0]) \
        and (mins % 30 >= post_semi_hr_window and windowtest):
        tn.append(cnt)
    # false positive
    if (n[1]['Scores']>=spicy_threshold and n[1]['Gain']<=gain_threshold[0]) \
        and (mins % 30 <= post_semi_hr_window and windowtest):
        fp.append(cnt)
    # false negative
    if (n[1]['Scores']<spicy_threshold and n[1]['Gain']>gain_threshold[1]) \
        and (mins % 30 >= post_semi_hr_window and windowtest):
        fn.append(cnt)


#pd.set_option('display.max_columns', None)
#pd.set_option('display.max_rows', None)
#pd.options.display.width = 50
if found:
    truepositives = hldataframe.iloc[tp]
    truenegatives = hldataframe.iloc[tn]
    falsepositives = hldataframe.iloc[fp]
    falsenegatives = hldataframe.iloc[fn]
    print(f"TruePositives:\n{truepositives.sort_values(by='Gain',ascending=False)}")
    print(f"FalseNegatives:\n{falsenegatives.sort_values(by='Gain',ascending=False)}")
    print(f"TrueNegatives:\n{truenegatives.sort_values(by='Gain',ascending=False)}")
    print(f"FalsePositives:\n{falsepositives.sort_values(by='Gain',ascending=False)}")

    print(f"-------------------------Performance Summary----------------------------")
    print(f"Total rows: {len(hldataframe.index)}")
    print(f"TruePositives:\n{len(truepositives.index)}")
    print(f"FalseNegatives:\n{len(falsenegatives.index)}")
    print(f"TrueNegatives:\n{len(truenegatives.index)}")
    print(f"FalsePositives:\n{len(falsepositives.index)}")
else:
    print(f"Not enough information to obtain performance.")

pdb.set_trace()
