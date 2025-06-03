from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, ARRAY, select
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

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/<name>/<tag>")
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
            new_player = Verbose_Player(
                puuid=player_info['puuid'],
                account_level=player_info['account_level'],
                card=player_info['card'],
                title=player_info['title']
            )
            db.session.add(new_player)
            db.session.commit()
            return {
                'puuid': player_info['puuid'],
                'account_level': player_info['account_level'],
                'card': val.get_player_card(player_info['card']!=None, player_info['card']),
                'title': await val.get_title(player_info['title']!=None, player_info['title'])
            }
        else:
            return {
                'puuid': existing_verbose_player.puuid,
                'account_level': existing_verbose_player.account_level,
                'card': val.get_player_card(existing_verbose_player.card!=None, existing_verbose_player.card),
                'title': await val.get_title(existing_verbose_player.title!=None, existing_verbose_player.title)
            }