import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

def getFloorPrice():
    slug = 'thecurrency'
    openseaUrl = f'https://opensea.io/collection/thecurrency'
    openseaUrl2 = f'https://opensea.io/assets/{slug}?search[sortAscending]=true&search[sortBy]=PRICE&search[toggles][0]=BUY_NOW'
    page = requests.get(openseaUrl2)
    soup = BeautifulSoup(page.content, "html.parser")
    print(f'{page}')
    view = soup.find("div", {"class": "AssetsSearchView--assets"})
    footer = view.find("div", {"class": "AssetCardFooter--price"})
    fpa = footer.findChild("div", {"class": "AssetCardFooter--price-amount"})
    view = fpa.findChild("div", {"class": "Price--amount"})
    floor_price = str(view.text)
   # floor_price = 100
    return floor_price

getFloorPrice()