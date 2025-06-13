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

                    time = convert_datetime_string_to_unix(match['date'])
                    match_info.append({'match_id': match['match_id'], 'mmr_change': int(match['last_change']), 'map': match['map']['name'],
                                       'refunded_rr': match['refunded_rr'], 'was_derank_protected': int(match['was_derank_protected']),
                                       'account_rank': match['tier']['name'], 'account_rr': int(match['rr']), 'account_rank_img': await get_rank_img(int(match['tier']['id'])),
                                       'date': time})
                return match_info

# Get the rank image from the rank id (add error checking later)

async def get_rank_img(id:int):
    if id < 0 or id > 27: return None # ids must be 0-27
    async with request('GET', f'https://valorant-api.com/v1/competitivetiers') as response:
        if response.status == 200:
            data = await response.json()
            tiers_list = data['data'][4]['tiers']
            return tiers_list[id]['largeIcon']
        
# Convert datetime string (ISO format) to unix

def convert_datetime_string_to_unix(date_str):
    if date_str.endswith('Z'):
        date_str = date_str[:-1]
    dt = datetime.datetime.fromisoformat(date_str)
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp())

async def get_match_info(region, puuid):
    match_url = f'https://api.henrikdev.xyz/valorant/v4/match/{region}/{puuid}'
    async with request('GET', match_url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            data = data['data']

            metadata = data['metadata']
            full_match_info = {'match_id': metadata['match_id'], 'map': metadata['map']['name'], 
                               'game_length': int(metadata['game_length_in_ms']), 'game_start': convert_datetime_string_to_unix(metadata['started_at']),
                               'region': str(metadata['region']).upper(), 'server': metadata['cluster']}
            
            # get who won and how many rounds each team won

            who_won = ''
            for team in data['teams']:
                if team['team_id'] == 'Red':
                    full_match_info['red_score'] = team['rounds']['won']
                    if team['won'] == True:
                        who_won = 'red'
                elif team['team_id'] == 'Blue':
                    full_match_info['blue_score'] = team['rounds']['won']
                    if team['won'] == True:
                        who_won = 'blue'
            
            if who_won == '':
                who_won = 'tie'
            
            full_match_info['who_won'] = who_won

            # player stats

            player_stats = []
            for player in data['players']:
                stats = player['stats']
                casts = player['ability_casts']
                player_stats.append({'puuid': player['puuid'], 'agent': player['agent']['name'], 'party_id': player['party_id'], 'team': str(player['team_id']).lower(),
                                     'name': player['name'], 'tag': player['tag'],
                                     'score': stats['score'], 'kills': stats['kills'], 'deaths': stats['deaths'], 'assists': stats['assists'],
                                     'headshots': stats['headshots'], 'bodyshots': stats['bodyshots'], 'legshots': stats['legshots'],
                                     'damage_dealt': stats['damage']['dealt'], 'damage_received': stats['damage']['received'],
                                     'c_ability': casts['ability1'], 'e_ability': casts['grenade'], 'q_ability': casts['ability2'], 'x_ability': casts['ultimate']})
            
            full_match_info['match_players'] = player_stats

            # kill stats

            kill_stats = []
            for kill in data['kills']:
                kill_dict = {'time_in_round': kill['time_in_round_in_ms'], 'round': kill['round'], 'killer_puuid': kill['killer']['puuid'], 'victim_puuid': kill['victim']['puuid'],
                             'victim_x': kill['location']['x'], 'victim_y': kill['location']['y'], 'weapon_id': kill['weapon']['id']}
                
                # get killer player location from player_locations list
                for player in kill['player_locations']:
                    if player['player']['puuid'] == kill_dict['killer_puuid']:
                        kill_dict['killer_x'] = player['location']['x']
                        kill_dict['killer_y'] = player['location']['y']
                        kill_dict['killer_view'] = player['view_radians']
                
                # if player died to themself, killer died before this, etc.
                if not ('killer_x' in kill_dict):
                    if kill_dict['killer_puuid'] == kill_dict['victim_puuid']:
                        kill_dict['killer_x'] = kill_dict['victim_x']
                        kill_dict['killer_y'] = kill_dict['victim_y']
                    else:
                        kill_dict['killer_x'] = -100000
                        kill_dict['killer_y'] = -100000
                    kill_dict['killer_view'] = -1

                # get assistant puuids
                assistants = []
                for assistant in kill['assistants']:
                    assistants.append(assistant['puuid'])
                
                kill_dict['assistants'] = assistants
                
                kill_stats.append(kill_dict)

            full_match_info['match_kills'] = kill_stats

            return full_match_info
        else:
            return None