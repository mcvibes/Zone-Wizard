import numpy as np
from models import HeartRateZones

def calculate_max_hr(age, gender='male'):
    """
    Calculate theoretical maximum heart rate based on age
    using the formula: 220 - age (for males) or 226 - age (for females)
    """
    if gender.lower() == 'female':
        return 226 - age
    else:
        return 220 - age

def get_or_create_user_zones(user):
    """
    Get user's heart rate zones or create default ones
    """
    from app import db
    
    zones = HeartRateZones.query.filter_by(user_id=user.id).first()
    if not zones:
        # Create default zones
        max_hr = 180  # Default value, will need to be updated by user
        zones = HeartRateZones(
            user_id=user.id,
            max_hr=max_hr,
            resting_hr=60,  # Default resting HR
            zone_method="percentage"
        )
        db.session.add(zones)
        db.session.commit()
    
    return zones

def calculate_activity_zones(user, hr_data):
    """
    Calculate time spent in each heart rate zone for an activity
    Returns a dictionary with zone data
    """
    # Get user's heart rate zones
    user_zones = get_or_create_user_zones(user)
    zones = user_zones.calculate_zones()
    
    if not zones or not hr_data:
        return None
    
    # Extract heart rate values and times
    times = [point[0] for point in hr_data]
    hr_values = [point[1] for point in hr_data]
    
    # Calculate time difference between consecutive points
    time_diffs = np.diff(times, prepend=0)
    time_diffs[0] = 0  # First point has no time difference
    
    # Initialize zone times
    zone_times = {
        "zone1": 0,
        "zone2": 0,
        "zone3": 0,
        "zone4": 0,
        "zone5": 0,
        "below": 0,  # Below zone 1
        "total": sum(time_diffs[1:])  # Total time excluding first point
    }
    
    # Calculate time in each zone
    for i, hr in enumerate(hr_values):
        if i == 0:
            continue  # Skip first point as we don't have a time difference
        
        if hr < zones["zone1"]["min"]:
            zone_times["below"] += time_diffs[i]
        elif hr < zones["zone2"]["min"]:
            zone_times["zone1"] += time_diffs[i]
        elif hr < zones["zone3"]["min"]:
            zone_times["zone2"] += time_diffs[i]
        elif hr < zones["zone4"]["min"]:
            zone_times["zone3"] += time_diffs[i]
        elif hr < zones["zone5"]["min"]:
            zone_times["zone4"] += time_diffs[i]
        else:
            zone_times["zone5"] += time_diffs[i]
    
    # Calculate percentages
    zone_percentages = {}
    if zone_times["total"] > 0:
        for zone in ["zone1", "zone2", "zone3", "zone4", "zone5", "below"]:
            zone_percentages[zone] = round((zone_times[zone] / zone_times["total"]) * 100, 1)
    
    # Combine all zone data
    zone_data = {
        "times": zone_times,
        "percentages": zone_percentages,
        "zone_ranges": zones
    }
    
    return zone_data

def format_zone_times(zone_data):
    """
    Format zone times for display
    Returns a dictionary with formatted times
    """
    if not zone_data or "times" not in zone_data:
        return {}
    
    formatted = {}
    for zone, seconds in zone_data["times"].items():
        if zone == "total":
            continue
        
        minutes = int(seconds / 60)
        hours = int(minutes / 60)
        minutes = minutes % 60
        
        if hours > 0:
            formatted[zone] = f"{hours}h {minutes}m"
        else:
            formatted[zone] = f"{minutes}m"
    
    return formatted

def get_zone_colors():
    """
    Return standard colors for heart rate zones
    """
    return {
        "zone1": "#3A86FF",  # Blue - Easy
        "zone2": "#4CB944",  # Green - Fat Burn
        "zone3": "#FFD60A",  # Yellow - Aerobic
        "zone4": "#FF9E0A",  # Orange - Threshold
        "zone5": "#FF0000",  # Red - Maximum
        "below": "#AAAAAA"   # Gray - Below zone 1
    }

def get_zone_labels():
    """
    Return human-readable labels for heart rate zones with BPM ranges
    """
    return {
        "zone1": "Zone 1 - Very Light (120-140 bpm)",
        "zone2": "Zone 2 - Light (140-160 bpm)",
        "zone3": "Zone 3 - Moderate (160-180 bpm)",
        "zone4": "Zone 4 - Hard (180-200 bpm)",
        "zone5": "Zone 5 - Maximum (200+ bpm)",
        "below": "Below Zone 1 (<120 bpm)"
    }
