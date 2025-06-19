from app import app
from sqlalchemy import select
from models import db, Valorant_Player
from flask import request

import val

'''
The goal of v2 is to move all updating to a separate instance/program to completely reduce overhead and to provide information better
'''

# Reduce verbose player call by simplifying our logic (instead of splitting it up to identifier and info, we just combine it and store in one table)

@app.route("/v2/users")
def get_all_users_v2():
    player_list = Valorant_Player.query.all()
    count_only: bool = str(request.args.get('count_only')).lower() == 'true'
    if count_only:
        return {'data': {'total_users': Valorant_Player.query.count()}}
    else:
        return {
            'data':{
                'total_users': len(player_list),
                'players': [
                    {
                        'name': player.name,
                        'tag': player.tag,
                        'puuid': player.puuid,
                        'region': player.region
                    } for player in player_list
                ]
            }
        }

@app.route("/v2/users/<name>/<tag>")
async def get_player_by_username_v2(name, tag):
    query = select(Valorant_Player).where(
        Valorant_Player.name == name,
        Valorant_Player.tag == tag
    )
    existing_player = db.session.execute(query).scalar_one_or_none()

    if existing_player:
        return {
            'data': 
                {
                    'name': existing_player.name,
                    'tag': existing_player.tag,
                    'puuid': existing_player.puuid,
                    'region': existing_player.region,
                    'account_level': existing_player.account_level,
                    'card': val.get_player_card(existing_player.card!=None, existing_player.card),
                    'title': await val.get_title(existing_player.title!=None, existing_player.title)
                }
            }
    else:
        player_info = await val.get_player_stats(name, tag)
        new_player = Valorant_Player(
            name = player_info['name'],
            tag = player_info['tag'],
            puuid = player_info['puuid'],
            region = player_info['region'],
            account_level = player_info['account_level'],
            title = player_info['title'],
            card = player_info['card']
        )
        db.session.add(new_player)
        db.session.commit()
        return {
            'data': 
                {
                    'name': new_player.name,
                    'tag': new_player.tag,
                    'puuid': new_player.puuid,
                    'region': new_player.region,
                    'account_level': new_player.account_level,
                    'card': val.get_player_card(new_player.card!=None, new_player.card),
                    'title': await val.get_title(new_player.title!=None, new_player.title)
                }
            }
    
@app.route("/v2/by-puuid/<puuid>")
async def get_player_by_puuid_v2(puuid):
    query = select(Valorant_Player).where(
        Valorant_Player.puuid == puuid
    )

    existing_player = db.session.execute(query).scalar_one_or_none()
    if existing_player:
        return {
            'data': 
                {
                    'name': existing_player.name,
                    'tag': existing_player.tag,
                    'puuid': existing_player.puuid,
                    'region': existing_player.region,
                    'account_level': existing_player.account_level,
                    'card': val.get_player_card(existing_player.card!=None, existing_player.card),
                    'title': await val.get_title(existing_player.title!=None, existing_player.title)
                }
            }
    else:
        player_info = await val.get_verbose_player_stats(puuid)
        new_player = Valorant_Player(
            name = player_info['name'],
            tag = player_info['tag'],
            puuid = player_info['puuid'],
            region = player_info['region'],
            account_level = player_info['account_level'],
            title = player_info['title'],
            card = player_info['card']
        )
        db.session.add(new_player)
        db.session.commit()
        return {
            'data': 
                {
                    'name': new_player.name,
                    'tag': new_player.tag,
                    'puuid': new_player.puuid,
                    'region': new_player.region,
                    'account_level': new_player.account_level,
                    'card': val.get_player_card(existing_player.card!=None, existing_player.card),
                    'title': await val.get_title(existing_player.title!=None, existing_player.title)
                }
            }