from tqdm import tqdm
from PIL import Image
import pytesseract
import time
import sys
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\stocks\TDA')
sys.path.append(r'C:\Users\sfb_s\src\Screen_Capture')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\utils')
sys.path.append(r'C:\Users\sfb_s\src\genutils')
sys.path.append(r'C:\Users\sfb_s\src\StockNotifier\postgres')
from get_ticker_list import get_ticker_list
from parse_screen import parse_screen
from pair_ticker_with_headline import pair_ticker_with_headline
from get_screenshot import get_screenshot
from postgres_io import postgres_io
import base64
from delay_hour import delay_hour
import requests
from sms import sms
import pdb
from post_image import post_image

pgio = postgres_io()
messager = sms()
table_name = 'real_time_news_data'
column_names = ['Time', 'Headline', 'Ticker']

def initialize_db_table():
    # check if database table exists, if not, create table
    tnames = pgio.view_table_names(table_name)
    if not tnames:
        types = [2**31+1,'AA','A']
        nullflags = [True] * len(column_names)
        pgio.create_table(table_name, column_names, types, nullflags)

def enter_data_into_table(newslist_sel):
    time_list = [n[column_names[-3]] for n in newslist_sel]
    headline_list = [n[column_names[-2]] for n in newslist_sel]
    ticker_list = [n[column_names[-1]] for n in newslist_sel]
    
    news_dict_list = [[n[column_names[-3]], n[column_names[-2]], \
    n[column_names[-1]]] for n in newslist_sel]
    
    pgio.enter_data_into_table(table_name, \
    column_names, news_dict_list)
    # TODO: avoid pushing already captured headlines to news_dict_list
    pgio.remove_repeated_rows(table_name)


#wait_start('07:59')
initialize_db_table()

# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = \
r'C:\Users\sfb_s\AppData\Local\Programs\Tesseract-OCR\tesseract'

tickers, cname = get_ticker_list()        
#[print(f"{t} | {cname[cnt]}") for cnt,t in enumerate(tickers)]   

delay = delay_hour()
newsdict = []
try:
    while (True):
        delay.wait_between(3,19)
        print('-----')
        frame = get_screenshot('Live News Main@thinkorswim [build 1976]')
        if (len(frame)):
            img = post_image(frame,'call_screenshot.png',(9, 106),True) 

        #newslist_sel = parse_screen(img, newsdict)

        #if not newslist_sel:
        #    continue

        #[print(n['Headline']) for n in newslist_sel]
        #newslist_sel = pair_ticker_with_headline(cname, tickers, newslist_sel)
        #pdb.set_trace()
        #enter_data_into_table(newslist_sel)

        time.sleep(5)
except BaseException as err:
    msg=f"Unexpected {err=}, {type(err)=}"
    print(msg)
    messager.send_sms(f"'read_img_ocr.py' has stopped. {msg}") 
