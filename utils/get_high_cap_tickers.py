import sys
sys.path.append(r'../../postgres/')
from postgres_io import postgres_io

def get_high_cap_tickers(cap: int):

    # start postgres db
    pgio = postgres_io()

    ticker='TSLA'

    # pull fundam from db where mCap>1B (data is in millions)
    table='funddata_mktd'
    querystr='where marketcap > ' + str(cap)
    tickerlist=pgio.custom_query(table,'ticker, description, marketCap', querystr.split())
    tickercaps = {n[1].strip() for n in tickerlist}
    tickercaps = {n.split(',')[0] for n in tickercaps}
    tickercaps = {n.split(' Inc')[0] for n in tickercaps}
    tickercaps = {n.split(' Corporation')[0] for n in tickercaps}
    tickercaps = {n.split('.com')[0] for n in tickercaps}
    tickercaps = {n.split(' and Company')[0] for n in tickercaps}
    tickercaps = {n.split(' & Co')[0] for n in tickercaps}
    tickercaps = {n.split(' Common Stock')[0] for n in tickercaps}
    tickercaps = {n.split(' Company')[0] for n in tickercaps}
    tickercaps = {n.split(' Group')[0] for n in tickercaps}
    tickercaps = {n.split(' AG')[0] for n in tickercaps}
    tickercaps = {n for n in tickercaps if not n.count('Manufacturing')}
    tickercaps = {n for n in tickercaps if not n.count('Depositary Shares')}
    tickercaps = {n for n in tickercaps if not len(n)<4}
    tickercaps = list(tickercaps)

    for cnt,n in enumerate(tickercaps):
        if len(n.split())>3:
            tickercaps[cnt] = n.split()[0]

    #for i in tickercaps:
    #    print(f"{i}")
    #    if i.count('Home'):
    #        break
    return tickercaps
