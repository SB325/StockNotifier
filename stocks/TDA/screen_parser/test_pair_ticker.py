import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA\screen_parser')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA')
from pair_ticker_with_headline import pair_ticker_with_headline
from get_ticker_list import get_ticker_list

tickers, cname = get_ticker_list()
newslist_sel = [{'Headline':'Rhythm Granted FDA Approval For Co Imcivree'}]
news_out = pair_ticker_with_headline(cname, tickers, newslist_sel, True)
