import os
from dotenv import load_dotenv
load_dotenv()

import datetime

from aiohttp import request

API_KEY = os.getenv("VAL_API_KEY")

headers = {
    "Accept": "application/json",
    "Authorization": f"{API_KEY}"
}

# Get basic player stats (name, tag, puuid, region)

async def get_player_stats(name, tag):
    account_data_url = f'https://api.henrikdev.xyz/valorant/v2/account/{name}/{tag}?force=true'
    async with request('GET', account_data_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']
            
            player_info = {'name': data['name'], 'tag': data['tag'], 'puuid': data['puuid'], 'region': data['region'].upper()}
            return player_info

        else:
            return None

# Get verbose player stats (name, tag, puuid, region, account_level, card, title)

async def get_verbose_player_stats(puuid):
    account_data_url = f'https://api.henrikdev.xyz/valorant/v2/by-puuid/account/{puuid}?force=true'
    async with request('GET', account_data_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']
            
            player_info = {'name': data['name'], 'tag': data['tag'], 'puuid': data['puuid'], 'region': data['region'].upper(), 
                           'account_level': data['account_level'], 'card': data['card'], 'title': data['title']}
            return player_info

        else:
            return None

# Get the player's card (small/pfp) image if it exists

def get_player_card(has_card, card) -> str:
    if has_card:
        return f'https://media.valorant-api.com/playercards/{card}/smallart.png'
    else:
        return 'None'
    
# Get the player's title if it exists

async def get_title(has_title, title) -> str:
    if has_title:
        title_link_url = f'https://valorant-api.com/v1/playertitles/{title}'
        async with request('GET', title_link_url, headers={}) as response:
            if response.status == 200:
                data = await response.json()
                data = data['data']
                return data['titleText']
            else:
                return 'None'
    else:
        return 'None'

# Get the player's comp mmr history

async def get_player_comp_mmr_history(region, puuid):
    account_mmr_history_url = f'https://api.henrikdev.xyz/valorant/v2/by-puuid/mmr-history/{region}/pc/{puuid}'
    async with request('GET', account_mmr_history_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']['history']

            if len(data) < 1:
                return None
            else:
                match_info = []
                for match in data:

                    date_str = match['date']
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1]
                    dt = datetime.datetime.fromisoformat(date_str)
                    time = int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())

                    match_info.append({'match_id': match['match_id'], 'mmr_change': int(match['last_change']), 'map': match['map']['name'],
                                       'refunded_rr': match['refunded_rr'], 'was_derank_protected': int(match['was_derank_protected']),
                                       'account_rank': match['tier']['name'], 'account_rr': int(match['rr']), 'account_rank_img': await get_rank_img(int(match['tier']['id'])),
                                       'date': time})
                return match_info

# Get the rank image from the rank id (add error checking later)

async def get_rank_img(id:int):
    async with request('GET', f'https://valorant-api.com/v1/competitivetiers') as response:
        if response.status == 200:
            data = await response.json()
            tiers_list = data['data'][4]['tiers']
            return tiers_list[id]['largeIcon']