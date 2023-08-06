from EdgarRead import get_cik_list
from cikread import get_ticker_cik
import requests
import json

headers_dict = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
        'Accept-Encoding':'gzip', \
        'Host':'www.sec.gov'}

# Look for new feeds from https://www.sec.gov/os/accessing-edgar-data
ciks = get_cik_list()
tiks = get_ticker_cik()

name = 'Bit Mining Ltd'

# match name to cik
ind = [n[0] for n in ciks].index(name.upper())
assert ind > 0 , "Company Name Not Found!"
cik = ciks[ind][1]
cind = [m[1] for m in tiks].index(cik)
cname = tiks[cind][0]

print(f"CIK of {name} ({cname}) is: {cik}")

url_in = 'https://data.sec.gov/submissions/CIK' + cik + '.json'
data = requests.get(url=url_in, headers=headers_dict)

if data.ok:
    print(data.text)
else:
    print(f"sec request failed: Code {data.raise_for_status}")
    print('Url ' + url_in + ' didn\'t work')
