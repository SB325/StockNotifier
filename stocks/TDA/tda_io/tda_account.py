import requests
import time
import json
from pprint import pprint
import math
from copy import copy

class tda_account:
    
    def __init__(self, auth): 
        self.auth = auth
        self.resource_url ='https://api.tdameritrade.com/v1/accounts/866675922'
        self.roundTrips : int
        self.currentBalances : dict
        self.initialBalance : float
        self.projectedBalance : float
        self.n_orders = 0
        self.workingOrders : list
        self.filledOrders : list
        self.closedOrders : list
        self.pendingOrders : list
        self.n_rejected = 0
        self.openPositions : list 
        self.auth.log('tda_account: Initiating tda_account class.')
    
    def __iter__(self):
        yield 'roundTrips', self.roundTrips
        yield 'currentBalances', self.currentBalances
        yield 'initialBalance', self.initialBalance 
        yield 'projectedBalance', self.projectedBalance 
        yield 'n_orders', self.n_orders 
        yield 'workingOrders', self.workingOrders 
        yield 'filledOrders', self.filledOrders 
        yield 'closedOrders', self.closedOrders 
        yield 'pendingOrders', self.pendingOrders
        yield 'openPositions', self.openPositions 

    def get_token(self):
        aut = 'Bearer ' + self.auth.access_token
        header = {'Authorization': aut} #.replace('\n','')}
        auth = {'apikey': self.auth.consumer_key}
        return header, auth 

    def get_positions(self, verbose=False):
        self.auth.refresh()
        try:
            header, auth = self.get_token()
            response = self.auth.get_req(url = self.resource_url, \
            params={'fields':'positions'}, \
            headers=header)
        except:
            msg = 'tda_account: web call failed'
            self.auth.log(msg)
            raise Exception(msg)
        #response.raise_for_status()
        time.sleep(0.5)
        # for each position, get ticker, date purchased, shares held,
        # sale price. place in self.positions as fields of struct array.
        # TODO: Get date of position opening for purposes of preventing round
        # trip trading.
        
        if not response.ok:
            print(f"get_positions POST request failed!")
            print(f"Post Error! Code {response.status_code}: " + \
            f"{response.reason}")
            self.auth.log('tda_account: get_positions POST request failed!')
        else:
            data = json.loads(response.text)
            #pprint(data)
            
            # Current Balance
            balances = data['securitiesAccount']['currentBalances']
            liquidationValue = balances['availableFunds']
            tradeableBalance = balances['buyingPowerNonMarginableTrade']
            self.currentBalances = {'liquidationValue':liquidationValue, \
                    'tradeableBalance':tradeableBalance}

            # Balance at start of day
            daystartbalances = data['securitiesAccount']['initialBalances']
            self.initialBalance = daystartbalances['accountValue']
            
            # Balance of current value of account and open positions
            self.projectedBalance = \
            data['securitiesAccount']['projectedBalances']['availableFunds']
            
            self.roundTrips = data['securitiesAccount']['roundTrips']
            
            if verbose:
                print('Current Balances:')
                pprint(self.currentBalances)
                print('Day\'s Initial Balance:')
                pprint(self.initialBalance)
                print('Projected Balance:')
                pprint(self.projectedBalance)
                print('Round Trips:')
                pprint(self.roundTrips)
            
            positions = data['securitiesAccount']['positions']
            self.openPositions = [p for p in positions if 'EQUITY' in p['instrument']['assetType']]
            #print(f"Day\'s Gain: {(self.projectedBalance-self.initialBalance)*100/self.initialBalance}")
            #print(f"Number of open Positions: {len(self.openPositions)}")
            #pprint(self.openPositions)
            self.auth.log('tda_account: Downloaded positions response')

    def get_quantity_held(self):
        # return dictionary where keys are tickers of open positions, and
        # values are quantity of shares held
        self.get_positions()
        return dict([(p['instrument']['symbol'],int(p['longQuantity'])) for p in \
        self.openPositions])

    def get_orders(self):
        self.auth.refresh()
        header, auth = self.get_token()
        try:
            response = self.auth.get_req(url=self.resource_url, \
                 params = {'fields':'orders'}, headers=header)
        except:
            msg = 'tda_account: get_orders web call failed'
            self.auth.log(msg)
            raise Exception(msg)
        response.raise_for_status()
        time.sleep(0.5)
        
        # json string to dictionary (data)
        data = json.loads(response.text) 
        #pprint(data)
        
        if 'orderStrategies' in data['securitiesAccount'].keys():
            orders = data['securitiesAccount']['orderStrategies']
            self.n_orders = len(orders)
            working = [n for n in orders if 'WORKING' in n['status']]
            filled = [n for n in orders if 'FILLED' in n['status']]
            closed = [n for n in orders if 'CLOSED' in n['status']]
            pending = [n for n in orders if 'PENDING_ACTIVATION' in n['status']]
        else:
            working = []
            filled = [] 
            closed = []
            pending = []
        
        self.pendingOrders = \
        [{k:n[k] for k in
        ('orderLegCollection','price','enteredTime','orderId') if k in n} \
        for n in pending]
        self.workingOrders = \
        [{k:n[k] for k in ('orderLegCollection','price','enteredTime','orderId') if k in n} for n in working]
        self.filledOrders = \
        [{k:n[k] for k in ('filledQuantity','closeTime', \
        'price','enteredTime','orderId') if k in n} for n in filled]
        self.closedOrders = \
        [{k:n[k] for k in ('orderLegCollection','orderId') if k in n} for n in closed]

        print(f"{len(self.filledOrders)} Orders Filled \n" \
        f"{len(self.workingOrders)} Working Orders \n" \
        f"{len(self.closedOrders)} Orders Closed \n" \
        f"{len(self.pendingOrders)} Orders Pending")
        self.auth.log('tda_account: Downloaded orders response')
    
    def calc_nshares(self, closeprice, min_pos_size, max_pos_size):
        self.get_positions()
        balance = self.currentBalances['liquidationValue']
        availablebalance = self.currentBalances['tradeableBalance']
        print(f"Avail: {availablebalance} | Bal: {balance}")
        if availablebalance < closeprice:
            # Can't afford this stock
            return 0
        
        if (balance < min_pos_size):
            msg = 'Not enough Buying power available to trade.'
            self.auth.log(msg)
            raise Exception(msg)
        if(balance < max_pos_size):
            max_pos_size = balance
        
        print(f"max pos size: {max_pos_size}")
        incr = 1.00
        buyprice = round(closeprice,2)
        nshares = math.floor((max_pos_size/buyprice))
        nshares = nshares - nshares%10  #round down to lower 10
        return nshares
