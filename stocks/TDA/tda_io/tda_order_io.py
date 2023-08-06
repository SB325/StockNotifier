import requests
import json
from datetime import datetime
import time
import math
import order_ticket
from pprint import pprint
import requests

class tda_order_io:
    def __init__(self, auth, acct):
        self.resource_url = 'https://api.tdameritrade.com/v1/accounts/866675922'
        self.acct = acct  # balances
        self.retries = 0
        self.auth = auth
        self.auth.log('tda_order_io: Initiating tda_order_io class.')
    
    def get_token(self):
        header = {'Authorization': f"Bearer {self.auth.access_token}", \
            "Content-Type":"application/json"} 
        auth = {'apikey': self.auth.consumer_key}
        return header, auth

    def place_order(self,order_t: dict):
        # Do not allow orders to be placed if one of the following
        # things are true: 1) tradeableBalance are less then 50# of
        # liquidationValue, 2) roundTrips>2 3) There is already an
        # existing order, 4) There is already an existing position, or 5)
        # there is a position to sell if a sell order 
        self.acct.get_orders()
        self.acct.get_positions()
        tradeableBalance = self.acct.currentBalances['tradeableBalance']
        liquidationValue = self.acct.currentBalances['liquidationValue']
        balance_test = tradeableBalance/liquidationValue > 0.5
        ## TODO: round trip test should prevent the opening of more positions than there are
        # allowable round trips. The number of positions that can be
        # opened are effectively unlimited, but closing more than the
        # few allowed in the same day will be disastrous.
#             round_trip_test = (self.acct.roundTrips + numel(self.acct.openPositions)) < 3
        # TODO: self.acct.openPositions should reflect positions opened TODAY.
        # create new member variable in acct for this.

        # TODO: Opened TODAY:
        #opened_today = self.acct.openPositions['enteredTime']
        #opened_today_posix = 
        #now = 
        #opened_today_test = (now-opened_today_posix)<3600*12  # 12 hours ago
        #should make it yesterday fix this.
        #closedtime = self.acct.filledOrders
        #today = datetime.now().strftime('%m-%d')
        #new_open_positions = 0
        #for i in closedtime:
        #    mmdd = i['closeTime'].rsplit('-')[1:2]
        #    if mmdd == today:
        #        new_open_positions+=1
        
        # When calculating whether or not entering an order will risk exposure
        # to the PDT rule, include any currently working orders that would add 
        # to the round trip tally if the working order was a sell order.
        # With 2 RT's and one working buy order, the working buy order would
        # effectively block additional buy orders, as this buy position closing
        # would bring RT count to 3. If 2 buy orders are allowed at the time of
        # 2RT's, then only one could be closed that day without violating the
        # PDT rule.
        round_trip_test = (self.acct.roundTrips+len(self.acct.workingOrders)) < 3
        
        # TODO: add to previous todo-> PENDING, WORKING positions should be
        # added to positions FILLED today as those BUY position types will add
        # to potential round trips should they be sold same-day.
        working_order_test = len(self.acct.workingOrders) ==0

        # TODO: Rather than anticipating the possible sale of multiple open
        # positions, consider that once there are 3 round trip trades, this
        # will lock out the ability to open other positions automatically.
        # existing_position_test = self.acct.openPositions==0
        issellorder = \
        order_t['orderLegCollection'][0]['instruction'].find('SELL') >= 0
        valid_order = True

        test_summary = f"\n====== Order Execution Requirements (Buy): ======\n" \
                    f"Balance Test:...............................{balance_test}\n" \
                    f"Is this a sell order?.......................{issellorder}\n" \
                    f"Are there < 3 round trips on account?......{round_trip_test}\n" \
                    f"=================================================\n" 
        print(test_summary)
        response = []
        # Condition order entry if
        # enough available percentage of account is available for BUY
        # any sell order
        # round trips are less than 3
        # NOTE: This places no limit on number of BUY orders or open positions,
        # but once round_trip_test becomes false, you can only sell positions
        # acquired before today. Need a tda_account variable for positions
        # opened before today as eligible to sell with a false round_trip_test.
        # Otherwise, once the test fails, no selling can occur until it passes.
        if ((balance_test and not issellorder) or issellorder) and round_trip_test:
            
            self.auth.refresh()
            val = {'time': str(math.floor(time.time())*1000)}
            self.auth.log(json.dumps(val))
            data_ = json.dumps(order_t)
            pprint(data_)
            header, auth = self.get_token()
            response = requests.post(url=self.resource_url \
                    + '/orders', headers = header, json=order_t)
            if response.ok:
                self.auth.log([ 'tda_order_io: POST request to PLACE_ORDER'\
                + 'on ' +
                order_t['orderLegCollection'][0]['instrument']['symbol'] + 'succeeded!' ]) 
                print(f"Response ({response.status_code}):{response.reason}")
            else:
                print(f"Response tda_order_io: POST request failed!({response.status_code}) Sent Order:")
                self.auth.log([ 'tda_order_io: POST request failed!' ]) 
                response.raise_for_status()
        else:
            if not balance_test:
                msg = f"Available Funds ({tradeableBalance}) too low to place this order" \
                f"Sending SMS instead."
                sms=self.auth.send_sms('Buy: ' + \
                str(order_t['orderLegCollection'][0]['quantity']) + ' shares of ' + \
                order_t['orderLegCollection'][0]['instrument']['symbol'])
                print(msg)
                self.auth.log([msg])
                response = requests.get(url='https://api.tdameritrade.com/v1/accounts') 
            if ~round_trip_test:
                msg = f"No round trip trades available to support order." \
                f"Sending SMS instead."
                sms=self.auth.send_sms('Buy: ' + \
                str(order_t['orderLegCollection'][0]['quantity']) + ' shares of ' + \
                order_t['orderLegCollection'][0]['instrument']['symbol'])
                print(msg)
                self.auth.log('tda_order_io: ' + msg)
                #raise Exception
                response = requests.get(url='https://api.tdameritrade.com/v1/accounts') 
        return response
    
    def replace_order_by_id(self, data_, orderId ):
        self.auth.refresh()
        # TODO: new trade data_ needed
        try:
            header, auth = self.get_token()
            response = requests.put(self.resource_url + '/orders/' \
            + orderId ,data=data_, header=header)
        except:
               self.auth.log(['tda_order_io: PUT request failed!' ]) 
        
        self.auth.log('tda_order_io: Replaced order.') 
        return response
        
    def cancel_order(self,orderId: int):
        self.auth.refresh()
        logstr = {'time': str(math.floor(time.time())*1000), \
                  'cancel_order': str(orderId)}
        self.auth.log(json.dumps(logstr))
        header, auth = self.get_token()
        try:
            data = requests.delete(url = self.resource_url + '/orders/' \
                + str(orderId), headers=header)
            if data.status_code < 400:
                print(f"Successfully cancelled order {orderId}. Response {data.status_code}")
            else: print(data.status_code)
        except:
            print(f"failed to cancel order {orderId}. Response {data.status_code}")
            self.auth.log(['tda_order_io: DELETE request failed!' ]) 
        self.auth.log(['tda_order_io: Order ' + str(orderId) + ' cancelled.']) 
        time.sleep(0.5)
        return data
   
    def cancel_all_orders(self):
        self.auth.refresh()
        self.acct.get_orders()
        ord_Id = [n['orderId'] for n in self.acct.pendingOrders]
        for oid in ord_Id:
            self.cancel_order(oid)
        ord_Id = [n['orderId'] for n in self.acct.workingOrders]
        for oid in ord_Id:
            self.cancel_order(oid)
