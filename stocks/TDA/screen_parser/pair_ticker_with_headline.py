def is_alnum(char):
    if char.count('-'):
        return True
    return char.isalnum()

def pair_ticker_with_headline(cname, tickers, newslist_sel, verbose=False):
    common_elements = ['None']*len(newslist_sel)
    #print(common_elements)
    # for each headline

    for cnt,h in enumerate(newslist_sel):
        # for each line in headline
        headline = h['Headline']
        headline.replace('  ',' ')
        if not headline.find(': ')<0:
            ind = headline.index(': ')
            preheadline=headline[:ind]
            if len(preheadline.split()) > 2:
                #pre colon headline is too long suggesting b.s.
                continue
            headline = headline[ind+1:]
        hlist = headline.split()
        hlist = [''.join(filter(is_alnum, n)) for n in hlist ]
        if verbose: print(f"Filtered Headline: {hlist}")
        if len(hlist)>1:
            hlist1 = hlist[0]
            hlist2 = ' '.join([hlist[0], hlist[1]])
            if verbose: print(f"First word: {hlist1}, Second word: {hlist2}")
            test2=[cnt for cnt,n in enumerate(cname) if hlist2 in \
            n]
            test1=[cnt for cnt,n in enumerate(cname) if (hlist1 in \
            n) and n.find(hlist1)==0]
            if verbose:
                print(f"Test1: {test1}, Test2: {test2}")
                print(f"Match1: {[tickers[n] for n in test1]}," + \
                f"Match2:{[tickers[n] for n in test2]}")
                print(f"MatchName1: {[cname[n] for n in test1]}," + \
                f"MatchName2:{[cname[n] for n in test2]}")
            if len(test2)>0:
                # append cname to list of common elements
                sel_ticker = tickers[test2[0]]
                #print(f"selected ticker: {sel_ticker}")
                common_elements[cnt] = sel_ticker
            elif len(test1)>0:
                # append cname to list of common elements
                sel_ticker = tickers[test1[0]]
                #print(f"selected ticker: {sel_ticker}")
                common_elements[cnt] = sel_ticker
            else:
                common_elements[cnt] = []
        else:
            #print(f"s: {s}, headline: {headline}")
            common_elements[cnt] = []

    #print(f"Common Elements: {common_elements}")
    [n.update({'Ticker':common_elements[cnt]}) for cnt,n in enumerate(newslist_sel)]
    [print(f"{n['Ticker']} : {n['Headline']}") for n in newslist_sel]

    return newslist_sel
