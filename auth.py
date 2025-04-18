import os
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, redirect, url_for, session, flash, render_template
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import requests
from app import app, db
from models import User

# Set up LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# Set up Blueprint
auth_bp = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Generate Strava authorization URL
    client_id = app.config['STRAVA_CLIENT_ID']
    redirect_uri = app.config['STRAVA_REDIRECT_URI']
    if not client_id:
        flash('Strava client ID is not configured.', 'danger')
        return render_template('login.html', auth_url=None)
    
    # Scope for read access to activities and profile
    scope = 'read,activity:read,profile:read_all'
    auth_url = f"https://www.strava.com/oauth/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope={scope}"
    
    return render_template('login.html', auth_url=auth_url)

@auth_bp.route('/callback')
def callback():
    error = request.args.get('error')
    if error:
        flash(f"Authorization error: {error}", 'danger')
        return redirect(url_for('auth.login'))
    
    code = request.args.get('code')
    if not code:
        flash('Authorization code not received.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Exchange code for token
    client_id = app.config['STRAVA_CLIENT_ID']
    client_secret = app.config['STRAVA_CLIENT_SECRET']
    token_url = "https://www.strava.com/oauth/token"
    
    try:
        response = requests.post(
            token_url,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'grant_type': 'authorization_code'
            }
        )
        response.raise_for_status()
        token_data = response.json()
        
        # Extract token information
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('expires_at')
        
        if not all([access_token, refresh_token, expires_at]):
            flash('Incomplete token data received.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Extract athlete data
        athlete = token_data.get('athlete')
        if not athlete:
            flash('Athlete data not received.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if user exists
        user = User.query.filter_by(strava_id=athlete.get('id')).first()
        
        if user:
            # Update existing user
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expiry = datetime.fromtimestamp(expires_at)
            user.firstname = athlete.get('firstname')
            user.lastname = athlete.get('lastname')
            user.profile_pic = athlete.get('profile')
        else:
            # Create new user
            user = User(
                strava_id=athlete.get('id'),
                username=athlete.get('username'),
                firstname=athlete.get('firstname'),
                lastname=athlete.get('lastname'),
                profile_pic=athlete.get('profile'),
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=datetime.fromtimestamp(expires_at)
            )
        
        # Save user to database
        db.session.add(user)
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))
        
    except requests.exceptions.RequestException as e:
        flash(f"Error exchanging authorization code: {str(e)}", 'danger')
        logging.error(f"Strava token request error: {str(e)}")
        return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

def refresh_strava_token(user):
    """Refresh Strava access token if expired"""
    if not user.token_expired():
        return True
    
    client_id = app.config['STRAVA_CLIENT_ID']
    client_secret = app.config['STRAVA_CLIENT_SECRET']
    token_url = "https://www.strava.com/oauth/token"
    
    try:
        response = requests.post(
            token_url,
            data={
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': user.refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        response.raise_for_status()
        
        token_data = response.json()
        user.access_token = token_data.get('access_token')
        user.refresh_token = token_data.get('refresh_token')
        user.token_expiry = datetime.fromtimestamp(token_data.get('expires_at'))
        
        db.session.add(user)
        db.session.commit()
        return True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Token refresh error: {str(e)}")
        return False
