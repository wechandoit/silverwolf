from flask import Flask

from dotenv import load_dotenv
import os
load_dotenv()

from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SUPABASE_DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db.init_app(app)

import routes