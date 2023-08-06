import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\tda_io')
sys.path.append(r'C:\Users\sfb_s\src\genutils')
sys.path.append(r'C:\Users\sfb_s\src\Screen_Capture')
import numpy as np
import time
import json
import pprint
import pdb

from datetime import datetime
from posix_now import posix_now

from tda_auth import tda_auth
from tda_market_data import tda_market_data
from order_ticket import order_ticket
from tda_account import tda_account
from tda_order_io import tda_order_io

class ticker_obj:
    def __init__(self, ticker, verbose):
        self.verbose = verbose
        self.ticker_is_sampled = False
        self.position_has_been_opened = False
        self.symbol = ticker
        self.bid_list = [] # list of tuples (posixtime, price)
        if self.verbose: print('ticker_obj constructor')
    
    def add_bid(self, bid):
        self.bid_list.append((posix_now(), bid))
        if self.verbose: print('add_bid')
        
    def set_ticker_sampled(self):
        self.ticker_is_sampled = True
        if self.verbose: print('ticker_sampled')

    def print_ticker_obj(self):
        # make entire object a dict and pprint it
        print(self.__dict__)

quotevals = ['askPrice','askSize','assetType', \
    'bidPrice','bidSize','closePrice', \
    'highPrice','netPercentChangeInDouble', \
    'realimeEntitled','totalVolume',
    'tradeTimeInLong']

