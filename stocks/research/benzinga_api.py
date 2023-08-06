# News Key:  23720bd194684507bb3f1e825257480f  (effective until 2021-07-26)
# REST API Docs: https://docs.benzinga.io/benzinga/newsfeed-v2.html
# Websocket Docs: https://docs.benzinga.io/benzinga/newsfeed-stream-v1.html

# Press Releases Key: 3de26b6b47f74653a85c66099679db8e (effective until 2021-07-26)

#import time
from benzinga import financial_data, news_data
#import json
from pprint import pprint
from datetime import datetime
import time
import requests
import re
import html
from itertools import compress
import numpy as np
from bs4 import BeautifulSoup

class benzinga_api:
    '''
    capture fundamental, data at daily frequency and save to disk.
    TYPE: array of struct. Each element is struct containing ticker,
    descrip and data elements
    (one element per time point)
    '''
    def __init__(self,auth,pgio):
        self.newskey = '23720bd194684507bb3f1e825257480f'
        self.prkey = '3de26b6b47f74653a85c66099679db8e'
        self.pgio = pgio
        self.auth = auth
        self.fin = financial_data.Benzinga(self.newskey) # not working
        self.paper = news_data.News(self.newskey)
        tnames = self.pgio.view_table_names(self.table_name())
        if not tnames:
            types = ['A',2**31+1,5,'A','AA','AAA','AA','AA','AA','AA']
            nullflags = [True]*len(types)
            self.pgio.create_table(self.table_name(), self.column_names(), types, nullflags)
        self.auth.log('benzinga_api: Initialized benzinga_api class')     
            
    def table_name(self):
        suffix = 'mktd'
        self.tablename = 'news_' + suffix
        return self.tablename
    
    def column_names(self):
        # 1. Create news table with column names:
        #   1.id                # unique identifier for news story
        #   2.author            # source of news story
        #   3.created           # date created
        #   4.title             # news title
        #   5.url               # url to news story page
        #   6.body              # body of story page (minus xml tags)
        #   7.channels          # category of news story
        #   8.stocks            # tickers related to news story
        #   9.tags              # keywords related to news story
        self.columnnames = ['Ticker','posixtime_ms','id','author','title','body','url', \
                            'channels','stocks','tags']
        return self.columnnames
    
    def filter_returns(self,omitlist, includelist, initlist):
        # fileter_returns returns a logical list containing true where
        #   elements of initilist contain a value in includelist and 
        #   where elements of initilist do not contain a value in omitlist
        omvallist=[]
        for omval in omitlist:
            #omvallist.append(list(compress(title, \
            #                [not('Stocks' in word) for word in title])))
            omvallist.append(np.array([not(omval in word) for word in initlist]))
        omvallist = np.all(omvallist, axis=0)
        
        
        incllist=[]
        for elval in includelist:
            incllist.append(np.array([elval in word for word in initlist]))
        incllist = np.all(incllist, axis=0)
        
        # returns [1xm] boolean list
        return np.logical_and(omvallist,incllist)
        
    def get_latest_news(self, ticker, cname, dat_from='2011-01-01', dat_to=None):
        # News download is paged. For a given page size, loop through until 
        # all news is gathered for a ticker.
        pgsize=1000
        pg=0
        #dat_from='2011-01-01' #"YYYY-MM-DD"
        #dat_to=None
        upd_since=None
        pub_since=None
        ch=None
        newsdata = []
        
        while (((pg+1)*pgsize) < 10000): 
            news = self.paper.news(pagesize=pgsize, \
                        page=pg, \
                        date_from=dat_from, \
                        date_to=dat_to, \
                        updated_since=upd_since, \
                        publish_since=pub_since, \
                        company_tickers=ticker, \
                        channel=ch )
            if not news:
                print('Finished getting Newsdata for ' + ticker + '.')
                break;
            newsdata.extend(news)
            pg+=1
        
        if not newsdata:
            return
        iddb = self.pgio.get_entire_column(self.table_name(), 'id')
        temp = set([i.get('id') for i in newsdata])
        matching_ind = [i for i, val in enumerate(iddb) if val in temp]
        if matching_ind:
            del newsdata[matching_ind]
        
        url_list = [i.get('url') for i in newsdata]
        title = [i.get('title') for i in newsdata]
        
        omissionlist = ['52-Week', \
                        'Stocks']
        exclusiveadmissionlist = [cname]
        filtlist = self.filter_returns(omissionlist, exclusiveadmissionlist, title)
        
        if not any(filtlist):
            return
        
        newsdata = list(compress(newsdata,filtlist))
        url_list = list(compress(url_list,filtlist))
        title =  list(compress(title,filtlist))
        
        posixt = self.convert_time_to_posixtime([i.get('created') for i in newsdata])
        # add posixt as column to table
        stocklists = self.get_headline_related_stock_list( \
                            [i.get('stocks') for i in newsdata])
        channellists = self.get_headline_related_channel_list( \
                            [i.get('channels') for i in newsdata])
        taglists = self.get_headline_related_tag_list( \
                            [i.get('tags') for i in newsdata])
              
        newsbody = self.get_headline_related_news_list( \
                            url_list, \
                            title)

        dat = [[ticker]*len(newsdata), \
                posixt, \
                [i.get('id') for i in newsdata], \
                [i.get('author') for i in newsdata], \
                title, \
                newsbody, \
                url_list, \
                channellists, \
                stocklists, \
                taglists]
        
        dat2=[]
        for cnt,i in enumerate(dat[0]):
            dat2.append([dat[0][cnt],dat[1][cnt],dat[2][cnt],dat[3][cnt], \
                        dat[4][cnt],dat[5][cnt],dat[6][cnt],dat[7][cnt], \
                        dat[8][cnt],dat[9][cnt]])
                
        self.pgio.enter_data_into_table(self.table_name(), self.column_names(), dat2)
        #return newsdata
    
    def convert_time_to_posixtime(self,datelist):
        posix_dt = []
        for i in datelist:
            dt = datetime.strptime(i, "%a, %d %b %Y %H:%M:%S %z")
            posix_dt.append(int(time.mktime(dt.timetuple())*1000))
        return posix_dt
    
    def get_headline_related_stock_list(self,stocklists):
        slists = []
        for i in stocklists:
            stocks = str([hh.get('name') for hh in i])
            if len(stocks)>1000:
                stocks = stocks[:999]
            slists.append(stocks)
        return slists
    
    def get_headline_related_channel_list(self,channellists):
        clists = []
        for i in channellists:
            channels = str([hh.get('name') for hh in i])
            if len(channels)>1000:
                channels = channels[:999]
            clists.append(channels)
        return clists
    
    def get_headline_related_tag_list(self,taglists):
        tlists = []
        for i in taglists:
            tags = str([hh.get('name') for hh in i])
            if len(tags)>1000:
               tags = tags[:999] 
            tlists.append(tags)
        return tlists
    
    def get_headline_related_news_list(self,newslists, titles):
        # replaces empty 'body' value for content of url page minus xml tags
        nlists = []
        for cnt, val in enumerate(newslists): 
            response = requests.get(val)
            soup = BeautifulSoup(response.content,'html5lib')
            text = soup.get_text(strip = True)
            if text.find('CommentsShare:')>=0 and text.find('2021 Benzinga')>=0:
                subtext = text[text.index('CommentsShare:'):text.index('2021 Benzinga')]
            else: 
                subtext = ''
            subtext = subtext.replace('\'',' ')
            subtext = '\'' + subtext.replace(':',' ')[:9999] + '\''
    
            nlists.append(subtext)
            print('{:.2f}% news downloaded'.format(cnt/len(newslists)*100))

        return nlists
    
    def update_news_body(self,ticker,time):
        # get all news urls for ticker
        respon = self.pgio.get_values_eq_val_given_ticker(self.table_name(), \
                        'url', 'ticker', ticker,'posixtime_ms',time)
        
        response = requests.get(respon)
        soup = BeautifulSoup(response.content,'html5lib')
        text = soup.get_text(strip = True)
        if text.find('CommentsShare:')>=0 and text.find('2021 Benzinga')>=0:
            subtext = text[text.index('CommentsShare:'):text.index('2021 Benzinga')]
            print(subtext) 
        else:
            subtext = ''

        self.pgio.replace_cell(self.table_name(), 'body', 'posixtime_ms', \
                    time, subtext)

        
        
    def strip_xml_tags(self,content): 
        xmlremoved = re.sub('<[^<]+>', "", content)
        return re.sub('{[^{]+}', "", xmlremoved)