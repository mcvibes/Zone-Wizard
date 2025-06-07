# Zone Wizard - Developer Setup Guide

## Quick Start for Code Review

This is a Flask web application that integrates with Strava for heart rate zone analysis.

### Project Overview
- **Purpose**: Track time spent in heart rate zones using Strava activity data
- **Stack**: Python Flask, PostgreSQL, Strava OAuth, Chart.js
- **Current Status**: Fully functional with 30+ users, hit Strava API limits

### Key Files to Review

#### Core Application
- `app.py` - Flask app configuration, database setup
- `main.py` - Entry point
- `models.py` - Database models (User, Activity, HeartRateZones)

#### Business Logic
- `auth.py` - Strava OAuth authentication flow
- `strava_client.py` - Strava API integration and data fetching
- `zone_calculator.py` - Heart rate zone calculations
- `routes.py` - Web routes and API endpoints

#### Frontend
- `templates/` - HTML templates using Bootstrap
- `static/js/charts.js` - Chart.js visualizations
- `static/css/custom.css` - Custom styling

### Local Development Setup

1. **Install Dependencies**
   ```bash
   pip install flask flask-sqlalchemy flask-login psycopg2-binary requests oauthlib
   ```

2. **Database Setup**
   ```bash
   # PostgreSQL required
   createdb zone_wizard_dev
   export DATABASE_URL="postgresql://user:pass@localhost/zone_wizard_dev"
   ```

3. **Strava API Setup**
   - Create app at https://www.strava.com/settings/api
   - Set callback URL to `http://localhost:5000/callback`
   ```bash
   export STRAVA_CLIENT_ID="your_client_id"
   export STRAVA_CLIENT_SECRET="your_client_secret"
   export SESSION_SECRET="any_random_string"
   ```

4. **Run Application**
   ```bash
   python main.py
   # Or with gunicorn:
   gunicorn --bind 0.0.0.0:5000 --reload main:app
   ```

### Architecture Notes

#### Database Schema
- **User**: Strava user data, OAuth tokens
- **Activity**: Strava activities with heart rate data (JSON stored)
- **HeartRateZones**: User-configurable zone thresholds

#### Heart Rate Zone Logic
- Uses 5-zone system with 20 BPM increments from max HR
- Zone 1: Below (Max HR - 100), Zone 5: (Max HR - 40) to Max HR
- Calculates percentage time spent in each zone per activity

#### Key Challenges Solved
1. **Token Management**: Auto-refresh expired Strava tokens
2. **Data Sync**: Efficient activity syncing with duplicate prevention
3. **Zone Calculation**: Real-time zone analysis from heart rate streams
4. **API Limits**: Handles Strava's 100 requests/15min, 1000/day limits

### Code Review Focus Areas

1. **Security**: OAuth implementation, token storage
2. **Performance**: Database queries, API rate limiting
3. **Error Handling**: Strava API failures, missing heart rate data
4. **Code Structure**: Separation of concerns, modularity
5. **Scalability**: Database design, caching opportunities

### Current Issues & Limitations

1. **Strava API Quota**: Hit 100-user limit on free tier
2. **Git Integration**: Replit git sync issues (why this manual setup)
3. **Activity Filtering**: UI display issues with filter dropdowns
4. **Zone Customization**: Limited to percentage-based calculations

### Production Environment
- **Deployed on**: Replit
- **Domain**: zone-wizard-malcolmmcdonal1.replit.app
- **Database**: Replit PostgreSQL
- **Users**: 30+ active users before hitting API limits

### Questions for Review

1. Best practices for Strava OAuth token management?
2. Optimizing database queries for activity analysis?
3. Caching strategies for zone calculations?
4. Handling Strava API rate limits more gracefully?
5. Code organization and module structure improvements?

---

All source files are included in this archive. The application is fully functional and can be run locally following the setup instructions above.