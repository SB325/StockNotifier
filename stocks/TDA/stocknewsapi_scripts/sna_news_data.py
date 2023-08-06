import json
#from pprint import pprint

class sna_news_data:
    def __init__(self,sna_auth): 
        self.resource_url = 'https://stocknewsapi.com/api/v1'
        self.sna_auth = sna_auth
        self.sna_auth.log('sna_news_response: Initiated sna_news_response class.')
    
    def single_ticker_news(self, ticker):
        # specify ticker as a list of ticker symbols if needed.
        if isinstance(ticker,list):
            tick = ",".join(ticker)
        else:
            tick = ticker
            
        try:
            response = self.sna_auth.get_req( \
                        url = self.resource_url + '?tickers=' + tick + '&items=10&token=')
        except:
            msg = 'sna_news_data: get request parameter error'
            self.sna_auth.log(msg)
            raise Exception(msg)
        
        self.sna_auth.log('sna_news_data: Downloaded instrument response for ' + ticker + '.')
        
        if response.ok:
            responsejson = json.loads(response.text)
            #if (not valjson['candles'] or not valjson['symbol']):
            #    print('The call for price history did not yield a value.')
            #    return
        else:
            responsejson = ''
        
        return responsejson

    def all_ticker_news(self):
        # https://stocknewsapi.com/api/v1/category?section=alltickers&items=50&token=cccykwclsmbykusdqen6qymg434dvbfsbikyiwuv
            
        try:
            response = self.sna_auth.get_req( \
                        url = self.resource_url + '/category?section=alltickers&items=50&token=')
        except:
            msg = 'sna_news_data: get request parameter error'
            self.sna_auth.log(msg)
            raise Exception(msg)
        
        self.sna_auth.log('sna_news_data: Downloaded instrument response for all tickers.')
        
        if response.ok:
            responsejson = json.loads(response.text)
            #if (not valjson['candles'] or not valjson['symbol']):
            #    print('The call for price history did not yield a value.')
            #    return
        
        return responsejson