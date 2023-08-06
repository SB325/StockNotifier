import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\screen_parser')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA')
from spicy_test import spicy_test
from spicy import spicy
import numpy as np
from similarity import similarity
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
from postgres_io import postgres_io
import pprint
from pair_ticker_with_headline import pair_ticker_with_headline
from get_ticker_list import get_ticker_list
#import textmessage
#textmessage.send('hi')

spicy = spicy()
#headline1 = "Spire Global Obtains $120 Million Credit Facility"

#s = spicy_test(headline1, spicy, False)
#print('Modified Headline:')
#print(s['modified_headline'])

print(spicy)
