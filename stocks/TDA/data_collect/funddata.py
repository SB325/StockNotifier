#import time
import json
from pprint import pprint

class funddata:
    '''
    capture fundamental, data at daily frequency and save to disk.
    TYPE: array of struct. Each element is struct containing ticker,
    descrip and data elements
    (one element per time point)
    '''
    def __init__(self,fd,pgio):
        self.fund = fd
        self.pgio = pgio
        
        # check if table techdata_mktd exists, if not, create table
        tnames = self.pgio.view_table_names(self.table_name())
        if not tnames:
            types = ['A', '', 'A', 'A', \
                     5.5, 5.5, 5.5, 5.5, '', \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     5.5, 5.5, 5.5, 5.5, 5.5, \
                     '', 5.5, 5.5, 5.5, 5.5 ]
                
            nullflags = [True] * len(self.column_names())
            self.pgio.create_table(self.table_name(), self.column_names(), types, nullflags)
        self.fund.auth.log('techdata: Initialized techdata class')      
    
    def table_name(self, suffix='mktd'):
        self.tablename = 'funddata_' + suffix
        return self.tablename
    
    def column_names(self):
        # insert 'cusip', 'description', 'exchange', between first ('symbol') and
        # second ('high52') elements of fundamentals array
        self.columnnames = ['ticker', 'cusip', 'description', 'exchange', \
                            'high52', 'low52', 'dividendAmount', 'dividendYield', \
                            'dividendDate', 'peRatio', 'pegRatio', 'pbRatio', \
                            'prRatio', 'pcfRatio', 'grossMarginTTM', 'grossMarginMRQ', \
                            'netProfitMarginTTM', 'netProfitMarginMRQ', \
                            'operatingMarginTTM', 'operatingMarginMRQ', \
                            'returnOnEquity', 'returnOnAssets', 'returnOnInvestment', \
                            'quickRatio', 'currentRatio', 'interestCoverage', \
                            'totalDebtToCapital', 'ltDebtToEquity', 'totalDebtToEquity', \
                            'epsTTM', 'epsChangePercentTTM', 'epsChangeYear', 'epsChange', \
                            'revChangeYear', 'revChangeTTM', 'revChangeIn', \
                            'sharesOutstanding', 'marketCapFloat', 'marketCap', \
                            'bookValuePerShare', 'shortIntToFloat', 'shortIntDayToCover', \
                            'divGrowthRate3Year', 'dividendPayAmount', 'dividendPayDate', \
                            'beta', 'vol1DayAvg', 'vol10DayAvg', 'vol3MonthAvg']
        return self.columnnames
    
    def get_fundamentals(self,ticker,varargin=None):
        response = self.fund.get_instruments(ticker,varargin)
        
        if (response.ok and not response.text=='{}'):
            #dat.ticker = val.symbol
            #dat2.fundamental = val.fundamental
            #dat2.descrip = val.description
            #dat2.posixtime_ms = math.floor(time.time())*1000
            self.fund.auth.log(['funddata: Downladed fundamental data for ' + ticker ])

            valjson = json.loads(response.text)[ticker]
            #columns = self.column_names()[5:]
            
            try:
                dat = [valjson['symbol'],valjson['cusip'],valjson['description'],valjson['exchange']]            
                for n in self.column_names()[4:]:
                    dat.append(valjson['fundamental'][n])
                
                self.pgio.enter_data_into_table(self.table_name(), self.column_names(), dat)
                #dat.ticker = val.symbol
                #dat.candles = val.candles
                #                open = [val.candles(:).open]'
                #                high = [val.candles(:).high]'
                #                low = [val.candles(:).low]'
                #                close = [val.candles(:).close]'
                #                vol = [val.candles(:).volume]'
                #                newdata = [posixtime_ms,open,high,low,close,vol] #mx1 array of
                self.fund.auth.log([ 'funddata: ' + valjson['symbol'] + ' data updated.'])
            except:
                self.fund.auth.log([ 'funddata: ' + valjson['symbol'] + ' did not load.'])
                
            #pprint(json.loads(response.text))
