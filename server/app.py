from flask import Flask
from flask_caching import Cache

from dotenv import load_dotenv
import os
load_dotenv()

from models import db

config = {
    'DEBUG': True,          # some Flask specific configs
    'CACHE_TYPE': 'SimpleCache',  # Flask-Caching related configs
    'CACHE_DEFAULT_TIMEOUT': 300,
    'SQLALCHEMY_DATABASE_URI': os.getenv('SUPABASE_DB_URI'),
    'SQLALCHEMY_TRACK_MODIFICATIONS': True
}

app = Flask(__name__)
app.config.from_mapping(config)
cache = Cache(app)

db.init_app(app)

import routes