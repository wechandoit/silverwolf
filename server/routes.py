from app import app, cache
from sqlalchemy import select, desc
from models import db, Valorant_Player, MMR_History, Competitive_Match, Competitive_Match_Kill, Competitive_Match_Player
from flask import request

import val

'''
The goal of v2 is to move all updating to a separate instance/program to completely reduce overhead and to provide information better
- Reduce verbose player call by simplifying our logic (instead of splitting it up to identifier and info, we just combine it and store in one table)
- Instead of having to create updaters we can just cache returned data until it can potentially update (5 minute simple cache, move to redis in future)
'''

@app.route('/')
def hello_world():
    return '<p>Hello, World!</p>'

@app.route('/users')
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

@app.route('/users/<name>/<tag>')
@cache.cached(timeout=300)
async def get_player_by_username_v2(name, tag):
    query = select(Valorant_Player).where(
        Valorant_Player.name == name,
        Valorant_Player.tag == tag
    )
    existing_player = db.session.execute(query).scalar_one_or_none()

    if existing_player:
        player_info = await val.get_verbose_player_stats(existing_player.puuid)

        existing_player.name = player_info['name']
        existing_player.tag = player_info['tag']
        existing_player.region = player_info['region']
        existing_player.account_level = player_info['account_level']
        existing_player.title = player_info['title']
        existing_player.card = player_info['card']

        db.session.commit()

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
        if player_info:
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
        else:
            return {
                'error': f'<p>{name}#{tag} is not a valid player</p>'
            }, 404

@app.route('/by-puuid/users/<puuid>')
@cache.cached(timeout=300)
async def get_player_by_puuid_v2(puuid):
    query = select(Valorant_Player).where(
        Valorant_Player.puuid == puuid
    )

    existing_player = db.session.execute(query).scalar_one_or_none()
    if existing_player:
        player_info = await val.get_verbose_player_stats(existing_player.puuid)

        existing_player.name = player_info['name']
        existing_player.tag = player_info['tag']
        existing_player.region = player_info['region']
        existing_player.account_level = player_info['account_level']
        existing_player.title = player_info['title']
        existing_player.card = player_info['card']

        db.session.commit()

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
        if player_info:
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
        else:
            return {
                'error': f'<p>{puuid} is not a valid player</p>'
            }, 404

