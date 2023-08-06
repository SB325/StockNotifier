from pprint import pprint
import os
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
import time 
import os.path
import math
import json
from requests_util import requests_util
import subprocess
import platform
from urllib.parse import unquote
import os.path
import requests

homepath='C:\\Users\\sfb_s\\src\\StockNotifier\\stocks\\TDA\\'

class tda_auth(requests_util):
    def __init__(self):
        requests_util.__init__(self)
        self.refresh_token = ''
        self.callback_url = 'https://173.69.166.29'
        self.consumer_key = 'RCKJNG0XLQ8TIPOUT6DIQOD4JVC7DPSR'
        self.resource_url = 'https://api.tdameritrade.com/v1/oauth2/token'
        # log all actions performed with TDAPI
        self.sms_payload = { 'phone': '8605504982', \
                    'message': 'default_message', \
                    'key':'71a0168b7c12362a405266308dc64c562104842bPVFFq7EioyXR8GxqR0M8TKpij'}
        
        self.expiration = \
            math.floor(os.path.getmtime(homepath + 'tokens\\access_token.txt'))+1740
        self.logstring = []
        
        self.on_remote = 'Linux' in platform.system()
        
        # sync TDA tokens between remote and local
        self.sync_tokens()
        
        fid_at = open(homepath + 'tokens/access_token.txt','r')
        fid_rt = open(homepath + 'tokens/refresh_token.txt','r')
        self.access_token = fid_at.read()
        self.refresh_token = fid_rt.read()
        fid_at.close()
        fid_rt.close()
        
        if 'code=' in self.refresh_token:
            self.get_refresh_token()

        if not os.path.exists('DATASET/LOGS/'):
            if self.on_remote:
                os.mkdir('DATASET/LOGS/')
            else:
                os.makedirs('DATASET/LOGS/')

        self.logfile = 'DATASET/LOGS/logfile_' + str(math.floor(time.time())) + '.json'

        self.logfid = open(self.logfile,'w+')
        logstring = [{"header": "Initiating TDA_AUTH_LOGFILE"}]
        self.logfid.write(json.dumps(logstring))
        self.logfid.flush()
        os.fsync(self.logfid.fileno())
        
    def send_sms(self,message: str):
        self.sms_payload['message'] = message
        resp = requests.post('https://textbelt.com/text', \
            self.sms_payload)
        resptext = json.loads(resp.text)
        if 'quotaRemaining' in resptext:
            print(f"{resptext['quotaRemaining']} more text messages remaining.")
        return resp

    def post_req(self, url, params, headers={}):
        self.refresh()
        if len(headers.keys())>0:
            headers['Authorization']='Bearer ' + self.access_token
        self.post(url,params,*headers)
        
    def get_req(self, url, params,headers):
        self.refresh()
        headers['Authorization']='Bearer ' + self.access_token
        response = self.get(url,params,headers)
        if not response.ok:
            raise Exception('GET Request failed.')
        return self.get(url,params,headers)
        
    def delete(self):
        self.sync_tokens()
        self.logfid.close()
    
    def sync_tokens(self):
        self.sync_tokens_with_remote()
        self.sync_tokens_with_local()

    def sync_tokens_with_remote(self):
        # Use system call to sync tokens (between host and s3 bucket)
        os.system('aws s3 sync s3://tda-log-bucket/*.txt ' + homepath + 'tokens/') 
        print('Tokens Sync\'ed with remote.')

    def sync_tokens_with_local(self):
        # Use system call to sync tokens (between host and s3 bucket)
        os.system('aws s3 sync ' + homepath + 'tokens/ s3://tda-log-bucket')
        print('Tokens Sync\'ed with local.')
    
    def log(self, msg):
        now = math.floor(time.time())
        str = [{ "{} ".format(now) : msg }]
        self.logfid.write(json.dumps(str))
        self.logfid.flush()
        os.fsync(self.logfid.fileno())

    def refresh(self):
        now = math.floor(time.time())
        if (self.expiration<(now+60)):
            self.get_access_token()
            
    def get_refresh_token(self):
        # After logging into auth.tdameritrade.com/oauth, copy the reply url
        # into tokens\refresh_token.txt before running tda_auth.py.
        # get_refresh_token() will take care of the rest.
        url = self.resource_url
        raw_code=self.refresh_token
        code = raw_code[raw_code.find('code=')+5:]
        code = unquote(code,encoding='utf-8').replace('\n','')
        # refresh token at this point is merely the auth code needed to create
        # new tokens.
        data_dict = {'grant_type' :'authorization_code', \
                    'access_type' : 'offline', \
                    'code' : code, \
                    'client_id' : self.consumer_key, \
                    'redirect_uri' : self.callback_url}
        reply = self.post(url, data_dict)
        
        if not reply.ok:
            print('Authentication Failed!')
            print(f"{reply.request} Failed with {reply.reason} code:{reply.status_code}")
            print(f"full response: \n{json.loads(reply.text)}")
            print(f"{data_dict}")
            assert False
        print('Successfully authenticated tokens!')
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])
        self.access_token = replyjson['access_token']
        self.refresh_token = replyjson['refresh_token']
        fid = open(homepath + 'tokens/access_token.txt','w')
        fid.write(self.access_token)
        fid.close()
        fid = open(homepath + 'tokens/refresh_token.txt','w')
        fid.write(self.refresh_token)
        fid.close()
        os.system('aws s3 sync ' + homepath + 'tokens/ s3://tda-log-bucket') 
        print('Refresh token updated.')
    
    def get_access_token(self):
        url = self.resource_url
        data_dict = {'grant_type' :'refresh_token', \
                    'refresh_token' : self.refresh_token, \
                    'client_id' : self.consumer_key}
        reply = self.post(url, data_dict)
        
        if not reply.ok:
            print('Authentication Failed! {} Failed with {} code {}'.format(reply.request, reply.reason, reply.status_code))
            assert False
        replyjson = json.loads(reply.text)
        # posixtime in seconds that access token will expire
        self.expiration = math.floor(time.time())+(replyjson['expires_in'])
        self.access_token = replyjson['access_token']
        fid = open(homepath + 'tokens/access_token.txt','w')
        fid.write(self.access_token)
        fid.close()
        self.sync_tokens_with_local()
        print('Access token updated.')
