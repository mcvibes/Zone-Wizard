# Zone Wizard - Heart Rate Zone Tracker

A web application that integrates with Strava to provide comprehensive heart rate zone analysis and training insights.

## Features

- **Strava Integration**: Seamless OAuth authentication with Strava
- **Heart Rate Zone Analysis**: Customizable 5-zone heart rate system with 20 BPM increments
- **Activity Filtering**: Filter zone data by activity type (Run, Ride, Workout, etc.)
- **Time Period Analysis**: View zone distribution over 7 days, 30 days, 3 months, or 1 year
- **Interactive Visualizations**: Pie charts and progress bars showing time spent in each zone
- **Activity Details**: Individual activity analysis with heart rate charts
- **Zone Customization**: Set your maximum heart rate for personalized zone calculations

## Technology Stack

- **Backend**: Python Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: Bootstrap 5 with Chart.js for visualizations
- **Authentication**: Strava OAuth 2.0
- **Deployment**: Replit

## Zone Calculation Method

Uses a simplified 5-zone system based on maximum heart rate:
- Zone 1 (Recovery): Below Max HR - 100 BPM
- Zone 2 (Endurance): Max HR - 100 to Max HR - 80 BPM  
- Zone 3 (Aerobic): Max HR - 80 to Max HR - 60 BPM
- Zone 4 (Threshold): Max HR - 60 to Max HR - 40 BPM
- Zone 5 (Anaerobic): Max HR - 40 to Max HR BPM

## Setup Instructions

### 1. Create Strava API Application
1. Go to https://www.strava.com/settings/api
2. Create a new application
3. Set Authorization Callback Domain to your Replit domain
4. Note your Client ID and Client Secret

### 2. Environment Variables
Set these secrets in your Replit environment:
- `STRAVA_CLIENT_ID`: Your Strava application client ID
- `STRAVA_CLIENT_SECRET`: Your Strava application client secret
- `DATABASE_URL`: PostgreSQL connection string (automatically provided by Replit)

### 3. Deploy
1. Fork this repository
2. Import into Replit
3. Add the environment variables
4. Run the application

## Usage

1. Click "Login with Strava" to authenticate
2. Your activities with heart rate data will be automatically synced
3. Use the dashboard filters to analyze your training:
   - Select different time periods
   - Filter by activity type
4. Customize your heart rate zones in the Profile section
5. Click on individual activities for detailed analysis

## Contributing

This project is open for contributions. Feel free to submit issues or pull requests.

## License

MIT License - feel free to use this code for your own projects.
