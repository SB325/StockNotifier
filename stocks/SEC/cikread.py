import requests

def get_ticker_cik():
    url_in = 'https://www.sec.gov/include/ticker.txt'
    headers_dict = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
                        'Accept-Encoding':'deflate', \
                                    'Host':'www.sec.gov'}
    data = requests.get(url=url_in,headers=headers_dict)

    assert data.ok, 'failed'

    lines = data.text.split('\n')
    lines = [m.split('\t') for m in lines]
    lines = [(m[0].upper(), m[1].zfill(10)) for m in lines]
    
    return lines
