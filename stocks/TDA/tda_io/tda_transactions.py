import requests

class tda_transactions:
# preference settings for the TDA Account
    def __init__(self,auth): 
        self.resource_url = \
            'https://api.tdameritrade.com/v1/accounts/866675922/transactions' 
        self.auth = auth
    
    def get_token(self):
        aut = 'Bearer ' + self.auth.access_token
        header = {'Authorization': aut} 
        auth = {'apikey': self.auth.consumer_key}
        return header, auth

    def get_transactions(self,varargin):
        #nargin must ==4. The 3 varargin elements must be 'type',
        #'startDate', 'endDate'. Dates are Valid ISO-8601 format
        # MAX DATE RANGE IS 1 YEAR. Set assert for this
        #validtypes = {'ALL','TRADE','BUY_ONLY','SELL_ONLY', \
        #    'CASH_IN_OR_CASH_OUT','CHECKING','DIVIDEND','INTEREST', \
        #    'OTHER','ADVISOR_FEES'};
        header, auth = self.get_token()
        self.auth.refresh()
        pl = {'type':varargin[0], 'startDate':varargin[1], 'endDate':varargin[2]}
        data = self.auth.get_req(url=self.resource_url , params=pl, \
           headers=header)
        return data
    
