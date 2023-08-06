import requests
import numpy as np

def get_ticker_list():
    
    nysetickers, moddate0, ncname = get_tickerdata('http://ftp.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt');
    nasdaqtickers, moddate1, qcname = get_tickerdata('http://ftp.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt')

    tickers = []; cname=[]
    tickers.extend(nasdaqtickers)
    tickers.extend(nysetickers)
    cname.extend(qcname)
    cname.extend(ncname)
    # Sort by symbol
    idx = np.argsort(np.array(tickers))
    tickers = [tickers[x] for x in idx]
    cname = [cname[x] for x in idx]
    # use first word in company name to represent it
    cname = [' '.join(x.split(' ')[0:2]) for x in cname]
    #[print(f"{t} | {cname[cnt]}") for cnt,t in enumerate(tickers)]       
    
    return tickers, cname

def get_tickerdata(url_string):
    data = requests.get(url = url_string)
    #modified_date format: 'Sat, 08 May 2021 01:30:53 GMT'
    modified_date = data.headers.get('Last-Modified') 
    datalist = data.text.splitlines()
    tickers = list()
    cname = list()
    for n in datalist[2:]:
        t = n.split('|')[0]
        c = n.split('|')[1]
        if (not (t.isalpha())): # | (not(c.isalpha())):
            continue
        tickers.append(t)
        c = clean_names(c)
        cname.append(c)

    return tickers, modified_date, cname

def clean_names(name : str) -> str:
    name = ''.join(name.split(' - ')[0])
    name = ''.join(name.split(' Corp')[0])
    name = ''.join(name.split(',')[0])
    name = ''.join(name.split(' Inc')[0])
    name = ''.join(name.split(' N.A.')[0])
    return name

