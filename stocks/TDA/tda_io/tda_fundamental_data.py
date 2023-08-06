import json
#from pprint import pprint

class tda_fundamental_data:
    def __init__(self,auth): 
        self.resource_url = 'https://api.tdameritrade.com/v1/instruments'
        self.auth = auth
        self.auth.log('tda_fundamental_response: Initiated tda_fundamental_response class.')
    
    def get_instruments(self, ticker, varargin=None):
        try:
            response = self.auth.get_req(url = self.resource_url, \
                                    params = {'apikey': self.auth.consumer_key, \
                                        'symbol': ticker, \
                                        'projection': 'fundamental'}, \
                                        headers={'Authorization' : 'Bearer ' +
                                        self.auth.access_token })
        except:
            msg = 'tda_fundamental_data: get request parameter error'
            self.auth.log(msg)
            raise Exception(msg)
        
        self.auth.log('tda_fundamental_data: Downloaded instrument response for ' + ticker + '.')
        return response