@app.route('/by-puuid/mmr-history/<puuid>')
@cache.cached(timeout=300)
async def get_mmr_history_puuid_v2(puuid):
    is_player_in_basic_table_query = select(Valorant_Player).where(
        Valorant_Player.puuid == puuid
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return {'error': f'<p>{puuid} is not in the db yet!</p>'}, 404
    else:
        mmr_history = await val.get_player_comp_mmr_history_by_puuid(existing_player.region, puuid)

        if mmr_history is None:
            return {'error': f'<p>{puuid} does not have a mmr history</p>'}, 404
        
        matches_added = 0
        for match in mmr_history:
            is_match_in_history_table_query = select(MMR_History).where(
                MMR_History.puuid == puuid,
                MMR_History.match_id == match['match_id']
            )

            existing_match = db.session.execute(is_match_in_history_table_query).scalar_one_or_none()
            if existing_match == None:
                player_match = MMR_History(
                    match_id = match['match_id'],
                    puuid = puuid,
                    mmr_change = match['mmr_change'], 
                    refunded_rr = match['refunded_rr'],
                    was_derank_protected= match['was_derank_protected'],
                    map = match['map'],
                    account_rank = match['account_rank'], 
                    account_rr = match['account_rr'],
                    account_rank_img = match['account_rank_img'],
                    date = match['date']
                )
                db.session.add(player_match)
                matches_added += 1
        
        db.session.commit()

    matches_list = MMR_History.query.filter_by(puuid=puuid).order_by(desc(MMR_History.date)).all()
    print(f'Added {matches_added} matches to the db')
    return {
        'matches': [
            {
                'match_id': match.match_id,
                'mmr_change': match.mmr_change,
                'refunded_rr': match.refunded_rr,
                'was_derank_protected': match.was_derank_protected,
                'map': match.map,
                'account_rank': match.account_rank,
                'account_rr': match.account_rr,
                'account_rank_img': match.account_rank_img,
                'date': match.date
            } for match in matches_list
        ]
    }

@app.route('/mmr-history/<name>/<tag>')
@cache.cached(timeout=300)
async def get_mmr_history_username_v2(name, tag):
    is_player_in_basic_table_query = select(Valorant_Player).where(
        Valorant_Player.name == name,
        Valorant_Player.tag == tag
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return {'error': f'<p>{name}#{tag} is not in the db yet!</p>'}, 404
    else:
        mmr_history = await val.get_player_comp_mmr_history_by_username(existing_player.region, existing_player.name, existing_player.tag)

        if mmr_history is None:
            return {'error': f'<p>{name}#{tag} does not have a mmr history</p>'}, 404
        
        matches_added = 0
        for match in mmr_history:
            is_match_in_history_table_query = select(MMR_History).where(
                MMR_History.puuid == existing_player.puuid,
                MMR_History.match_id == match['match_id']
            )

            existing_match = db.session.execute(is_match_in_history_table_query).scalar_one_or_none()
            if existing_match == None:
                player_match = MMR_History(
                    match_id = match['match_id'],
                    puuid = existing_player.puuid,
                    mmr_change = match['mmr_change'], 
                    refunded_rr = match['refunded_rr'],
                    was_derank_protected= match['was_derank_protected'],
                    map = match['map'],
                    account_rank = match['account_rank'], 
                    account_rr = match['account_rr'],
                    account_rank_img = match['account_rank_img'],
                    date = match['date']
                )
                db.session.add(player_match)
                matches_added += 1
        
        db.session.commit()

    matches_list = MMR_History.query.filter_by(puuid=existing_player.puuid).order_by(desc(MMR_History.date)).all()
    print(f'Added {matches_added} matches to the db')
    return {
        'matches': [
            {
                'match_id': match.match_id,
                'mmr_change': match.mmr_change,
                'refunded_rr': match.refunded_rr,
                'was_derank_protected': match.was_derank_protected,
                'map': match.map,
                'account_rank': match.account_rank,
                'account_rr': match.account_rr,
                'account_rank_img': match.account_rank_img,
                'date': match.date
            } for match in matches_list
        ]
    }

@app.route('/mmr-history')
async def get_full_mmr_history_v2():
    mmr_history = MMR_History.query.order_by(desc(MMR_History.date)).all()
    return {
        'matches': [
            {
                'match_id': match.match_id,
                'mmr_change': match.mmr_change,
                'refunded_rr': match.refunded_rr,
                'was_derank_protected': match.was_derank_protected,
                'map': match.map,
                'puuid': match.puuid,
                'account_rank': match.account_rank,
                'account_rr': match.account_rr,
                'account_rank_img': match.account_rank_img,
                'date': match.date
            } for match in mmr_history
        ]
    }

@app.route('/match/<region>/<match_id>')
@cache.cached(timeout=300)
async def get_match_info_v2(region, match_id):
    is_match_in_db_query = select(Competitive_Match).where(
        Competitive_Match.region == region.upper(),
        Competitive_Match.match_id == match_id
    )

    existing_match = db.session.execute(is_match_in_db_query).scalar_one_or_none()

    if existing_match is None:
        full_match_info = await val.get_match_info(region, match_id)
        if full_match_info is None:
            return {'error': f'<p>Cannot retrieve info for match: {match_id}...</p>'}, 404
        else:
            new_match = Competitive_Match(
                match_id = full_match_info['match_id'],
                map = full_match_info['map'],
                game_length = full_match_info['game_length'],
                game_start = full_match_info['game_start'],
                region = full_match_info['region'],
                server = full_match_info['server'],
                blue_score = full_match_info.get('blue_score', 0),
                red_score = full_match_info.get('red_score', 0),
                who_won = full_match_info['who_won']
            )
            db.session.add(new_match)
            db.session.flush()

            for player_info in full_match_info['match_players']:
                player = Competitive_Match_Player(
                    match_id = new_match.id,
                    puuid = player_info['puuid'],
                    name = player_info['name'],
                    tag = player_info['tag'],
                    agent = player_info['agent'],
                    team = player_info['team'],
                    party_id = player_info['party_id'],
                    score = player_info['score'],
                    kills = player_info['kills'],
                    deaths = player_info['deaths'],
                    assists = player_info['assists'],
                    headshots = player_info['headshots'],
                    bodyshots = player_info['bodyshots'],
                    legshots = player_info['legshots'],
                    damage_dealt = player_info['damage_dealt'],
                    damage_received = player_info['damage_received'],
                    c_ability = player_info['c_ability'],
                    e_ability = player_info['e_ability'],
                    q_ability = player_info['q_ability'],
                    x_ability = player_info['x_ability']
                )
                db.session.add(player)
            
            for kill_info in full_match_info['match_kills']:
                kill = Competitive_Match_Kill(
                    match_id = new_match.id,
                    time_in_round = kill_info['time_in_round'],
                    round = kill_info['round'],
                    killer_puuid = kill_info['killer_puuid'],
                    victim_puuid = kill_info['victim_puuid'],
                    killer_x = kill_info['killer_x'],
                    killer_y = kill_info['killer_y'],
                    victim_x = kill_info['victim_x'],
                    victim_y = kill_info['victim_y'],
                    killer_view = kill_info['killer_view'],
                    weapon_id = kill_info['weapon_id'],
                    assistants = kill_info.get('assistants', [])
                )
                db.session.add(kill)
            db.session.commit()

            return full_match_info
    else:
        full_match_info = {
            'match_id': existing_match.match_id,
            'map': existing_match.map,
            'game_length': existing_match.game_length,
            'game_start': existing_match.game_start,
            'region': existing_match.region,
            'server': existing_match.server,
            'blue_score': existing_match.blue_score,
            'red_score': existing_match.red_score,
            'who_won': existing_match.who_won
        }

        match_players = [
            {
                'puuid': player.puuid, 
                'name': player.name, 
                'tag': player.tag, 
                'agent': player.agent, 
                'party_id': player.party_id, 
                'team': player.team,
                'score': player.score, 
                'kills': player.kills, 
                'deaths': player.deaths, 
                'assists': player.assists,
                'headshots': player.headshots, 
                'bodyshots': player.bodyshots, 
                'legshots': player.legshots,
                'damage_dealt': player.damage_dealt, 
                'damage_received': player.damage_received,
                'c_ability': player.c_ability, 
                'e_ability': player.e_ability, 
                'q_ability': player.q_ability, 
                'x_ability': player.x_ability
            } for player in existing_match.match_players
        ]

        match_kills = [
            {
                'match_id': kill.match_id,
                'time_in_round': kill.time_in_round,
                'round': kill.round,
                'killer_puuid': kill.killer_puuid,
                'victim_puuid': kill.victim_puuid,
                'killer_x': kill.killer_x,
                'killer_y': kill.killer_y,
                'victim_x': kill.victim_x,
                'victim_y': kill.victim_y,
                'killer_view': kill.killer_view,
                'weapon_id': kill.weapon_id,
                'assistants': list(kill.assistants) if hasattr(kill, 'assistants') else []
            } for kill in existing_match.match_kills
        ]

        full_match_info['match_players'] = match_players
        full_match_info['match_kills'] = match_kills

        return full_match_info

@app.route('/by-puuid/match-history/<puuid>')
@cache.cached(timeout=300)
async def get_match_history_puuid_v2(puuid):
    is_player_in_basic_table_query = select(Valorant_Player).where(
        Valorant_Player.puuid == puuid
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return {'error': f'<p>{puuid} is not in the db yet!</p>'}, 404
    else:
        
        map_filter = request.args.get('map')

        matches_list = (
            db.session.query(Competitive_Match)
            .join(Competitive_Match_Player)
            .filter(Competitive_Match_Player.puuid == puuid)
        )

        if map_filter:
            matches_list = matches_list.filter(Competitive_Match.map == map_filter)

        matches_list = matches_list.order_by(desc(Competitive_Match.game_start)).all()

        matches_return_list = []
        for existing_match in matches_list:
            full_match_info = {
                'match_id': existing_match.match_id,
                'map': existing_match.map,
                'game_length': existing_match.game_length,
                'game_start': existing_match.game_start,
                'region': existing_match.region,
                'server': existing_match.server,
                'blue_score': existing_match.blue_score,
                'red_score': existing_match.red_score,
                'who_won': existing_match.who_won
            }

            match_players = [
                {
                    'puuid': player.puuid, 
                    'name': player.name, 
                    'tag': player.tag, 
                    'agent': player.agent, 
                    'party_id': player.party_id, 
                    'team': player.team,
                    'score': player.score, 
                    'kills': player.kills, 
                    'deaths': player.deaths, 
                    'assists': player.assists,
                    'headshots': player.headshots, 
                    'bodyshots': player.bodyshots, 
                    'legshots': player.legshots,
                    'damage_dealt': player.damage_dealt, 
                    'damage_received': player.damage_received,
                    'c_ability': player.c_ability, 
                    'e_ability': player.e_ability, 
                    'q_ability': player.q_ability, 
                    'x_ability': player.x_ability
                } for player in existing_match.match_players
            ]

            match_kills = [
                {
                    'match_id': kill.match_id,
                    'time_in_round': kill.time_in_round,
                    'round': kill.round,
                    'killer_puuid': kill.killer_puuid,
                    'victim_puuid': kill.victim_puuid,
                    'killer_x': kill.killer_x,
                    'killer_y': kill.killer_y,
                    'victim_x': kill.victim_x,
                    'victim_y': kill.victim_y,
                    'killer_view': kill.killer_view,
                    'weapon_id': kill.weapon_id,
                    'assistants': list(kill.assistants) if hasattr(kill, 'assistants') else []
                } for kill in existing_match.match_kills
            ]

            full_match_info['match_players'] = match_players
            full_match_info['match_kills'] = match_kills
            matches_return_list.append(full_match_info)

        return {'matches': matches_return_list}
    
@app.route('/match-history/<name>/<tag>')
@cache.cached(timeout=300)
async def get_match_history_username_v2(name, tag):
    is_player_in_basic_table_query = select(Valorant_Player).where(
        Valorant_Player.name == name,
        Valorant_Player.tag == tag
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return {'error': f'<p>{name}#{tag} is not in the db yet!</p>'}, 404
    else:
        
        map_filter = request.args.get('map')

        matches_list = (
            db.session.query(Competitive_Match)
            .join(Competitive_Match_Player)
            .filter(Competitive_Match_Player.puuid == existing_player.puuid)
        )

        if map_filter:
            matches_list = matches_list.filter(Competitive_Match.map == map_filter)

        matches_list = matches_list.order_by(desc(Competitive_Match.game_start)).all()

        matches_return_list = []
        for existing_match in matches_list:
            full_match_info = {
                'match_id': existing_match.match_id,
                'map': existing_match.map,
                'game_length': existing_match.game_length,
                'game_start': existing_match.game_start,
                'region': existing_match.region,
                'server': existing_match.server,
                'blue_score': existing_match.blue_score,
                'red_score': existing_match.red_score,
                'who_won': existing_match.who_won
            }

            match_players = [
                {
                    'puuid': player.puuid, 
                    'name': player.name, 
                    'tag': player.tag, 
                    'agent': player.agent, 
                    'party_id': player.party_id, 
                    'team': player.team,
                    'score': player.score, 
                    'kills': player.kills, 
                    'deaths': player.deaths, 
                    'assists': player.assists,
                    'headshots': player.headshots, 
                    'bodyshots': player.bodyshots, 
                    'legshots': player.legshots,
                    'damage_dealt': player.damage_dealt, 
                    'damage_received': player.damage_received,
                    'c_ability': player.c_ability, 
                    'e_ability': player.e_ability, 
                    'q_ability': player.q_ability, 
                    'x_ability': player.x_ability
                } for player in existing_match.match_players
            ]

            match_kills = [
                {
                    'match_id': kill.match_id,
                    'time_in_round': kill.time_in_round,
                    'round': kill.round,
                    'killer_puuid': kill.killer_puuid,
                    'victim_puuid': kill.victim_puuid,
                    'killer_x': kill.killer_x,
                    'killer_y': kill.killer_y,
                    'victim_x': kill.victim_x,
                    'victim_y': kill.victim_y,
                    'killer_view': kill.killer_view,
                    'weapon_id': kill.weapon_id,
                    'assistants': list(kill.assistants) if hasattr(kill, 'assistants') else []
                } for kill in existing_match.match_kills
            ]

            full_match_info['match_players'] = match_players
            full_match_info['match_kills'] = match_kills
            matches_return_list.append(full_match_info)

        return {'matches': matches_return_list}