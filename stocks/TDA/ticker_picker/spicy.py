import json
from pprint import pprint
from get_high_cap_tickers import get_high_cap_tickers

def spicy(verbose=False):
    f = open('ticker_picker\spicy.json')
    data = json.load(f)
    f.close()
   
    # Company names with high market caps should be spicy too
    data_high_caps = dict([(n,2) for n in get_high_cap_tickers(100000)])
    data.update(data_high_caps)

    if verbose:
        print(f"Spicy Words:")
        pprint(data)
    
    return data
