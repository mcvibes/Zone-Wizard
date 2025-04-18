import requests
import logging
from datetime import datetime
import numpy as np
from auth import refresh_strava_token
from models import Activity, db
from zone_calculator import calculate_activity_zones

def get_athlete_activities(user, page=1, per_page=30):
    """
    Fetch activities from the Strava API for the given user
    Returns a list of activities
    """
    # Refresh token if needed
    if not refresh_strava_token(user):
        logging.error(f"Failed to refresh token for user {user.id}")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {user.access_token}"}
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers,
            params={"page": page, "per_page": per_page}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching activities: {str(e)}")
        return None

def get_activity_details(user, activity_id):
    """
    Fetch detailed activity data including streams from Strava API
    Returns the activity with heart rate data
    """
    # Refresh token if needed
    if not refresh_strava_token(user):
        logging.error(f"Failed to refresh token for user {user.id}")
        return None
    
    try:
        # First, get the activity details
        headers = {"Authorization": f"Bearer {user.access_token}"}
        response = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}",
            headers=headers,
            params={"include_all_efforts": False}
        )
        response.raise_for_status()
        activity_data = response.json()
        
        # Check if activity has heart rate data
        if not activity_data.get('has_heartrate'):
            logging.info(f"Activity {activity_id} does not have heart rate data")
            return activity_data, None
        
        # Then get the heart rate stream
        stream_response = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}/streams",
            headers=headers,
            params={"keys": "heartrate,time", "key_by_type": True}
        )
        stream_response.raise_for_status()
        streams = stream_response.json()
        
        # Extract heart rate and time streams
        hr_stream = streams.get('heartrate', {}).get('data', [])
        time_stream = streams.get('time', {}).get('data', [])
        
        # Create a combined stream with time and heart rate
        combined_stream = None
        if hr_stream and time_stream and len(hr_stream) == len(time_stream):
            combined_stream = [(time_stream[i], hr_stream[i]) for i in range(len(hr_stream))]
        
        return activity_data, combined_stream
    
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching activity details: {str(e)}")
        return None, None

def sync_activities(user, max_activities=30):
    """
    Fetch and store the user's activities from Strava
    Returns the number of new activities synced
    """
    activities = get_athlete_activities(user, per_page=max_activities)
    if not activities:
        return 0
    
    new_count = 0
    for strava_activity in activities:
        # Check if activity already exists
        existing = Activity.query.filter_by(strava_id=strava_activity['id']).first()
        if existing:
            continue
        
        # Get full activity details with heart rate data if available
        activity_detail, hr_stream = get_activity_details(user, strava_activity['id'])
        if not activity_detail:
            continue
        
        # Create new activity record
        activity = Activity(
            strava_id=strava_activity['id'],
            user_id=user.id,
            name=strava_activity['name'],
            type=strava_activity['type'],
            distance=strava_activity['distance'],
            moving_time=strava_activity['moving_time'],
            elapsed_time=strava_activity['elapsed_time'],
            start_date=datetime.strptime(strava_activity['start_date'], '%Y-%m-%dT%H:%M:%SZ'),
            has_heartrate=strava_activity.get('has_heartrate', False),
            average_hr=strava_activity.get('average_heartrate'),
            max_hr=strava_activity.get('max_heartrate')
        )
        
        # Store heart rate data if available
        if hr_stream:
            activity.set_hr_data(hr_stream)
            
            # Calculate and store heart rate zones
            zones = calculate_activity_zones(user, hr_stream)
            if zones:
                activity.set_zone_data(zones)
        
        db.session.add(activity)
        new_count += 1
    
    if new_count > 0:
        db.session.commit()
    
    return new_count

def get_user_profile(user):
    """
    Fetch the user's profile from Strava
    Returns the user profile data
    """
    # Refresh token if needed
    if not refresh_strava_token(user):
        logging.error(f"Failed to refresh token for user {user.id}")
        return None
    
    try:
        headers = {"Authorization": f"Bearer {user.access_token}"}
        response = requests.get(
            "https://www.strava.com/api/v3/athlete",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching user profile: {str(e)}")
        return None
