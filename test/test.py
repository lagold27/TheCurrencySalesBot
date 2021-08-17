import datetime
import json
import requests
from pprint import pprint
import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
import difflib
from bs4 import BeautifulSoup

TOKEN = ""

client = commands.Bot(command_prefix="!")
slug_file = open("slugs.json", 'r+')
slugs = json.load(slug_file)


@client.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(client.latency * 1000)}ms")

@client.command()
async def info(ctx, slug=None, token=None):
    if slug is None:
        await ctx.reply("You didn't specify a collection name. Please try again.")
        return

    try:
        url = "https://api.opensea.io/api/v1/assets"
        querystring = {"order_direction": "desc", "collection": slug, "limit": "1", "offset": "0"}
        response = requests.request("GET", url, params=querystring)
        res = json.loads(response.text)

        address = res["assets"][0]["asset_contract"]["address"]

        if token is None:
            token_id = res["assets"][0]["token_id"]
            url2 = f"https://api.opensea.io/api/v1/asset/{address}/{token_id}/"
            response = requests.request("GET", url2)
            result = json.loads(response.text)

            collection = result["collection"]

            banner = collection["banner_image_url"]
            image = collection["image_url"]
            name = collection["name"]
            stats = collection["stats"]
            volume = '{0:.3f}'.format(stats["total_volume"])

            embed = discord.Embed(
                title=name,
                color=0x5076FF,
                url=f"https://opensea.io/collection/{slug}",
                timestamp=datetime.datetime.utcnow()
                )

            if banner is not None:
                embed.set_image(url=banner)
            if image is not None:
                embed.set_thumbnail(url=image)

            openseaUrl = f'https://opensea.io/assets/{slug}?search[sortAscending]=true&search[sortBy]=PRICE&search[toggles][0]=BUY_NOW'
            page = requests.get(openseaUrl)
            soup = BeautifulSoup(page.content, "html.parser")

            view = soup.find("div", {"class": "AssetsSearchView--assets"})
            footer = view.find("div", {"class": "AssetCardFooter--price"})
            fpa = footer.findChild("div", {"class": "AssetCardFooter--price-amount"})
            view = fpa.findChild("div", {"class": "Price--amount"})

            floor_prize = str(view.text)

            embed.add_field(name="Items: ", value=stats["count"])
            embed.add_field(name="Owners: ", value=stats["num_owners"])
            embed.add_field(name="Floor Price: ", value=floor_prize)
            embed.add_field(name="Volume Traded: ", value=volume)

            embed.set_footer(
                text="Bot",
                icon_url="https://media.discordapp.net/attachments/870015430025154601/870398895002370059/Logov2.png",
                )
            await ctx.reply(content=None, embed=embed, mention_author=False)

        else:
            url2 = f"https://api.opensea.io/api/v1/asset/{address}/{token}/"
            response = requests.request("GET", url2)
            result = json.loads(response.text)

            if response.status_code == 404:
                await ctx.reply("Your Token ID is wrong, Please try again.")
                return

            url3 = result["token_metadata"]
            req = requests.request("GET", url3)
            final = json.loads(req.text)

            if "name" not in final:
                name = result["collection"]["name"] + ' ' + token
            else:
                name = final["name"]

            image = final["image"]
            traits = final["attributes"]

            # name = result["collection"]["name"] + ' ' + result["name"]
            total = result["collection"]["stats"]["count"]
            owner = result["owner"]
            # image = result["image_original_url"]
            link = result["permalink"]
            # traits = result["traits"]

            # rank = str(str(token) + f" (out of {int(total)})")
            # rarity = 0

            embed = discord.Embed(
                title=name,
                color=0x5076FF,
                url=link,
                timestamp=datetime.datetime.utcnow()
                )

            if image is not None:
                if image[:7] == 'ipfs://':
                    image = 'https://gateway.pinata.cloud/ipfs/' + str(image[7:])
                # print(image[:7])
                # print(image)
                embed.set_image(url=image)

            if owner is not None:
                if owner["user"]["username"] is not None:
                    embed.add_field(name="Owned by",
                                    value=f"[{owner['user']['username']}](https://opensea.io/{owner['address']})",
                                    inline=False)
                else:
                    embed.add_field(name="Owned by",
                                    value=f"[unknown](https://opensea.io/{owner['address']})", inline=False)

            # embed.add_field(name="Rank", value=rank, inline=False)
            #
            # for trait in traits:
            #     rarity += (1 / (trait['trait_count'] / total))
            #
            # rarity_str = "{:.2f}".format(rarity)
            #
            # embed.add_field(name="Rarity Score: ", value=rarity_str, inline=False)

            for trait in traits:
                # rar = "{:.2f}".format(1 / (trait['trait_count'] / total))
                # per = "{:.2f}".format((trait['trait_count'] / total) * 100)

                # embed.add_field(name=trait['trait_type'], value=f"{trait['value']} \n ({rar}) \n ({per} %)", inline=True)
                embed.add_field(name=trait['trait_type'], value=trait['value'], inline=True)

            embed.set_footer(
                text="Bot",
                icon_url="https://media.discordapp.net/attachments/870015430025154601/870398895002370059/Logov2.png",
                )
            await ctx.reply(content=None, embed=embed, mention_author=False)

    except requests.exceptions.RequestException as e:
        print(f"Error - {e}")
        await ctx.reply(f"Internal request error. {e} \nPlease try later.")

    except Exception as e:
        print(f"Error - {e}")
        await ctx.send(f"Internal error - {e}")
        suggestions = difflib.get_close_matches(slug, slugs, n=5, cutoff=0.7)

        if len(list(suggestions)) > 0:
            i = 1
            desc = ''
            for sugg in suggestions:
                desc = desc + f' `{sugg}`, '
                i += 1

            embed = discord.Embed(
                title="Here are some suggestions: ",
                description=desc[:-2],
                color=0x5076FF,
                timestamp=datetime.datetime.utcnow()
                )
            embed.set_footer(
                text="Bot",
                icon_url="https://media.discordapp.net/attachments/870015430025154601/870398895002370059/Logov2.png",
                )

            await ctx.reply(content=f"No such collection {slug} exists", embed=embed, mention_author=False)
        else:
            await ctx.reply(content=f"No such collection {slug} exists", mention_author=False)

client.run(TOKEN)
