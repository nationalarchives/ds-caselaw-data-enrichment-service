# -*- coding: utf-8 -*-
"""
Created on Wed Feb 23 16:20:29 2022

@author: Imane.Hafnaoui
"""

import pandas as pd
import requests
from itertools import product
from xml.etree import ElementTree
import bs4 as BeautifulSoup

urid=pd.read_json('URIdescriptor.json')
# legtype = urid.params.type['category']['primary'][:3]
legtype = "ukpga"
legyear = [1997, 2021]
legnum = range(1, 69)

out={}
urltemplate = 'https://www.legislation.gov.uk/ukpga/%s/%s/data.xml'

for y in legyear:
    for n in legnum:
        url = urltemplate%(y,n)
        res=requests.get(url)
        
        if res.status_code == 200:
            # print (f"{url}, {res.status_code}")
            soup = BeautifulSoup.BeautifulSoup(res.content, "lxml")
            title = soup.find("dc:title").text
            print (title)
            # root = ElementTree.fromstring(res.content)
            # title = root[0][1].text
            out[title] = url
        else:
            print('%s: %s'%(res.status_code, url))
    
'''
Output example:
{'National Debt Act 1889': 'https://www.legislation.gov.uk/ukpga/1889/6/data.xml',
 'Wireless Telegraphy Act 1998 (repealed)': 'https://www.legislation.gov.uk/ukpga/1998/6/data.xml',
 'Petroleum Act 1998': 'https://www.legislation.gov.uk/ukpga/1998/17/data.xml',
 'Data Protection Act 1998': 'https://www.legislation.gov.uk/ukpga/1998/29/data.xml',
 'Supply and Appropriation (Anticipation and Adjustments) Act 2021': 'https://www.legislation.gov.uk/ukpga/2021/6/data.xml',
 'Domestic Abuse Act 2021': 'https://www.legislation.gov.uk/ukpga/2021/17/data.xml',
 'Compensation (London Capital & Finance plc and Fraud Compensation Fund) Act 2021': 'https://www.legislation.gov.uk/ukpga/2021/29/data.xml'}
'''

