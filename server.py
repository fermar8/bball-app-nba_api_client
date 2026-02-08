"""
NBA API Client Server
A Flask server that consumes the nba_api library to provide basketball data endpoints.
"""

from flask import Flask, jsonify, request
from nba_api.stats.endpoints import ScheduleLeagueV2
from datetime import datetime

app = Flask(__name__)


@app.route('/')
def index():
    """Root endpoint with API information."""
    return jsonify({
        'name': 'NBA API Client Server',
        'version': '1.0.0',
        'endpoints': {
            '/schedule': 'Get NBA league schedule',
            '/health': 'Health check endpoint'
        }
    })


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/schedule')
def get_schedule():
    """
    Get NBA league schedule using ScheduleLeagueV2 endpoint.
    
    Query Parameters:
    - season: Season in format YYYY (default: current season)
    
    Example: /schedule?season=2023
    """
    try:
        # Get season parameter from query string (optional)
        season = request.args.get('season', None)
        
        # Initialize the ScheduleLeagueV2 endpoint
        if season:
            schedule = ScheduleLeagueV2(season=f"{season}-{str(int(season) + 1)[-2:]}")
        else:
            schedule = ScheduleLeagueV2()
        
        # Get the schedule data
        schedule_data = schedule.get_dict()
        
        return jsonify({
            'success': True,
            'data': schedule_data
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
