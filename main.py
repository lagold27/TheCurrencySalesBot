import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

class openseaSalesBot():
    def __init__(self):
        self.asset_range = 20

    def requestLastSales(self):
        # Request event data
        json_data = self.successfulEventData()
        return self.parseSuccesfulEventData(json_data)

    # being deprecated due to WAF changes by openSea that block requests from python scripts
    #def getFloorPrice(self):
        #slug = 'thecurrency'
        #openseaUrl = f'https://opensea.io/collection/thecurrency'
        #page = requests.get(openseaUrl)
        #soup = BeautifulSoup(page.content, "html.parser")
        #print(f'{soup}')
        # view = soup.find("div", {"class": "AssetsSearchView--assets"})
        #footer = view.find("div", {"class": "AssetCardFooter--price"})
        #fpa = footer.findChild("div", {"class": "AssetCardFooter--price-amount"})
        #view = fpa.findChild("div", {"class": "Price--amount"})
        #floor_price = str(view.text)
        #floor_price = 100
        #return floor_price

    def successfulEventData(self):
        url = "https://api.opensea.io/api/v1/events"
        asset_contract_address = '0xaadc2d4261199ce24a4b0a57370c4fcf43bb60aa'  # Currently set to Hirst - The Currency
        querystring = {"only_opensea": "true", "offset": "0", "limit": str(self.asset_range),
                       "asset_contract_address": asset_contract_address, "event_type": "successful"}
        response = requests.request("GET", url, headers={"Accept": "application/json"}, params=querystring)
        return json.loads(response.text)

    def parseSuccesfulEventData(self, json_dump):
        json_list = []
        # Loop through the last sales
        for i in range(self.asset_range):
            # json only contains the last sale info
            asset_info = json_dump['asset_events'][i]['asset']
            image_url = asset_info['image_url']
            punk_name = asset_info['name']
            product_link = asset_info['permalink']

            # Seller info
            seller_info = json_dump['asset_events'][i]['seller']
            if (seller_info['user'] == None):
                seller_username = 'None'
            else:
                seller_username = seller_info['user']['username']
            seller_address = seller_info['address']

            # Buyer info
            buyer_info = json_dump['asset_events'][i]['winner_account']
            if (buyer_info['user'] == None):
                buyer_username = 'None'
            else:
                buyer_username = buyer_info['user']['username']
            buyer_address = buyer_info['address']

            payment_info = json_dump['asset_events'][i]['payment_token']
            payment_token = payment_info['symbol']

            sale_id = json_dump['asset_events'][i]['id']
            sale_price = int(json_dump['asset_events'][i]['total_price']) / 1000000000000000000
           # floor_price = self.getFloorPrice()

            json_info = {
                'asset_info': {
                    'asset_name': punk_name,
                    'asset_image': image_url,
                    'asset_link': product_link,
                },
                'seller_info': {
                    'seller_username': seller_username,
                    'seller_address': seller_address
                },
                'buyer_info': {
                    'buyer_username': buyer_username,
                    'buyer_address': buyer_address
                },
                'payment_token': payment_token,
                'sale_price': sale_price,
                'sale_id': sale_id,
              #  'floor_price': floor_price
            }
            json_list.append(json_info)
            #print(f'Sale Info: {json_info}')
        return json_list

    def sendWebhook(self, sale_json):
        discord_webhook = ''  # Enter the discord webhook

        asset_info = sale_json['asset_info']
        seller_info = sale_json['seller_info']
        buyer_info = sale_json['buyer_info']
        payment_token = sale_json['payment_token']
        sale_price = sale_json['sale_price']

        json_info = json.dumps(
            {
                'embeds': [
                    {
                        'title': f"{asset_info['asset_name']} was purchased!",
                        'url': asset_info['asset_link'],
                        'fields': [
                            {
                                'name': '**Sale price**',
                                'value': f'{sale_price} {payment_token}',
                                'inline': 'false'
                            },
                            {
                                'name': '**Buyer**',
                                'value': f"[{buyer_info['buyer_username']}](https://opensea.io/{buyer_info['buyer_address']})",
                                'inline': 'true'
                            },
                            {
                                'name': '**Seller**',
                                'value': f"[{seller_info['seller_username']}](https://opensea.io/{seller_info['seller_address']})",
                                'inline': 'true'
                            }
                        ],
                        'image': {
                            'url': asset_info['asset_image']
                        },
                        'footer': {
                            'text': f'The Currency',  # Change this to your projects name or set as variable
                        #    'icon_url': 'https://assets.stickpng.com/images/580b57fbd9996e24bc43bdf6.png'
                            # Change this to your projects logo
                        }
                    }
                ]
            }
        )
        # requests.post(discord_webhook, data=json_info, headers={"Content-Type": "application/json"})
        #Print for debugging/local env use
        print(f'Sale Info: {json_info}')

    def runInstance(self):
        old_sale_list = self.requestLastSales()
        old_sale_id = []

        for i in range(self.asset_range):
            old_sale_id.append(old_sale_list[i]['sale_id'])

        while (True):
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            new_sales = []

            try:
                new_sales_list = self.requestLastSales()
                new_sale_id = []

                for i in range(self.asset_range):
                    new_sale_id.append(new_sales_list[i]['sale_id'])

            except Exception as e:
                new_sales_list = old_sale_list
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S")
                print(f'[{current_time}] Error - {e}')

            new_sales = list(set(new_sale_id) - set(old_sale_id))

            if new_sales != []:

                for i in range(len(new_sales)):
                    print(f"[{current_time}] New  sale! - {new_sales[i]}")

                    for j in range(len(new_sales_list)):
                        if new_sales_list[j]['sale_id'] == new_sales[i]:

                            # Data for tweet
                            asset_name = new_sales_list[j]['asset_info']['asset_name']
                            asset_link = new_sales_list[j]['asset_info']['asset_link']
                            sale_price = new_sales_list[j]['sale_price']
                            payment_token = new_sales_list[j]['payment_token']

                            sale_data = [asset_name, asset_link, sale_price, payment_token]

                            try:
                                self.sendWebhook(new_sales_list[j])
                                print(f'Sale Short: {sale_data}')
                            except Exception as e:
                                print(f'Error: {e}')

            else:
                print(f'[{current_time}] No new sales!')

            old_sale_id = new_sale_id
            old_sale_list = new_sales_list

            time.sleep(30)  # Delay for requesting the opensea api

bot = openseaSalesBot()
bot.runInstance()