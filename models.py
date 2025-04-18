from datetime import datetime
from app import db
from flask_login import UserMixin
import json
import numpy as np

# Custom JSON encoder to handle NumPy types
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.Integer, unique=True, nullable=False)
    username = db.Column(db.String(64))
    firstname = db.Column(db.String(64))
    lastname = db.Column(db.String(64))
    email = db.Column(db.String(120))
    profile_pic = db.Column(db.String(255))
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    token_expiry = db.Column(db.DateTime)
    activities = db.relationship('Activity', backref='user', lazy='dynamic')
    
    def token_expired(self):
        """Check if Strava token has expired"""
        if self.token_expiry is None:
            return True
        return datetime.utcnow() > self.token_expiry
    
    def get_id(self):
        """Return the user ID as a unicode string"""
        return str(self.id)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strava_id = db.Column(db.BigInteger, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(255))
    type = db.Column(db.String(64))
    distance = db.Column(db.Float)
    moving_time = db.Column(db.Integer)
    elapsed_time = db.Column(db.Integer)
    start_date = db.Column(db.DateTime)
    average_hr = db.Column(db.Float)
    max_hr = db.Column(db.Float)
    has_heartrate = db.Column(db.Boolean, default=False)
    hr_data = db.Column(db.Text)  # Stored as JSON string
    zone_data = db.Column(db.Text)  # Stored as JSON string
    
    def get_hr_data(self):
        """Return heart rate data as a list"""
        if self.hr_data:
            return json.loads(self.hr_data)
        return []
    
    def set_hr_data(self, hr_data):
        """Store heart rate data as a JSON string"""
        self.hr_data = json.dumps(hr_data, cls=NumpyEncoder)
    
    def get_zone_data(self):
        """Return zone data as a dictionary"""
        if self.zone_data:
            return json.loads(self.zone_data)
        return {}
    
    def set_zone_data(self, zone_data):
        """Store zone data as a JSON string"""
        self.zone_data = json.dumps(zone_data, cls=NumpyEncoder)

class HeartRateZones(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    max_hr = db.Column(db.Integer)  # Maximum heart rate
    resting_hr = db.Column(db.Integer)  # Resting heart rate
    zone_method = db.Column(db.String(64), default="percentage")  # percentage or karvonen
    
    # Zone thresholds (percentages of max HR)
    zone1_threshold = db.Column(db.Integer, default=60)  # 50-60% of max HR - Very Light
    zone2_threshold = db.Column(db.Integer, default=70)  # 60-70% of max HR - Light
    zone3_threshold = db.Column(db.Integer, default=80)  # 70-80% of max HR - Moderate
    zone4_threshold = db.Column(db.Integer, default=90)  # 80-90% of max HR - Hard
    zone5_threshold = db.Column(db.Integer, default=100)  # 90-100% of max HR - Maximum
    
    def calculate_zones(self):
        """Calculate the actual heart rate values for each zone"""
        if not self.max_hr:
            return None
        
        # Simple 20bpm increments method as requested with adjusted Zone 4 and 5
        # Zone 1: max_hr - 80bpm to max_hr - 60bpm (120-140 bpm for max_hr=200)
        # Zone 2: max_hr - 60bpm to max_hr - 40bpm (140-160 bpm for max_hr=200)
        # Zone 3: max_hr - 40bpm to max_hr - 20bpm (160-180 bpm for max_hr=200)
        # Zone 4: 180-200 bpm (for all max heart rates)
        # Zone 5: 200+ bpm (for all max heart rates)
        zones = {
            "zone1": {
                "min": max(self.max_hr - 80, 90),  # Ensure min is at least 90bpm
                "max": self.max_hr - 60
            },
            "zone2": {
                "min": self.max_hr - 60,
                "max": self.max_hr - 40
            },
            "zone3": {
                "min": self.max_hr - 40,
                "max": 180  # Fixed at 180 bpm as requested
            },
            "zone4": {
                "min": 180,  # Fixed at 180 bpm as requested
                "max": 200   # Fixed at 200 bpm as requested
            },
            "zone5": {
                "min": 200,  # Fixed at 200 bpm as requested
                "max": 220   # Just for visualization purposes
            }
        }
        
        return zones