class quote_trend:
    def __init__(self, md, ot, order, acct, config, verbose):
        # 'max_entry_sampling_age' means deadline to reach 'percent_jump_trigger'
        # before quitting
        # 'max_exit_sampling_age' means max age of open position
        # 'percent_drop_trigger' means trailing stop pct value
        self.md_ = md
        self.ot_ = ot
        self.acct_ = acct
        self.order_ = order
        self.max_entry_sampling_age = config['max_entry_sampling_age']
        self.max_exit_sampling_age = config['max_exit_sampling_age']
        self.trigger_drop_pct = config['percent_drop_trigger']
        self.trigger_jump_pct = config['percent_jump_trigger']
        self.mandatory_hold_time_mins = config['mandatory_hold_time_mins']
        
        self.ticker_obj_list = [] 
        self.verbose = verbose
        if self.verbose: print('quote_trend constructor')
   
    def open_or_close_position(self, ticker='', price=0.0, close=False, \
        *argv):
        if close:
            self.ot_.auth.send_sms(f"Attempting to close position " \
                f"on {ticker}")
            sharesdict = self.acct_.get_quantity_held()
            if ticker not in sharesdict.keys():
                msg = 'Buy order probably did not go though.' + \
                    'ticker not found in list of positions'
                if self.verbose: print(msg)
                sms = self.ot_.auth.send_sms(msg)
                return Exception
            nshares = sharesdict[ticker]
            if nshares > 0:
                if self.ot_.set_default_buy_ticket(nshares, price, ticker, \
                    self.trigger_drop_pct):
                    #if argv[0]=='trailing':
                    #    self.ot_.set_orderType('TRAILING_STOP')
                    #    self.ot_.set_stopPriceLinkType('PERCENT')
                    #    order_tick = self.ot_.single_sell_order()
                    #    msg=f"Selling {nshares} shares of {ticker} using " \
                    #    + f"{self.trigger_drop_pct}% trailing stop."
                    #else:
                    order_tick = self.ot_.single_sell_order()
                    msg=f"Selling {nshares} shares of {ticker} at ${price}/share."
                    self.ot_.auth.send_sms(msg)
            else:
                self.ot_.auth.send_sms(f"Attempted to sell 0 shares of {ticker}")
        else:
            nshares = self.acct_.calc_nshares(price, 0, 10000)
            if self.ot_.set_default_buy_ticket(nshares, price, ticker, self.trigger_drop_pct):
                order_tick = self.ot_.single_buy_order()
                msg=f"Buying {nshares} shares of {ticker} at ${price}/share."
                sms=self.ot_.auth.send_sms(msg) 
        
        if self.verbose: print('open_or_close_position')
        response = self.order_.place_order(order_tick)
        if close:
            # wait for order execution to finish
            while self.acct_.get_quantity_held()[ticker] > 0:
                time.sleep(2)
                print('waiting for order execution to finish')
            
        else:
            # wait for order execution to finish
            if ticker in self.acct_.get_quantity_held().keys():
                while self.acct_.get_quantity_held()[ticker] != nshares:
                    time.sleep(2)
                    print('waiting for order execution to finish')                 

    def get_bid(self, ticker=''):
        # append quote bid to ticker's bid list
        data_ = self.md_.get_quote(ticker)
        datajson = json.loads(data_.text)
        if not ticker in datajson.keys():
            return
        quote=datajson[ticker]
        quote_downselect= {k: v for k, v in quote.items() if k in quotevals}
        bid = quote_downselect['bidPrice']
        
        bid_added = False
        if self.ticker_obj_list:
            for n in self.ticker_obj_list:
                if n.symbol==ticker:
                    n.add_bid(bid)
                    bid_added = True
            if not bid_added:
                self.ticker_obj_list.append(ticker_obj(ticker, self.verbose))
                [obj.add_bid(bid) for obj in self.ticker_obj_list \
                    if obj.symbol == ticker]
        else:
            self.ticker_obj_list.append(ticker_obj(ticker, self.verbose))
            [obj.add_bid(bid) for obj in self.ticker_obj_list \
                if obj.symbol == ticker]
        if self.verbose: print('get_bid')
    
    def position_management(self):
        for t_obj in [obj for obj in self.ticker_obj_list if not obj.ticker_is_sampled]:
            times = [n[0]/1000 for n in t_obj.bid_list]
            bids = [n[1] for n in t_obj.bid_list]
            d_bids = np.array(bids)
            diff_bids = np.diff(d_bids)
            if len(bids)<2:
                if self.verbose: print('no bids')
                continue
            if t_obj.position_has_been_opened:
                #self.ot_.auth.send_sms(f"open positddion exists on {t_obj.symbol}")
                if (times[-1]-times[0])/60 >= self.max_exit_sampling_age:
                    # close long position
                    self.open_or_close_position(t_obj.symbol, bids[-1], True)
                    #hopefully that overrode the trailing stop order...
                    # set ticker as sampled
                    t_obj.set_ticker_sampled()
                else: 
                    # check to see if bid has dropped more than
                    # t_obj.trigger_drop_pct. If so, sell at bid[-1]
                    mbids = max(bids)
                    if 100*(mbids-bids[-1])/mbids >= self.trigger_drop_pct:
                        self.open_or_close_position(t_obj.symbol, bids[-1], True)
                        t_obj.set_ticker_sampled()

            else:
                if (times[-1]-times[0])/60 >= self.max_entry_sampling_age:
                    # give up on this ticker, taking too long 
                    self.ot_.auth.send_sms(f"{t_obj.symbol} is a dud!")
                    t_obj.set_ticker_sampled()
                else:
                    if 100*(bids[-1]-bids[0])/bids[0] \
                        >= self.trigger_jump_pct:
                        self.ot_.auth.send_sms(f"{t_obj.symbol} is getting " \
                            f"bought!")
                        # open long position
                        self.open_or_close_position(t_obj.symbol, \
                        bids[-1], False)
                        t_obj.position_has_been_opened = True
                        # mandatory position hold time
                        time.sleep(self.mandatory_hold_time_mins*60)
                        # Set trailing stop (Can't get TDAPI's trailing stop to
                        # work. Create makeshift one here
                        #self.open_or_close_position(t_obj.symbol, \
                        #    bids[-1], True, 'trailing', self.trigger_drop_pct)
                        t_obj.bid_list.clear()
                        self.get_bid(t_obj.symbol)
        if self.verbose: print('position_management')

    def is_ticker_sampled(self, ticker):
        # get sampled_tickers 
        out = False
        if self.ticker_obj_list:
            samplecheck = [n.ticker_is_sampled for n in self.ticker_obj_list if n.symbol==ticker]
            assert len(samplecheck)<=1, "No more than one ticker can possibly be checked."
            if not len(samplecheck):
                out = False
            else:
                out = samplecheck[0]
                
            if self.verbose: print('is_ticker_sampled')
        return out

    def print_obj_list(self):
        [n.print_ticker_obj() for n in self.ticker_obj_list]
        

