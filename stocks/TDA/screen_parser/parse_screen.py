import pytesseract
import datetime as dt
import time
import nltk
from nltk.tokenize import  word_tokenize
from PIL import Image
import math

def parse_screen(img, newsdict):
    topstring = pytesseract.image_to_string(img)
    str_array = topstring.split('\n')

    times = []
    headlines =[]
    for n in str_array:
        headline = []
        if not n.find('News will appear here')<0:
            # no news on screen, return
            time.sleep(6)
            return 0
        for s in n.split(' '):
            if s.count(':') >= 2:
                times.append(s)
            elif len(s)> 1:
                headline.append(s)
        if len(headline)>0:
            headlines.append(' '.join(headline))

    times = [n.replace(',','') for n in times ]
    times = [n.replace('.','') for n in times ]
    #print(f"Nheadlines: {len(headlines)}, \nheadlines: {headlines}")
    #print(f"NTimes: {len(times)}, \nTimes: {times}")

    if len(times) != len(headlines):
        print(f"Number of times ({len(times)}) != ({len(headlines)})")
        print(f"Parsed String Array: \n{str_array}")
        print(f"***")
        print(f"Times \n{times}")
        print(f"Headlines \n{headlines}")
        return 0 
    
    # Current # Date
    today = dt.date.today()
    #print(f"Today: {today}")
    # times to posixtimes
    date_object = [dt.datetime.strptime('{d}T{t}'.format(d=today, \
    t=news_time), "%Y-%m-%dT%H:%M:%S") for news_time in times]
    posixt = [int(time.mktime(dat.timetuple())) for dat in date_object]
    
    # in the event that any in posixt is greater than
    # math.floor(time.time()), remove headline.
    negtimes = [cnt for cnt,n in enumerate(posixt) if n>math.floor(time.time())]
    if negtimes:
        print(f"Error: posixtimes generated to the future!!")
        posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if \
        negtimes.count(cnt)]
        headlines = [x for cnt,x in enumerate(headlines) if negtimes.count(cnt)]
    headlines = [n for n in headlines if n]
    
    # remove headlines containing "movers" and "gainers"
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x.find('Movers')<0]
    headlines = [x for x in headlines if x.find('Movers')<0]
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x.find('Gainers')<0]
    headlines = [x for x in headlines if x.find('Gainers')<0] 
    # Remove headlines that begin with starting non alpha characters in headline
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x[0].isalpha()]
    headlines = [n for n in headlines if n[0].isalpha()] 
    # Remove headlines that begin with certain strings
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if \
    x.split(' ')[0].find('Stock')<0]
    headlines = [n for n in headlines if n.split(' ')[0].find('Stock')<0]
    #-
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x.find('Moving')<0]
    headlines = [x for x in headlines if x.find('Moving')<0]
    # Remove headlines beginning with 'Sector Update:'
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if \
        x.find('Sector Update:')<0]
    headlines = [x for x in headlines if x.find('Sector Update:')<0]
    # Remove headlines beginning with 'Why'
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x.find('Why')<0]
    headlines = [x for x in headlines if x.find('Why')<0]
    # Remove headlines beginning with 'Shares of several'
    posixt = [posixt[cnt] for cnt,x in enumerate(headlines) if x.find('Shares of several')<0]
    headlines = [x for x in headlines if x.find('Shares of several')<0]
    
    # remove asterisks from headline
    headlines = [x.replace('*','') for x in headlines]
    # Remove starting apostrophe characters in headline
    headlines = [n[1:] if not n[0].isalnum() else n for n in headlines]
    # Remove all " 's " pluralizers in headline
    headlines = [n.replace("'s","") for n in headlines ]

    #print(f"#posixt: {[x for x in posixt]}")
    #print(f"#news: {[x for x in headlines]}")

    newsdict.extend([{'Time':posixt[cnt], 'Headline':n} \
            for cnt,n in enumerate(headlines)])

    # Removing Duplicates
    news = []
    [news.append(x) for x in newsdict if x not in news]

    # get part of speech and add to news dict list
    pos = []
    [pos.extend([nltk.pos_tag(word_tokenize(n['Headline']))])
    for n in news]
    for cnt,n in enumerate(news):
        pos[cnt].pop()
        news[cnt].update({'nltk':pos[cnt]})

    # Remove news headlines based on similar parts of speech words
    NNlist = []
    #for ind in news:
    #    NNlist.append([n[0] for n in ind['nltk'] if n[1].startswith('NN')])

    cut = [False]*len(NNlist)
    for cnt,n in enumerate(NNlist):
        if (cnt>0):
            #print(cnt)
            if (cnt==1):
                nntemp = NNlist[0]
            else:
                nntemp = NNlist[0:cnt]
                nntemp = [item for sublist in nntemp for item in sublist]
            #print(f"nntemp: {nntemp}")
            lenset = list(set(n) & set(nntemp))
            cut[cnt] = (len(lenset)>4) | \
                (len(n)<4)
    ind2remove = [i for i, x in enumerate(cut) if x]
    newslist_sel = [x for cnt,x in enumerate(news) if cnt not in ind2remove]
    
    # Return list of dict of news with keys time, headlines, nltk
    return newslist_sel
