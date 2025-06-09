from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ARRAY, select, desc
from sqlalchemy.orm import Mapped, mapped_column
import val

db = SQLAlchemy()
app = Flask(__name__)
db_name = 'val_stats.db'
db_type = 'sqlite'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_name
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)

class Player(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    puuid: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]
    tag: Mapped[str]
    region: Mapped[str]

class Verbose_Player(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    puuid: Mapped[str] = mapped_column(unique=True)
    account_level: Mapped[int] = mapped_column(default=0)
    card: Mapped[str]
    title: Mapped[str]

class MMR_History(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[str]
    puuid: Mapped[str]
    mmr_change: Mapped[int]
    map: Mapped[str]
    account_rank: Mapped[str]
    account_rr: Mapped[int]
    account_rank_img: Mapped[str]
    date: Mapped[int]

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
async def get_mmr_history(puuid):
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
                "map": match.map,
                "account_rank": match.account_rank,
                "account_rr": match.account_rr,
                "account_rank_img": match.account_rank_img,
                "date": match.date
            } for match in matches_list
        ]
    }
