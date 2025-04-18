import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy import desc, func
from app import app, db
from models import User, Activity, HeartRateZones
from strava_client import sync_activities, get_activity_details
from zone_calculator import get_zone_colors, get_zone_labels, format_zone_times, calculate_max_hr

@app.route('/')
def index():
    """Homepage route"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing activity summaries and zone data"""
    # Sync latest activities
    try:
        new_activities = sync_activities(current_user)
        if new_activities > 0:
            flash(f"Synced {new_activities} new activities from Strava", "success")
    except Exception as e:
        logging.error(f"Error syncing activities: {str(e)}")
        flash("Failed to sync activities from Strava", "danger")
    
    # Get date filters or use defaults
    days = request.args.get('days', 30, type=int)
    if days not in [7, 30, 90, 365]:
        days = 30
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get activities within date range
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.start_date >= start_date,
        Activity.start_date <= end_date,
        Activity.has_heartrate == True
    ).order_by(desc(Activity.start_date)).all()
    
    # Calculate total time in each zone across all activities
    zone_totals = {
        "zone1": 0,
        "zone2": 0,
        "zone3": 0,
        "zone4": 0,
        "zone5": 0,
        "below": 0,
        "total": 0
    }
    
    for activity in activities:
        zone_data = activity.get_zone_data()
        if zone_data and "times" in zone_data:
            for zone, time in zone_data["times"].items():
                if zone in zone_totals:
                    zone_totals[zone] += time
    
    # Calculate percentages
    zone_percentages = {}
    if zone_totals["total"] > 0:
        for zone in ["zone1", "zone2", "zone3", "zone4", "zone5", "below"]:
            zone_percentages[zone] = round((zone_totals[zone] / zone_totals["total"]) * 100, 1)
    
    # Format zone times for display
    formatted_times = format_zone_times({"times": zone_totals})
    
    # Get user's heart rate zones
    user_zones = HeartRateZones.query.filter_by(user_id=current_user.id).first()
    
    # Get labels and colors for zones
    zone_colors = get_zone_colors()
    zone_labels = get_zone_labels()
    
    return render_template(
        'dashboard.html',
        activities=activities, 
        zone_totals=zone_totals,
        zone_percentages=zone_percentages,
        formatted_times=formatted_times,
        zone_colors=zone_colors,
        zone_labels=zone_labels,
        user_zones=user_zones,
        days=days
    )

