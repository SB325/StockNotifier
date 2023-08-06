import time 
import os.path
import math
import json
from requests_util import requests_util

class sna_auth(requests_util):
    def __init__(self):
        requests_util.__init__(self)
        self.token_key = 'cccykwclsmbykusdqen6qymg434dvbfsbikyiwuv'
        # 'https://stocknewsapi.com/api/v1?tickers=FB&items=50&token=' + self.token_key

        if not os.path.exists('DATASET/LOGS/'):
            os.makedir('DATASET/LOGS/')
        self.logfile = 'DATASET/LOGS/sna_logfile_' + str(math.floor(time.time())*1000) + '.json'
        self.logfid = open(self.logfile,'w+')
        logstring = [{"header": "Initiating STOCKNEWSAPI_LOGFILE"}]
        self.logfid.write(json.dumps(logstring))
        self.logfid.flush()
        os.fsync(self.logfid.fileno())
        
    def get_req(self, url):
        # params should be empty for stocknewsapi
        params = None
        return self.get(url + self.token_key, params)
        
    def delete(self):
        self.logfid.close()
        
    def log(self, msg):
        now = math.floor(time.time())*1000
        str = [{ "{} ".format(now) : msg }]
        self.logfid.write(json.dumps(str))
        self.logfid.flush()
        os.fsync(self.logfid.fileno())


