from tqdm import tqdm
import time
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\genutils')
sys.path.append(r'C:\Users\sfb_s\src\Screen_Capture')
import numpy as np
import math
import json
import pdb
import pprint
import traceback2 as traceback

from datetime import datetime
from posix_now import posix_now
from pull_window import pull_window

from tda_auth import tda_auth
from tda_market_data import tda_market_data
from order_ticket import order_ticket
from tda_account import tda_account
from tda_order_io import tda_order_io
from quote_trend import quote_trend

if __name__ == "__main__":
    # this script will poll the call_screenshot for new tickers, then track
    # quotes on the tickers for trend in bid price. Increasing bids should
    # trigger the opening of a long position. Onward, decreasing bids should
    # trigger the closing of the long position. Exclude explored tickers from
    # consideration of new positions.
   
    auth = tda_auth()
    md = tda_market_data(auth)
    ot = order_ticket(auth)
    acct = tda_account(auth)
    order = tda_order_io(auth, acct)
    
    sms=auth.send_sms('Momentum finder app has begun.')
    # 'max_entry_sampling_age' means deadline to reach 'percent_jump_trigger'
    # before quitting
    # 'max_exit_sampling_age' means max age of ticker tracking
    # 'percent_drop_trigger' means trailing stop pct value
    config = {'max_entry_sampling_age':5, \
        'max_exit_sampling_age':30, \
        'percent_drop_trigger': 10, \
        'mandatory_hold_time_mins': 10, \
        'percent_jump_trigger': 6}
    # set reasonable limits on config
    assert config['max_exit_sampling_age'] > config['max_entry_sampling_age'], \
        f"exit sampling age must be greater than entry!!"
    verbose = False
    qt = quote_trend(md, ot, order, acct, config, verbose)
    update_msg = True
   
    try:
        while True:
            # poll for new tickers
            t = datetime.fromtimestamp(posix_now()/1000).strftime('%Y-%m-%dT%H:%M:%SZ')
            new_tickers = pull_window('Watchlist',[10, 77, 75, 350])
            new_tickers = [n for n in new_tickers if len(n)]
            if not new_tickers:
                if update_msg:
                    print(f"No New Tickers as of {t}")
                    update_msg = False
                time.sleep(2)
                continue
            else:
                if not update_msg:
                    sms=auth.send_sms(f"Found New Ticker(s): {new_tickers}" \
                        f" Time: {t}")
                    update_msg = True

            if verbose: print(f"new tickers: {new_tickers}")

            # omit previously sampled tickers. Tickers are sampled only after
            # max_sampling age has expired OR position has been CLOSED already
            # (check tda)
            passed_tickers = [n for n in new_tickers if not qt.is_ticker_sampled(n)]
            if verbose: print(f"passed tickers: {passed_tickers}")

            # get quotes on incompletely sampled tickers and update their dicts
            # (class members). Tickers of open positions are incompletely sampled
            # by default. 
            [qt.get_bid(n) for n in passed_tickers]
             
            # quote trends of incompletely sampled tickers will be inspected for
            # INCREASING values (for consecutive_incr_bids) to trigger_jump_pct.
            # quote trends of incompletely sampled tickers THAT HAVE OPEN
            # POSITIONS, will be inspected for DECREASING values (up to
            # consecutive_decr_bids) upon which the position will be CLOSED and
            # ticker appended to sampled_tickers list.

            if verbose: qt.print_obj_list()
            qt.position_management()
    
    except BaseException as err:
        print(f"Unexpected {err=}, {type(err)=}")
        print(traceback.format_exc())
        sms=auth.send_sms('Momentum Finder app has stopped.')
