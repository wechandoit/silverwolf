from flask import request
from sqlalchemy import select, desc
from models import db, Player, Verbose_Player, MMR_History, Competitive_Match, Competitive_Match_Kill, Competitive_Match_Player
from app import app
import val

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/users")
def get_all_users():
    player_list = Player.query.all()
    return {
        "players": [
            {
                "name": player.name,
                "tag": player.tag,
                "puuid": player.puuid,
                "region": player.region
            } for player in player_list
        ]
    }

@app.route("/users/<name>/<tag>")
async def get_player_stats(name, tag):
    query = select(Player).where(
        Player.name == name,
        Player.tag == tag
    )
    existing_player = db.session.execute(query).scalar_one_or_none()

    if existing_player is None:
        player_info = await val.get_player_stats(name, tag)
        new_player = Player(
            name=player_info['name'],
            tag=player_info['tag'],
            puuid=player_info['puuid'],
            region=player_info['region']
        )
        db.session.add(new_player)
        db.session.commit()
        return player_info
    else:
        return {
            'name': existing_player.name,
            'tag': existing_player.tag,
            'puuid': existing_player.puuid,
            'region': existing_player.region
        }

@app.route("/by-puuid/<puuid>")
async def get_verbose_player_stats(puuid):
    is_player_in_basic_table_query = select(Player).where(
        Player.puuid == puuid
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return f'<p>{puuid} not in the database</p>'
    else:
        is_player_in_verbose_table_query = select(Verbose_Player).where(
            Verbose_Player.puuid == puuid
        )

        existing_verbose_player = db.session.execute(is_player_in_verbose_table_query).scalar_one_or_none()
        if existing_verbose_player is None:
            player_info = await val.get_verbose_player_stats(puuid)

            if player_info is None:
                return f'<p>{puuid} does not have verbose stats</p>'

            new_player = Verbose_Player(
                puuid=player_info['puuid'],
                account_level=player_info['account_level'],
                card=player_info['card'],
                title=player_info['title']
            )
            db.session.add(new_player)
            db.session.commit()
            return {
                'name': existing_player.name,
                'tag': existing_player.tag,
                'puuid': player_info['puuid'],
                'account_level': player_info['account_level'],
                'card': val.get_player_card(player_info['card']!=None, player_info['card']),
                'title': await val.get_title(player_info['title']!=None, player_info['title']),
                'region': player_info['region']
            }
        else:
            return {
                'name': existing_player.name,
                'tag': existing_player.tag,
                'puuid': existing_verbose_player.puuid,
                'account_level': existing_verbose_player.account_level,
                'card': val.get_player_card(existing_verbose_player.card!=None, existing_verbose_player.card),
                'title': await val.get_title(existing_verbose_player.title!=None, existing_verbose_player.title),
                'region': existing_player.region
            }
        
@app.route("/mmr-history/<puuid>")
async def get_puuid_mmr_history(puuid):
    is_player_in_basic_table_query = select(Player).where(
        Player.puuid == puuid
    )

    existing_player = db.session.execute(is_player_in_basic_table_query).scalar_one_or_none()
    if existing_player is None:
        return f'<p>{puuid} is not in the db yet!</p>'
    else:
        mmr_history = await val.get_player_comp_mmr_history(existing_player.region, puuid)

        if mmr_history is None:
            return f'<p>{puuid} does not have a mmr history</p>'
        
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
                db.session.commit()
                matches_added += 1

    matches_list = MMR_History.query.filter_by(puuid=puuid).order_by(desc(MMR_History.date)).all()
    print(f'Added {matches_added} matches to the db')
    return {
        "matches": [
            {
                "match_id": match.match_id,
                "mmr_change": match.mmr_change,
                "refunded_rr": match.refunded_rr,
                "was_derank_protected": match.was_derank_protected,
                "map": match.map,
                "account_rank": match.account_rank,
                "account_rr": match.account_rr,
                "account_rank_img": match.account_rank_img,
                "date": match.date
            } for match in matches_list
        ]
    }

@app.route("/mmr-history")
async def get_full_mmr_history():
    mmr_history = MMR_History.query.order_by(desc(MMR_History.date)).all()
    return {
        "matches": [
            {
                "match_id": match.match_id,
                "mmr_change": match.mmr_change,
                "refunded_rr": match.refunded_rr,
                "was_derank_protected": match.was_derank_protected,
                "map": match.map,
                "puuid": match.puuid,
                "account_rank": match.account_rank,
                "account_rr": match.account_rr,
                "account_rank_img": match.account_rank_img,
                "date": match.date
            } for match in mmr_history
        ]
    }

@app.route("/match/<region>/<match_id>")
async def get_match_info(region, match_id):
    is_match_in_db_query = select(Competitive_Match).where(
        Competitive_Match.region == region.upper(),
        Competitive_Match.match_id == match_id
    )

    existing_match = db.session.execute(is_match_in_db_query).scalar_one_or_none()

    if existing_match is None:
        full_match_info = await val.get_match_info(region, match_id)
        if full_match_info is None:
            return f'<p>Cannot retrieve info for match: {match_id}...</p>'
        else:
            new_match = Competitive_Match(
                match_id = full_match_info["match_id"],
                map = full_match_info["map"],
                game_length = full_match_info["game_length"],
                game_start = full_match_info["game_start"],
                region = full_match_info["region"],
                server = full_match_info["server"],
                blue_score = full_match_info.get("blue_score", 0),
                red_score = full_match_info.get("red_score", 0),
                who_won = full_match_info['who_won']
            )
            db.session.add(new_match)
            db.session.flush()

            for player_info in full_match_info['match_players']:
                player = Competitive_Match_Player(
                    match_id = new_match.id,
                    puuid = player_info["puuid"],
                    agent = player_info["agent"],
                    team = player_info["team"],
                    party_id = player_info['party_id'],
                    score = player_info["score"],
                    kills = player_info["kills"],
                    deaths = player_info["deaths"],
                    assists = player_info["assists"],
                    headshots = player_info["headshots"],
                    bodyshots = player_info["bodyshots"],
                    legshots = player_info["legshots"],
                    damage_dealt = player_info["damage_dealt"],
                    damage_received = player_info["damage_received"],
                    c_ability = player_info["c_ability"],
                    e_ability = player_info["e_ability"],
                    q_ability = player_info["q_ability"],
                    x_ability = player_info["x_ability"]
                )
                db.session.add(player)
            
            for kill_info in full_match_info['match_kills']:
                kill = Competitive_Match_Kill(
                    match_id = new_match.id,
                    time_in_round = kill_info["time_in_round"],
                    round = kill_info["round"],
                    killer_puuid = kill_info["killer_puuid"],
                    victim_puuid = kill_info["victim_puuid"],
                    killer_x = kill_info["killer_x"],
                    killer_y = kill_info["killer_y"],
                    victim_x = kill_info["victim_x"],
                    victim_y = kill_info["victim_y"],
                    killer_view = kill_info['killer_view'],
                    weapon_id = kill_info['weapon_id'],
                    assistants = kill_info.get("assistants", [])
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
                'assistants': list(kill.assistants) if hasattr(kill, "assistants") else []
            } for kill in existing_match.match_kills
        ]

        full_match_info['match_players'] = match_players
        full_match_info['match_kills'] = match_kills

        return full_match_info
        