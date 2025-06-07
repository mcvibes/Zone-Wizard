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

# Configure the database
database_url = os.environ.get("DATABASE_URL")
# Ensure PostgreSQL URI compatibility
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Strava API settings
app.config["STRAVA_CLIENT_ID"] = os.environ.get("STRAVA_CLIENT_ID")
app.config["STRAVA_CLIENT_SECRET"] = os.environ.get("STRAVA_CLIENT_SECRET")
# Set the redirect URI for Strava
import urllib.parse

# HARDCODED: Always use the production domain for Strava callback
# This ensures consistency between development and production
production_domain = "zone-wizard-malcolmmcdonal1.replit.app"
replit_domain = production_domain

# Keep this logging just for debugging
print(f"Using hard-coded domain: {replit_domain}")
print(f"Is deployed: {os.environ.get('REPL_DEPLOYMENT_ID') is not None}")

# Build and URL-encode the callback URI
callback_path = "/callback"
full_callback_url = f"https://{replit_domain}{callback_path}"
app.config["STRAVA_REDIRECT_URI"] = full_callback_url
print(f"Using Replit domain: {replit_domain}")
print(f"Full callback URL: {full_callback_url}")
print(f"For Strava settings, use domain: {replit_domain} (without https:// or /callback)")

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

# Print the Strava redirect URI for reference
print(f"Strava redirect URI: {app.config['STRAVA_REDIRECT_URI']}")
