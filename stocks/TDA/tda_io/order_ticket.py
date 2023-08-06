from datetime import datetime
import time 
import pprint

def select_from_tuple(tup: tuple, val: str):
    ind = list(tup).index(val)   # returns exception if not found
    return tup[ind] 

class order_ticket():
    def __init__(self, auth):
        self.auth = auth
        self.auth.log('order_ticket: Initializing order_ticket class.')
        
        self.orderType = {'val': None, \
            'range':('MARKET','LIMIT','STOP','STOP_LIMIT','TRAILING_STOP', \
            'MARKET_ON_CLOSE','EXERCISE','TRAILING_STOP_LIMIT')}
        self.session = {'val': None, \
            'range':('NORMAL','AM','PM','SEAMLESS')}
        self.price  : float
        self.stopPrice : float
        self.stopType = {'val': None, \
            'range':('STANDARD','BID','ASK','LAST','MARK')}
        self.duration = {'val': None, \
            'range':('DAY','GOOD_TILL_CANCEL','FILL_OR_KILL')}
        self.orderStrategyType = {'val': None, \
            'range':('TRIGGER','OCO','SINGLE', \
            'TRAILING_STOP','MARKET_ON_CLOSE','EXERCISE', \
            'TRAILING_STOP_LIMIT','NET_DEBIT','NET_CREDIT','NET_ZERO')}
        self.quantity : float
        self.assetType = 'EQUITY'  
        self.symbol : str
        self.instruction = {'val': None, \
            'range':('BUY','SELL','BUY_TO_OPEN','SELL_TO_CLOSE')}
        self.specialInstruction = {'val': None, \
            'range':('ALL_OR_NONE','DO_NOT_REDUCE', \
            'ALL_OR_NONE_DO_NOT_REDUCE')}
        self.quantityType = {'val': None, \
            'range':('ALL_SHARES','DOLLARS','SHARES')}
        self.cancelTime : int # when to auto cancel order (posixtime)
        self.releaseTime : str                  #date-time string)
        self.closeTime : str # (datetime string YYYY-MM-DD when to auto close position?
        self.stopPriceLinkType = {'val': None, \
            'range':('VALUE','PERCENT','TICK')}
        self.stopPriceOffset : float
        
    def set_session(self,val : str):
        self.session['val'] = select_from_tuple(self.session['range'], val) 

    def set_duration(self,val : str):
        self.duration['val'] = select_from_tuple(self.duration['range'], val)

    def set_orderType(self,val : str):
        self.orderType['val'] = select_from_tuple(self.orderType['range'], val)
    
    def set_quantity(self,val : float):
        assert val>0, 'Invalid entry for quantity type.'
        self.quantity = val 
    
    def set_stopType(self,val : str):
        self.stopType['val'] = select_from_tuple(self.stopType['range'], val)
    
    def set_instruction(self,val : str):
        self.instruction['val'] = select_from_tuple(self.instruction['range'], val)
    
    def set_specialInstruction(self,val : str):
        self.specialInstruction['val'] = select_from_tuple(self.specicalInstruction['range'], val)

    def set_quantityType(self,val : str):
        self.quantityType['val'] = select_from_tuple(self.quantityType['range'], val)
    
    def set_orderStrategyType(self,val : str):
        self.orderStrategyType['val'] = select_from_tuple(self.orderStrategyType['range'], val)

    def set_price(self,val : float):
        assert val>0, f'Invalid entry ({val}) for price type.'
        self.price = round(val,2)

    def set_stopPrice(self,val : float):
        assert val>0, f'Invalid entry ({val}) for price type.'
        self.stopPrice = val 
    
    def set_symbol(self,val : str):
        self.symbol = val

    def set_stopPriceLinkType(self,val: str):
        self.stopPriceLinkType['val'] = select_from_tuple(self.stopPriceLinkType['range'], val)
    
    def set_stopPriceOffset(self, val : float):
        self.stopPriceOffset = val
    
    # find out format of interface input
    #def set_cancelTime(self,val : int)
    #    now = time.time()
    #    assert (val < (now + 3600)) , 'cancelTime should be less than one hour from now.'
    #    #self.cancelTime = datetime.utcfromtimestamp(val).strftime('%Y-%m-%d')
    
    # find out format of interface input
    #def set_closeTime(self,val : int)
    #    self.closeTime = val)
        
    # check if all necessary fields of order are filled
    def filled(self):
        members = ['duration','orderType','quantity','stopPrice','stopType', \
            'price','symbol','quantityType']
        for cnt,i in enumerate(members):
            if eval('self.get_' + i + '()') is None:
                self.auth.log('order_ticket: Order ticket is incompletely formed.')
                return False
        self.auth.log({'order_ticket' : f'order_ticket: Order ticket is well formed: \n' \
        + f'self.duration: {self.get_duration()} \n' \
        + f'orderType: {self.get_orderType()} \n' \
        + f'quantity: {self.get_quantity()} \n' \
        + f'stopPrice: {self.get_stopPrice()} \n' \
        + f'stopType: {self.get_stopType()} \n' \
        + f'price: {self.get_price()} \n' \
        + f'symbol: {self.get_symbol()} \n' \
        + f'quantityType: {self.get_quantityType()} \n' \
        + f'stopPriceLinkType: {self.get_stopPriceLinkType()} \n' \
        + f'orderStrategyType: {self.get_orderStrategyType()} \n' \
        + f'stopPriceOffset: {self.get_stopPriceOffset()}'})
        return True
        
    def get_duration(self): return self.duration['val']
    def get_orderType(self): return self.orderType['val']
    def get_orderStrategyType(self): return self.orderStrategyType['val']
    def get_quantity(self): return self.quantity
    def get_session(self): return self.session['val']
    def get_stopPrice(self): return self.stopPrice
    def get_stopType(self): return self.stopType['val']
    def get_price(self): return self.price
    def get_symbol(self): return self.symbol
    def get_instruction(self): return self.instruction['val']
    def get_specialInstruction(self): return self.specialInstruction['val']
    def get_quantityType(self): return self.quantityType['val']
    def get_cancelTime(self): return self.cancelTime['val']
    def get_closeTime(self): return self.closeTime['val']
    def get_stopPriceLinkType(self): return self.stopPriceLinkType['val']
    def get_stopPriceOffset(self): return self.stopPriceOffset
        
    def single_buy_order(self):
        val = {
        'session' : self.get_session(), 
        'duration' : self.get_duration(), 
        'orderType' : self.get_orderType(), 
        'price' : self.get_price(), 
        'stopPriceLinkType' : self.get_stopPriceLinkType(), 
        'stopPriceOffset' : self.get_stopPriceOffset(), 
        'stopType' : self.get_stopType(), 
        'orderLegCollection' : 
        [ 
            { 
                'instruction':'BUY', 
                'instrument' : { 
                    'assetType' : 'EQUITY', 
                    'symbol':self.get_symbol() 
                }, 
                'quantity' : self.get_quantity() 
            } 
        ], 
        'orderStrategyType' : self.get_orderStrategyType()
        }
        self.auth.log('order_ticket: Crafted single buy order dictionary')
        return val
       
    def single_sell_order(self):
        val = {
        'complexOrderStrategyType': 'NONE',
        'session' : self.get_session(), 
        'duration' : self.get_duration(), 
        'orderType' : self.get_orderType(), 
        'price' : self.get_price(), 
        'stopPriceLinkBasis': 'BID',
        'stopPriceLinkType' : self.get_stopPriceLinkType(), 
        'stopPriceOffset' : self.get_stopPriceOffset(), 
        'orderStrategyType' : self.get_orderStrategyType(),
        'orderLegCollection' : 
         [ 
            { 
                'instruction':'SELL', 
                'instrument' : { 
                    'symbol':self.get_symbol(), 
                    'assetType' : 'EQUITY' 
                }, 
                'quantity' : self.get_quantity()
            } 
        ] \
        }
        self.auth.log('order_ticket: Crafted single sell order dictionary')
        return val
       
    def set_default_buy_ticket(self, nshares: int, buyprice: float, \
    tik: str, stoppriceoffset=5) -> bool:
        self.set_session('SEAMLESS')
        self.set_duration('GOOD_TILL_CANCEL')
        self.set_orderType('LIMIT')
        self.set_quantity(nshares)
        self.set_instruction('BUY')
        # price  must have 2 decimal places only!!
        self.set_price(buyprice)
        self.set_quantityType('SHARES')
        self.set_symbol(tik)
        self.set_stopType('MARK')
        self.set_orderStrategyType('SINGLE')
        self.set_stopPrice(buyprice*1.1)    # If stopPriceLinkType=VALUE 
        self.set_stopPriceLinkType('VALUE') #PERCENT')
        self.set_stopPriceOffset(stoppriceoffset) # If stopPriceLinkType=PERCENT
        # Record transaction
        return self.filled()
       
