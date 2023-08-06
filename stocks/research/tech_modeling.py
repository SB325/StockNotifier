# TECH_MODELING.PY
# Here, a technical model is formed that seeks a correlation between volume
# 'jumps' and subsequent price peaks after the jump has been detected (beyond a
# threshold value. 
# For all N tickers, the independent variables:
#   - moving window size (volume) in minutes
#   - volume jump threshold (over baseline based on moving window)
# For all N tickers, the dependent variables:
#   - price increase from time of threshold detection to subsequent peak (by
#   end of day)
#   - time elapsed between that of threshold detection and peak.

#imports
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
from postgres_io import postgres_io

# utils
import time
from pprint import pprint
from tqdm import tqdm
from datetime import datetime
import mpld3
from os.path import exists

# math
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def set_size(w,h, ax=None):
    """ w, h: width, height in inches """
    if not ax: ax=plt.gca()
    l = ax.figure.subplotpars.left
    r = ax.figure.subplotpars.right
    t = ax.figure.subplotpars.top
    b = ax.figure.subplotpars.bottom
    figw = float(w)/(r-l)
    figh = float(h)/(t-b)
    ax.figure.set_size_inches(figw, figh)

def plotyy(tik, tim_ms, op, vol):

    fig = plt.figure()
    ax1 = fig.add_subplot(111) 
    
    ax1.set_xlabel('Timepoint', {'fontsize':24})
    ax1.set_ylabel('$', {'fontsize':24}, color='tab:blue')
    ax1.set_ylim(min(op), max(op))
    ax1.plot(range(0,len(vol)), op, 'b')
    ax1.set_title(tik)

    #ax2 = fig.add_subplot(111) 
    ax2 = ax1.twinx()
    ax2.set_ylabel('Volume', {'fontsize':24}, color='tab:red')
    ax2.plot(range(0,len(vol)), vol,'r')
    ax2.set_ylim(min(vol), max(vol))
    
    #fig.tight_layout()
    ax2.patch.set_alpha(0.0)
    
    mpld3.save_html(fig,'C:\\apache-tomcat-8.5.75\webapps\ROOT\mplot.html')
    print(f"figure Saved!")
    return fig, ax1, ax2

def ploty_annotate(tik, tm, op, vol, ind_array):
    fig, ax1, ax2 =plotyy(tik,tm,op,vol)
    ax1.plot([40, 140],[18.6, 20],'g')

def drop_index(tm, op, drop_thresh):
    np.array(tm,copy=True)
    np.array(op,copy=True)

    tmdiff=np.diff(tm, append=0)
    opdiff=np.diff(op, append=0)
    frac=opdiff/op
    minind = frac < -drop_thresh
    minind = np.where(minind)

    return minind


#start db instance
pgio = postgres_io()

tablename='techdata_mktd'

if not exists('tickerlist.txt'):
    tickers = pgio.custom_query(tablename, 'DISTINCT ticker')
    tickers = [n[0].strip() for n in tickers]
    fid=open('tickerlist.txt','w+')
    [fid.write(str(ticker) + '\n') for ticker in tickers]
else:
    tickers = []
    fid=open('tickerlist.txt','r+')
    tickers = fid.read().splitlines()
fid.close()

# for each ticker, load posixtime_ms volume and candle data (ohlc)
for ticker in tickers:
    tik = ticker
    # data is an array of tuples containing (posixtime_ms, o,h,l,c,volume)
    data = pgio.custom_query(tablename, '*', \
        'where', 'ticker', '=', '\'' + tik + '\'' )
    
    # moving window array (minutes)
    mw=[2, 4, 6, 8, 10]
    # threshold array (% increase)
    th=[10, 100, 1000, 10000]
    
    tm = [n[2] for n in data]
    op = [n[3] for n in data]
    vol = [n[7] for n in data]
    
    # find index of price timeseries corresponding to a value drop of greater
    # than drop_thresh
    drop_thresh=0.5
    ind_array = drop_index(tm, op, drop_thresh)
    #print(f"ind_array= {ind_array}")
    ploty_annotate(tik, tm, op, vol, ind_array)
    raise Exception
