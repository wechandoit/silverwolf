import os
from dotenv import load_dotenv
load_dotenv()

from aiohttp import request

API_KEY = os.getenv("VAL_API_KEY_UPDATER")

headers = {
    "Accept": "application/json",
    "Authorization": f"{API_KEY}"
}

async def get_player_stats(name, tag):
    account_data_url = f'https://api.henrikdev.xyz/valorant/v2/account/{name}/{tag}?force=true'
    async with request('GET', account_data_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']
            
            player_info = {'name': data['name'], 'tag': data['tag'], 'puuid': data['puuid']}
            return player_info

        else:
            return f'Error fetching player stats | {response.status}: {response.reason}'
