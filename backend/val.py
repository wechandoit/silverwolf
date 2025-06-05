import os
from dotenv import load_dotenv
load_dotenv()

from aiohttp import request

API_KEY = os.getenv("VAL_API_KEY_UPDATER")

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

# Get the player's comp mmr history (at most 10 matches)
async def get_player_comp_mmr_history(region, puuid):
    account_mmr_history_url = f'https://api.henrikdev.xyz/valorant/v1/by-puuid/mmr-history/{region}/{puuid}'
    async with request('GET', account_mmr_history_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']

            if len(data) < 1:
                return f'{puuid} has no recently logged ranked games'
            else:
                match_info = []
                for match in data[:10]:
                    match_info.append({'match_id': match['match_id'], 'mmr_change': int(match['mmr_change_to_last_game']), 'map': match['map']['name'],
                                       'account_rank': match['currenttierpatched'], 'account_rr': int(match['ranking_in_tier']), 'account_rank_img': match['images']['small'],
                                       'date': int(match['date_raw'])})
                return match_info