@app.route('/activity/<int:activity_id>')
@login_required
def activity_detail(activity_id):
    """Show detailed information about a specific activity"""
    activity = Activity.query.filter_by(id=activity_id, user_id=current_user.id).first_or_404()
    
    # Get heart rate data and zone information
    hr_data = activity.get_hr_data()
    zone_data = activity.get_zone_data()
    
    # Format zone times
    formatted_times = format_zone_times(zone_data)
    
    # Get labels and colors for zones
    zone_colors = get_zone_colors()
    zone_labels = get_zone_labels()
    
    # Get user's heart rate zones
    user_zones = HeartRateZones.query.filter_by(user_id=current_user.id).first()
    
    return render_template(
        'activity_detail.html',
        activity=activity,
        hr_data=hr_data,
        zone_data=zone_data,
        formatted_times=formatted_times,
        zone_colors=zone_colors,
        zone_labels=zone_labels,
        user_zones=user_zones
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile and heart rate zone settings"""
    user_zones = HeartRateZones.query.filter_by(user_id=current_user.id).first()
    
    # Initialize with defaults if not exists
    if not user_zones:
        user_zones = HeartRateZones(
            user_id=current_user.id,
            max_hr=180,
            resting_hr=60,
            zone_method="percentage"
        )
        db.session.add(user_zones)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            # Update only max heart rate using the fixed 20bpm increments method
            max_hr = int(request.form.get('max_hr', 180))
            
            # Validate max_hr range
            if max_hr < 100 or max_hr > 230:
                flash('Maximum heart rate must be between 100 and 230 bpm', 'danger')
            else:
                user_zones.max_hr = max_hr
                db.session.commit()
                flash('Heart rate zone settings updated successfully!', 'success')
                
                # Recalculate zones for all activities
                recalculate_all_activity_zones(current_user.id)
                
                return redirect(url_for('profile'))
        
        except ValueError:
            flash('Please enter valid numbers for heart rate values', 'danger')
    
    # Calculate estimated max HR based on age if available
    estimated_max_hr = None
    try:
        # This is a placeholder - in a real app, you would get age from Strava API
        # or ask the user to provide their age
        age = 30  # Default age
        estimated_max_hr = calculate_max_hr(age)
    except:
        pass
    
    # Calculate actual zone values
    zones = user_zones.calculate_zones()
    
    # Get zone colors from zone_calculator
    zone_colors = get_zone_colors()
    zone_labels = get_zone_labels()
    
    return render_template(
        'profile.html',
        user=current_user,
        user_zones=user_zones,
        zones=zones,
        zone_colors=zone_colors,
        zone_labels=zone_labels,
        estimated_max_hr=estimated_max_hr
    )

@app.route('/api/activities/<int:activity_id>/hr_data')
@login_required
def get_activity_hr_data(activity_id):
    """API endpoint to get heart rate data for charts"""
    activity = Activity.query.filter_by(id=activity_id, user_id=current_user.id).first_or_404()
    
    hr_data = activity.get_hr_data()
    if not hr_data:
        return jsonify({'error': 'No heart rate data available'}), 404
    
    # Convert to format needed for Chart.js
    chart_data = {
        'labels': [point[0] for point in hr_data],  # Time values in seconds
        'datasets': [{
            'label': 'Heart Rate',
            'data': [point[1] for point in hr_data],  # HR values
            'borderColor': '#FF6384',
            'backgroundColor': 'rgba(255, 99, 132, 0.2)',
            'fill': True,
            'tension': 0.1
        }]
    }
    
    # Add zone lines if available
    zone_data = activity.get_zone_data()
    if zone_data and 'zone_ranges' in zone_data:
        zones = zone_data['zone_ranges']
        zone_colors = get_zone_colors()
        
        for zone, data in zones.items():
            chart_data['datasets'].append({
                'label': f'{zone.capitalize()} Max',
                'data': [data['max']] * len(hr_data),
                'borderColor': zone_colors[zone],
                'borderDash': [5, 5],
                'borderWidth': 1,
                'pointRadius': 0,
                'fill': False
            })
    
    return jsonify(chart_data)

@app.route('/api/dashboard/zone_summary')
@login_required
def zone_summary_data():
    """API endpoint to get zone summary data for dashboard charts"""
    # Get date filters or use defaults
    days = request.args.get('days', 30, type=int)
    if days not in [7, 30, 90, 365]:
        days = 30
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get activities within date range
    activities = Activity.query.filter(
        Activity.user_id == current_user.id,
        Activity.start_date >= start_date,
        Activity.start_date <= end_date,
        Activity.has_heartrate == True
    ).all()
    
    # Calculate total time in each zone across all activities
    zone_totals = {
        "zone1": 0,
        "zone2": 0,
        "zone3": 0,
        "zone4": 0,
        "zone5": 0,
        "below": 0
    }
    
    for activity in activities:
        zone_data = activity.get_zone_data()
        if zone_data and "times" in zone_data:
            for zone, time in zone_data["times"].items():
                if zone in zone_totals:
                    zone_totals[zone] += time
    
    # Prepare data for Chart.js
    zone_labels = get_zone_labels()
    zone_colors = get_zone_colors()
    
    chart_data = {
        'labels': [zone_labels[zone] for zone in zone_totals.keys()],
        'datasets': [{
            'data': [zone_totals[zone] / 60 for zone in zone_totals.keys()],  # Convert to minutes
            'backgroundColor': [zone_colors[zone] for zone in zone_totals.keys()],
            'borderWidth': 1
        }]
    }
    
    return jsonify(chart_data)

def recalculate_all_activity_zones(user_id):
    """
    Recalculate zone data for all activities of a user
    This is called when zone settings are updated
    """
    from zone_calculator import calculate_activity_zones
    
    activities = Activity.query.filter_by(user_id=user_id, has_heartrate=True).all()
    user = User.query.get(user_id)
    
    for activity in activities:
        hr_data = activity.get_hr_data()
        if hr_data:
            zones = calculate_activity_zones(user, hr_data)
            if zones:
                activity.set_zone_data(zones)
    
    db.session.commit()
