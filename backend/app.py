from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String, select
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
            puuid=player_info['puuid']
        )
        db.session.add(new_player)
        db.session.commit()
        return player_info
    else:
        return {
            'name': existing_player.name,
            'tag': existing_player.tag,
            'puuid': existing_player.puuid
        }