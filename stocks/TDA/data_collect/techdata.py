import json
import pprint
from pprint import pprint

class techdata:
    '''capture technical (ohlcvt), data at various frequencies and save to disk.
    TYPE: array of struct. Each element is struct containing ticker and ohlcvt elements
    ohlcvt element is nx1 array of cells where each cell is ohlcv data at n
    timepoints.'''
    def __init__(self,md,pgio):
        self.md = md
        self.pgio = pgio
        # check if table techdata_mktd exists, if not, create table
        tnames = self.pgio.view_table_names(self.table_name())
        if not tnames:
            types = ['A',2**31+1,5.5,5.5,5.5,5.5,100]
            nullflags = [True,True,True,True,True,True,True]
            self.pgio.create_table(self.table_name(), self.column_names(), types, nullflags)
        self.md.auth.log('techdata: Initialized techdata class')            

    def table_name(self, suffix='mktd'):
        self.tablename = 'techdata_' + suffix
        return self.tablename
    
    def column_names(self):
        self.columnnames = ['Ticker','posixtime_ms','open','high','low','close','volume']
        return self.columnnames
    
    def get_technicals(self,ticker,short_term,varargin):
        assert (len(varargin)+1)%2, 'Must have an even number of arguments'
        dateset = False
        period_type = 'year'
        period = 1
        frequencyType = 'daily'
        frequency = '1'
        if len(varargin) >3:
            assert len(varargin)==7, 'If stating start and end dates, both must be specified.'
            assert varargin[0]=='startDate', 'Third argument must be ''startDate'''
            dateset = True
            startDate = varargin[1]
            endDate = varargin[3]
        if short_term:
            period_type = 'day'
            frequencyType = 'minute'
            frequency = '1'

        # technicals can come as long term (5 year period at day
        # frequency) or short term (10 day at 1min period)
        if dateset:
            val = self.md.get_price_history((ticker,'periodType',period_type, \
                'frequencyType',frequencyType,'frequency',frequency, \
                'startDate',startDate,'endDate',endDate))
        else:
            val = self.md.get_price_history((ticker,'periodType',period_type, \
                'period',period,'frequencyType',frequencyType,'frequency',frequency))
        if val.ok:
            valjson = json.loads(val.text)
            if (not valjson['candles'] or not valjson['symbol']):
                print('The call for price history did not yield a value.')
                return
            ##
            ## This is the spot to consider placing database entry code
            ##
            #columns: ticker, open, high, low, close, volume
            candl = valjson.get('candles')
            symbol = []
            tim = []
            op = []
            hi = []
            lo = []
            cl = []
            vol = []
            for i in candl:
                tim.append(i.get('datetime'))
                symbol.append(valjson.get('symbol'))
                op.append(i.get('open'))
                hi.append(i.get('high'))
                lo.append(i.get('low'))
                cl.append(i.get('close'))
                vol.append(i.get('volume'))
            
            dat = list(list())
            for cnt,p in enumerate(symbol):
                dat.append([symbol[cnt], tim[cnt], op[cnt], hi[cnt], lo[cnt], cl[cnt], vol[cnt]])  
                
            #dat = [symbol, tim, op, hi, lo, cl, vol]         
                          
            self.pgio.enter_data_into_table(self.table_name(), self.column_names(), dat)
            #dat.ticker = val.symbol
            #dat.candles = val.candles
            #                open = [val.candles(:).open]'
            #                high = [val.candles(:).high]'
            #                low = [val.candles(:).low]'
            #                close = [val.candles(:).close]'
            #                vol = [val.candles(:).volume]'
            #                newdata = [posixtime_ms,open,high,low,close,vol] #mx1 array of
            self.md.auth.log([ 'techdata: ' + valjson['symbol'] + ' data updated.'])

    #def clear_data(self, ticker):
        # clear ticker data 
        
    #def summarize_techdata(self):
        # summarize techdata in database by printing stats to json string?
