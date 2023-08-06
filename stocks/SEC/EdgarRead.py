import requests
from os.path import exists
import json
import tqdm
import pdb

def get_cik_list():
    ################################################################################
    # Loading
    ################################################################################

    url_in = 'https://www.sec.gov/Archives/edgar/cik-lookup-data.txt'
    headers_dict = {'User-Agent': 'Sheldon Bish sbish33@gmail.com', \
            'Accept-Encoding':'deflate', \
            'Host':'www.sec.gov'}
    filename = 'CIK_List.txt'

    if not exists (filename):
        # Download raw CIK list
        rawlist = requests.get(url=url_in, headers=headers_dict)
        if rawlist.ok:
            # save list to txt file
            fid = open(filename,'w+')
            fid.write(rawlist.text)
        fid.close()
    else:
        fid = open(filename,'r')
        rawlist = fid.read()
        fid.close()

    ################################################################################
    # Cleaning
    ################################################################################

    cnt=0
    with open(filename, 'r', encoding='ISO-8859-1') as file:
        lines = file.readlines()
        name_cik = [(n.split(':')[0],n.split(':')[1]) for n in lines]

    name_cik = [(''.join([m for m in row[0] if (m.isalpha() or m.isspace())]) \
        ,row[1]) for row in name_cik]
    name_cik = [(row[0].lstrip(' ') ,row[1]) for row in name_cik if
            row[1].isdigit()]

    #fid = open('CleanCIKList.txt','w+')
    #fid.write(json.dumps(name_cik))
    #fid.close()
    
    print("CIK List Acquired!")
    return name_cik

if __name__ == "__main__":
    get_cik_list()
