from datetime import datetime

from flask import Blueprint, jsonify, request
from nba_api.stats.endpoints import (
    PlayerGameLogs,
    PlayerIndex,
    PlayerNextNGames,
    ScheduleLeagueV2,
    ScoreboardV2,
)
from nba_api.stats.static import teams as teams_static

from app.services.config import endpoint_persist_enabled, get_missing_required_env_vars
from app.services.ingestion_service import persist_validated_payload
from app.utils.request_utils import parse_int_query_param, should_persist_raw_from_request

api_blueprint = Blueprint('api', __name__)


def maybe_persist_endpoint_payload(endpoint_name: str, payload: dict | list, params: dict | None = None) -> str | None:
    if not endpoint_persist_enabled():
        return None
    if not should_persist_raw_from_request():
        return None
    return persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params=params)


@api_blueprint.route('/')
def index():
    return jsonify(
        {
            'name': 'NBA API Client Server',
            'version': '1.0.0',
            'endpoints': {
                '/schedule': 'Get NBA league schedule',
                '/scoreboard': 'Get NBA scoreboard data',
                '/teams': 'Get NBA teams list with ids',
                '/players/index': 'Get player index data',
                '/players/game-logs': 'Get player game logs',
                '/players/next-games': 'Get next N games for a player',
                '/health': 'Health check endpoint',
            },
        }
    )


@api_blueprint.route('/health')
def health():
    missing_vars = get_missing_required_env_vars()
    response = {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
    if missing_vars:
        response['config_warnings'] = {
            'missing_required_env_vars': missing_vars,
            'storage_ready': False,
        }
    return jsonify(response)


@api_blueprint.route('/health/config')
def health_config():
    missing_vars = get_missing_required_env_vars()
    return jsonify(
        {
            'storage_ready': len(missing_vars) == 0,
            'missing_required_env_vars': missing_vars,
        }
    )


@api_blueprint.route('/schedule')
def get_schedule():
    try:
        season = request.args.get('season')
        params = {}
        if season:
            try:
                year = int(season)
                season_value = f"{year}-{str(year + 1)[-2:]}"
                schedule = ScheduleLeagueV2(season=season_value)
                params['season'] = season_value
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid season parameter. Must be a valid year (e.g., 2023)'}), 400
        else:
            schedule = ScheduleLeagueV2()

        payload = schedule.get_dict()
        raw_key = maybe_persist_endpoint_payload('schedule_league_v2', payload, params)
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_blueprint.route('/scoreboard')
def get_scoreboard():
    try:
        game_date = request.args.get('game_date')
        params = {}

        if game_date:
            try:
                datetime.strptime(game_date, '%m/%d/%Y')
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid game_date format. Use MM/DD/YYYY.'}), 400

            payload = ScoreboardV2(game_date=game_date).get_dict()
            params['game_date'] = game_date
        else:
            payload = ScoreboardV2().get_dict()

        raw_key = maybe_persist_endpoint_payload('scoreboard_v2', payload, params)
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_blueprint.route('/teams')
def get_teams():
    try:
        payload = teams_static.get_teams()
        raw_key = maybe_persist_endpoint_payload('teams_static', payload, {})
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_blueprint.route('/players/index')
def get_players_index():
    try:
        active = request.args.get('active', '1')
        if active not in {'0', '1'}:
            return jsonify({'success': False, 'error': 'Invalid active parameter. Must be 0 or 1.'}), 400

        params = {'active': int(active)}
        payload = PlayerIndex(active_nullable=active).get_dict()
        raw_key = maybe_persist_endpoint_payload('player_index', payload, params)
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_blueprint.route('/players/game-logs')
def get_player_game_logs():
    try:
        player_id = request.args.get('player_id')
        season = request.args.get('season')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        if player_id is None and (not date_from or not date_to):
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'Provide player_id or both date_from and date_to query parameters.',
                    }
                ),
                400,
            )

        if player_id is None and (date_from and date_to) and not season:
            return (
                jsonify(
                    {
                        'success': False,
                        'error': 'season is required when using date_from/date_to.',
                    }
                ),
                400,
            )

        kwargs = {}
        params = {}

        if player_id is not None:
            try:
                player_id_int = int(player_id)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid player_id. Must be an integer.'}), 400

            if not season:
                return (
                    jsonify(
                        {
                            'success': False,
                            'error': 'season is required when player_id is provided.',
                        }
                    ),
                    400,
                )

            kwargs['player_id_nullable'] = player_id_int
            params['player_id'] = player_id_int

        if season:
            kwargs['season_nullable'] = season
            params['season'] = season

        if date_from:
            kwargs['date_from_nullable'] = date_from
            params['date_from'] = date_from
        if date_to:
            kwargs['date_to_nullable'] = date_to
            params['date_to'] = date_to

        payload = PlayerGameLogs(**kwargs).get_dict()
        raw_key = maybe_persist_endpoint_payload('player_game_logs', payload, params)
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@api_blueprint.route('/players/next-games')
def get_player_next_n_games():
    try:
        player_id, error_response, status_code = parse_int_query_param('player_id')
        if error_response:
            return error_response, status_code

        number_of_games = request.args.get('number_of_games', '5')
        try:
            number_of_games_int = int(number_of_games)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid number_of_games. Must be an integer.'}), 400

        season = request.args.get('season')
        kwargs = {'player_id': player_id, 'number_of_games': number_of_games_int}
        params = {'player_id': player_id, 'number_of_games': number_of_games_int}
        if season:
            kwargs['season_all'] = season
            params['season'] = season

        payload = PlayerNextNGames(**kwargs).get_dict()
        raw_key = maybe_persist_endpoint_payload('player_next_n_games', payload, params)
        response = {'success': True, 'data': payload}
        if raw_key:
            response['raw_s3_key'] = raw_key
        return jsonify(response)
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500
