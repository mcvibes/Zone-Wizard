import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///strava_hr_zones.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Strava API settings
app.config["STRAVA_CLIENT_ID"] = os.environ.get("STRAVA_CLIENT_ID")
app.config["STRAVA_CLIENT_SECRET"] = os.environ.get("STRAVA_CLIENT_SECRET")
app.config["STRAVA_REDIRECT_URI"] = os.environ.get("STRAVA_REDIRECT_URI", "http://localhost:5000/callback")

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import the models here so their tables will be created
    import models  # noqa: F401
    
    db.create_all()

# Import and register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

# Import routes after app is created to avoid circular imports
import routes
