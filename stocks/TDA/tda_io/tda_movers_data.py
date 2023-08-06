import requests
import time

class tda_movers_data:
    def __init__(self, auth):
        self.resource_url = 'https://api.tdameritrade.com/v1/marketdata'
        self.auth = auth
        self.auth.log('tda_movers_data: Initializing tda_movers_data class.')
    
    def get_token(self):
        aut = 'Bearer ' + self.auth.access_token
        header = {'Authorization': aut} #.replace('\n','')}
        auth = {'apikey': self.auth.consumer_key}
        return header, auth

    def get_movers(self, index: str, direction: str, change_pct: float):
        assert varargin.length()==4, 'Needs 3 arguments: MarketName, ' + \
            'direction (''''up''''/''''down'''') and change (''''percent''''/''''value'''')'
        header, auth = self.get_token()
        self.auth.refresh()

        try:
            data = self.auth.get_req(url=self.resource_url + '/' + index + '/movers', \
                params={'apikey':self.auth.consumer_key_val, \
                'direction': direction, \
                'change',change_pct}, \
                headers=header)
        except:
            self.auth.log('tda_movers_data: request for data failed')
        
        time.sleep(0.5)
        self.auth.log('tda_movers_data: Downloaded movers data for ' + index )
        return data
