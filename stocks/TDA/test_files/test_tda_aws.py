### Test TDA token validity ###
import sys
import json
sys.path.append(r'tda_io/')
sys.path.append(r'../../postgres/')
## TDAPI Authorization, Technical, Fundamentals and News
from tda_auth import tda_auth
from tda_market_data import tda_market_data
from tda_fundamental_data import tda_fundamental_data
from tda_preferences import tda_preferences
from postgres_io import postgres_io
 
print(f"imports done")
# authorize
auth = tda_auth()
print(f"init auth")

# start postgres db
pgio = postgres_io()
print(f"init postgres db")

# get account values
pref = tda_preferences(auth)
print(f"init pref")
# create market data object
md = tda_market_data(auth)
print(f"init market data")
# create fundamental data object

ticker='TSLA'
period_type = 'year'
period = 1
frequencyType = 'daily'
frequency = '1'
val = md.get_price_history((ticker,'periodType',period_type, \
                'period',period,'frequencyType',frequencyType,'frequency',frequency))
#reply = json.loads(val.text)
#print(f"{reply.keys()}")

if val.ok:
    print(f"Get Request Succeeded, Test passed.")
