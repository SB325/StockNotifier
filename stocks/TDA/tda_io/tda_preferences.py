import time
from pprint import pprint
from datetime import datetime

class tda_preferences():
    def __init__(self, auth_in): 
        self.resource_url = 'https://api.tdameritrade.com/v1'
        self.userid = ''
        self.token = ''
        self.account = ''
        self.company = ''
        self.segment = ''
        self.version = '1.0'
        self.cddomain = ''
        self.usergroup = ''
        self.accesslevel = ''
        self.authorized = ''
        self.acl = ''
        self.timestamp = ''
        self.appid = ''
        self.streamersocket = ''
        self.streamer_subscr_key = ''
        self.auth = auth_in 
        self.auth.log('tda_preferences: Initiated tda_preferences class.')
    
    def get_principals(self):
        data = self.auth.get_req(url=self.resource_url + '/userprincipals', \
            params={'fields':['streamerSubscriptionKeys','streamerConnectionInfo', \
            'preferences','surrogateIds']})
        pprint(data)
        self.userid = data.accounts[0].accountId
        self.token = data.streamerInfo.token
        self.account = data.primaryAccountId
        self.company = data.accounts[0].company
        self.segment = data.accounts[0].segment
        self.cddomain = data.accounts[0].accountCdDomainId
        self.usergroup = data.streamerInfo.userGroup
        self.accesslevel = data.streamerInfo.accessLevel
        self.authorized = 'Y'
        self.acl = data.streamerInfo.acl
        timestamp = data.streamerInfo.tokenTimestamp
        
        #convert UTC date string to posixtime (ms)
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
        timestamp.timezone(time.tzname('UTC'))
        
        self.timestamp = timestamp.timestamp*1000
        self.appid = data.streamerInfo.appId
        self.streamersocket = 'wss://' + data.streamerInfo.streamerSocketUrl + '/ws'
        self.streamer_subscr_key = data.streamerSubscriptionKeys.keys.key
        self.auth.log('tda_preferences: Downloaded user principals data.')
        
        # There is an API to update preferences as well
        # https://developer.tdameritrade.com/user-principal/apis

