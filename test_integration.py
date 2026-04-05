"""Unit tests for routes, ingestion, scheduler, and optional endpoint persistence."""

import os
import json
import unittest
from unittest.mock import MagicMock, patch

import server


def build_valid_schedule_payload():
    return {
        'meta': {'version': 1, 'request': 'test', 'time': '2026-03-08T00:00:00Z'},
        'leagueSchedule': {
            'seasonYear': '2025-26',
            'leagueId': '00',
            'gameDates': [
                {
                    'gameDate': '2026-03-08',
                    'games': [
                        {
                            'homeTeam': {
                                'teamId': 1,
                                'teamName': 'Home',
                                'teamCity': 'City',
                                'teamTricode': 'HOM',
                                'teamSlug': 'home',
                                'wins': 1,
                                'losses': 1,
                                'score': 100,
                                'seed': 0,
                            },
                            'awayTeam': {
                                'teamId': 2,
                                'teamName': 'Away',
                                'teamCity': 'City',
                                'teamTricode': 'AWY',
                                'teamSlug': 'away',
                                'wins': 1,
                                'losses': 1,
                                'score': 99,
                                'seed': 0,
                            },
                            'pointsLeaders': [
                                {
                                    'personId': 123,
                                    'firstName': 'First',
                                    'lastName': 'Last',
                                    'teamId': 1,
                                    'teamCity': 'City',
                                    'teamName': 'Home',
                                    'teamTricode': 'HOM',
                                    'points': 30,
                                }
                            ],
                        }
                    ],
                }
            ],
            'weeks': [],
        },
    }


def build_valid_scoreboard_payload():
    return {
        'resource': 'scoreboardv2',
        'parameters': {},
        'resultSets': [{'name': 'GameHeader', 'headers': ['GAME_ID'], 'rowSet': [['0022400001']]}],
    }


def build_valid_player_index_payload():
    return {
        'resource': 'playerindex',
        'parameters': {},
        'resultSets': [{'name': 'PlayerIndex', 'headers': ['PERSON_ID'], 'rowSet': [[2544]]}],
    }


def build_valid_player_game_logs_payload():
    return {
        'resource': 'playergamelogs',
        'parameters': {'PlayerID': '2544'},
        'resultSets': [{'name': 'PlayerGameLogs', 'headers': ['PLAYER_ID'], 'rowSet': [[2544]]}],
    }


def build_valid_player_next_games_payload():
    return {
        'resource': 'playernextngames',
        'parameters': {'PlayerID': '2544'},
        'resultSets': [{'name': 'NextNGames', 'headers': ['GAME_ID'], 'rowSet': [['0022400001']]}],
    }


def build_valid_boxscore_payload():
    return {
        'resource': 'boxscoretraditionalv2',
        'parameters': {'GameID': '0022400001'},
        'resultSets': [
            {'name': 'PlayerStats', 'headers': ['PLAYER_ID', 'PTS'], 'rowSet': [[2544, 25], [201939, 30]]}
        ],
    }


class ServerRouteTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()

    def test_health_route_returns_healthy(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['status'], 'healthy')

    def test_health_config_route_with_missing_env_vars(self):
        with patch.dict(os.environ, {'S3_BUCKET_NAME': '', 'AWS_ACCOUNT_ID': ''}, clear=False):
            response = self.client.get('/health/config')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertFalse(payload['storage_ready'])
        self.assertIn('S3_BUCKET_NAME', payload['missing_required_env_vars'])
        self.assertIn('AWS_ACCOUNT_ID', payload['missing_required_env_vars'])

    def test_health_route_includes_config_warnings_when_missing_env_vars(self):
        with patch.dict(os.environ, {'S3_BUCKET_NAME': '', 'AWS_ACCOUNT_ID': ''}, clear=False):
            response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn('config_warnings', payload)
        self.assertFalse(payload['config_warnings']['storage_ready'])

    @patch('app.routes.api_routes.ScheduleLeagueV2')
    def test_schedule_route_with_season(self, mock_schedule_cls):
        mock_schedule = MagicMock()
        mock_schedule.get_dict.return_value = build_valid_schedule_payload()
        mock_schedule_cls.return_value = mock_schedule

        response = self.client.get('/schedule?season=2023')

        self.assertEqual(response.status_code, 200)
        mock_schedule_cls.assert_called_once_with(season='2023-24')
        self.assertTrue(response.get_json()['success'])

    def test_schedule_route_invalid_season(self):
        response = self.client.get('/schedule?season=abc')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.get_json()['success'])

    @patch('app.routes.api_routes.ScoreboardV2')
    def test_scoreboard_route_default(self, mock_scoreboard_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_scoreboard_payload()
        mock_scoreboard_cls.return_value = endpoint_response

        response = self.client.get('/scoreboard')

        self.assertEqual(response.status_code, 200)
        mock_scoreboard_cls.assert_called_once_with()
        self.assertTrue(response.get_json()['success'])

    @patch('app.routes.api_routes.ScoreboardV2')
    def test_scoreboard_route_with_game_date(self, mock_scoreboard_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_scoreboard_payload()
        mock_scoreboard_cls.return_value = endpoint_response

        response = self.client.get('/scoreboard?game_date=03/06/2026')

        self.assertEqual(response.status_code, 200)
        mock_scoreboard_cls.assert_called_once_with(game_date='03/06/2026')
        self.assertTrue(response.get_json()['success'])

    def test_scoreboard_route_invalid_game_date(self):
        response = self.client.get('/scoreboard?game_date=2026-03-06')

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertFalse(payload['success'])
        self.assertEqual(payload['error'], 'Invalid game_date format. Use MM/DD/YYYY.')

    @patch('app.routes.api_routes.persist_validated_payload')
    @patch('app.routes.api_routes.ScoreboardV2')
    def test_scoreboard_route_persist_raw(self, mock_scoreboard_cls, mock_persist):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_scoreboard_payload()
        mock_scoreboard_cls.return_value = endpoint_response
        mock_persist.return_value = 'raw/scoreboard_v2/2026/03/08/file.json'

        response = self.client.get('/scoreboard?persist_raw=true')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn('raw_s3_key', payload)
        mock_persist.assert_called_once()

    @patch('app.routes.api_routes.persist_validated_payload')
    @patch('app.routes.api_routes.ScheduleLeagueV2')
    def test_schedule_route_persist_raw(self, mock_schedule_cls, mock_persist):
        mock_schedule = MagicMock()
        mock_schedule.get_dict.return_value = build_valid_schedule_payload()
        mock_schedule_cls.return_value = mock_schedule
        mock_persist.return_value = 'raw/schedule_league_v2/2026/03/08/file.json'

        response = self.client.get('/schedule?persist_raw=true')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn('raw_s3_key', payload)
        mock_persist.assert_called_once()

    @patch('app.routes.api_routes.teams_static.get_teams')
    def test_teams_route(self, mock_get_teams):
        mock_get_teams.return_value = [{'id': 1610612737, 'full_name': 'Atlanta Hawks', 'abbreviation': 'ATL', 'nickname': 'Hawks', 'city': 'Atlanta', 'state': 'Georgia', 'year_founded': 1949}]
        response = self.client.get('/teams')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()['success'])

    @patch('app.routes.api_routes.PlayerIndex')
    def test_players_index_route(self, mock_player_index_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_player_index_payload()
        mock_player_index_cls.return_value = endpoint_response

        response = self.client.get('/players/index')

        self.assertEqual(response.status_code, 200)
        mock_player_index_cls.assert_called_once_with(active_nullable='1')

    @patch('app.routes.api_routes.PlayerGameLogs')
    def test_player_game_logs_route(self, mock_player_game_logs_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_player_game_logs_payload()
        mock_player_game_logs_cls.return_value = endpoint_response

        response = self.client.get('/players/game-logs?player_id=2544&season=2025-26')

        self.assertEqual(response.status_code, 200)
        mock_player_game_logs_cls.assert_called_once_with(player_id_nullable=2544, season_nullable='2025-26')

    def test_player_game_logs_requires_season_when_player_id_is_provided(self):
        response = self.client.get('/players/game-logs?player_id=2544')
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload['error'], 'season is required when player_id is provided.')

    @patch('app.routes.api_routes.PlayerGameLogs')
    def test_player_game_logs_route_with_date_range_and_season(self, mock_player_game_logs_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_player_game_logs_payload()
        mock_player_game_logs_cls.return_value = endpoint_response

        response = self.client.get('/players/game-logs?date_from=03/07/2026&date_to=03/07/2026&season=2025-26')

        self.assertEqual(response.status_code, 200)
        mock_player_game_logs_cls.assert_called_once_with(
            date_from_nullable='03/07/2026',
            date_to_nullable='03/07/2026',
            season_nullable='2025-26',
        )

    def test_player_game_logs_requires_season_for_date_range(self):
        response = self.client.get('/players/game-logs?date_from=03/07/2026&date_to=03/07/2026')
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload['error'], 'season is required when using date_from/date_to.')

    def test_player_game_logs_missing_player_id(self):
        response = self.client.get('/players/game-logs')
        self.assertEqual(response.status_code, 400)

    @patch('app.routes.api_routes.PlayerNextNGames')
    def test_player_next_games_route(self, mock_player_next_games_cls):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_player_next_games_payload()
        mock_player_next_games_cls.return_value = endpoint_response

        response = self.client.get('/players/next-games?player_id=2544&number_of_games=4&season=2025-26')

        self.assertEqual(response.status_code, 200)
        mock_player_next_games_cls.assert_called_once_with(player_id=2544, number_of_games=4, season_all='2025-26')

    @patch('app.routes.api_routes.get_normalized_injury_report')
    def test_injuries_report_route(self, mock_get_normalized_report):
        mock_get_normalized_report.return_value = (
            [
                {
                    'player_id': 2544,
                    'player_name': 'LeBron James',
                    'team_abbr': 'LAL',
                    'status': 'questionable',
                    'availability': 'doubtful',
                    'reason_type': 'injury',
                    'reason': 'Right Knee; Soreness',
                    'report_date': '2026-03-23',
                }
            ],
            1,
        )

        response = self.client.get('/injuries/report?status=questionable&team=LAL')

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()['data']
        self.assertEqual(payload['source'], 'nbainjuries')
        self.assertEqual(payload['raw_entries_count'], 1)
        self.assertEqual(payload['count'], 1)
        self.assertEqual(payload['injuries'][0]['player_id'], 2544)
        self.assertEqual(payload['injuries'][0]['availability'], 'doubtful')
        mock_get_normalized_report.assert_called_once()

    @patch('app.routes.api_routes.get_normalized_injury_report')
    def test_injuries_report_route_runtime_error(self, mock_get_normalized_report):
        mock_get_normalized_report.side_effect = RuntimeError('nbainjuries dependency is not installed.')

        response = self.client.get('/injuries/report')

        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertFalse(payload['success'])
        self.assertIn('nbainjuries dependency is not installed.', payload['error'])


class RawIngestionTests(unittest.TestCase):
    @patch('app.services.storage_service.boto3.client')
    def test_upload_raw_payload_to_s3(self, mock_boto_client):
        s3_client = MagicMock()
        mock_boto_client.return_value = s3_client

        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'test-bucket', 'AWS_ACCOUNT_ID': '123456789012'}, clear=False):
            key = server.upload_raw_payload(endpoint_name='schedule_league_v2', payload=build_valid_schedule_payload(), params={'season': '2023-24'})

        self.assertTrue(key.startswith('raw/schedule_league_v2/'))
        s3_client.put_object.assert_called_once()
        args = s3_client.put_object.call_args.kwargs
        body = json.loads(args['Body'].decode('utf-8'))
        self.assertEqual(body['source'], 'nba_api')
        self.assertEqual(body['schema_version'], 'v1')
        self.assertIn('ingestion_id', body)
        self.assertIn('Tagging', args)
        self.assertIn('processed=false', args['Tagging'])

    @patch('app.services.storage_service.boto3.client')
    def test_mark_object_processed_updates_tag(self, mock_boto_client):
        s3_client = MagicMock()
        mock_boto_client.return_value = s3_client

        with patch.dict(os.environ, {'S3_BUCKET_NAME': 'bball-app-nba-data'}, clear=False):
            from app.services.storage_service import mark_object_processed

            mark_object_processed(
                object_key='raw/schedule_league_v2/2026/03/08/14/file.json',
                endpoint_name='schedule_league_v2',
            )

        s3_client.put_object_tagging.assert_called_once()
        tagging_args = s3_client.put_object_tagging.call_args.kwargs
        tag_set = tagging_args['Tagging']['TagSet']
        processed_tag = [item for item in tag_set if item['Key'] == 'processed'][0]
        self.assertEqual(processed_tag['Value'], 'true')

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service.ScheduleLeagueV2')
    def test_run_schedule_raw_ingestion(self, mock_schedule_cls, mock_persist):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_schedule_payload()
        mock_schedule_cls.return_value = endpoint_response

        with patch.dict(os.environ, {'SCHEDULE_DEFAULT_SEASON_YEAR': '2023'}, clear=False):
            server.run_schedule_raw_ingestion()

        mock_schedule_cls.assert_called_once_with(season='2023-24')
        mock_persist.assert_called_once()

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service.ScoreboardV2')
    def test_run_scoreboard_raw_ingestion(self, mock_scoreboard_cls, mock_persist):
        endpoint_response = MagicMock()
        endpoint_response.get_dict.return_value = build_valid_scoreboard_payload()
        mock_scoreboard_cls.return_value = endpoint_response

        with patch.dict(os.environ, {'SCOREBOARD_GAME_DATE': '03/06/2026'}, clear=False):
            server.run_scoreboard_raw_ingestion()

        mock_scoreboard_cls.assert_called_once_with(game_date='03/06/2026')
        mock_persist.assert_called_once()

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service.teams_static.get_teams')
    def test_run_teams_raw_ingestion(self, mock_get_teams, mock_persist):
        mock_get_teams.return_value = [{'id': 1610612737}]
        server.run_teams_raw_ingestion()
        mock_persist.assert_called_once()

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service._call_nba_api_with_resilience')
    def test_run_player_index_raw_ingestion(self, mock_call_nba_api, mock_persist):
        mock_call_nba_api.return_value = build_valid_player_index_payload()
        server.run_player_index_raw_ingestion()
        mock_persist.assert_called_once()

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service._call_nba_api_with_resilience')
    def test_run_player_game_logs_raw_ingestion(self, mock_call_nba_api, mock_persist):
        mock_call_nba_api.side_effect = [
            build_valid_scoreboard_payload(),
            build_valid_boxscore_payload(),
            build_valid_player_game_logs_payload(),
            build_valid_player_game_logs_payload(),
        ]

        with patch.dict(
            os.environ,
            {
                'PLAYER_PARTICIPANT_GAME_DATE': '03/07/2026',
                'PLAYER_JOB_MAX_PLAYERS_PER_RUN': '2',
            },
            clear=True,
        ):
            keys = server.run_player_game_logs_raw_ingestion()

        self.assertEqual(len(keys), 2)
        self.assertEqual(mock_persist.call_count, 2)

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service._call_nba_api_with_resilience')
    def test_run_player_next_games_raw_ingestion(self, mock_call_nba_api, mock_persist):
        mock_call_nba_api.side_effect = [
            build_valid_scoreboard_payload(),
            build_valid_boxscore_payload(),
            build_valid_player_next_games_payload(),
            build_valid_player_next_games_payload(),
        ]

        with patch.dict(
            os.environ,
            {
                'PLAYER_PARTICIPANT_GAME_DATE': '03/07/2026',
                'PLAYER_JOB_MAX_PLAYERS_PER_RUN': '2',
                'PLAYER_NEXT_GAMES_NUMBER_OF_GAMES': '4',
            },
            clear=True,
        ):
            keys = server.run_player_next_n_games_raw_ingestion()

        self.assertEqual(len(keys), 2)
        self.assertEqual(mock_persist.call_count, 2)

    @patch('app.services.ingestion_service.persist_validated_payload')
    @patch('app.services.ingestion_service.get_normalized_injury_report')
    def test_run_injury_report_raw_ingestion(self, mock_get_injuries, mock_persist):
        mock_get_injuries.return_value = (
            [
                {
                    'player_id': 2544,
                    'player_name': 'LeBron James',
                    'team_abbr': 'LAL',
                    'status': 'questionable',
                    'availability': 'doubtful',
                    'reason_type': 'injury',
                    'reason': 'Right Knee; Soreness',
                    'report_date': '2026-03-23',
                }
            ],
            1,
        )
        mock_persist.return_value = 'raw/injury_report/2026/03/23/18/file.json'

        key = server.run_injury_report_raw_ingestion()

        self.assertTrue(key.startswith('raw/injury_report/'))
        mock_get_injuries.assert_called_once()
        mock_persist.assert_called_once()
        call_kwargs = mock_persist.call_args.kwargs
        self.assertEqual(call_kwargs['endpoint_name'], 'injury_report')
        self.assertEqual(call_kwargs['source'], 'nbainjuries')

    def test_validate_invalid_schedule_payload_raises(self):
        with self.assertRaises(ValueError):
            server.persist_validated_payload('schedule_league_v2', {'invalid': 'shape'}, {})


class InjuriesNormalizationTests(unittest.TestCase):
    @patch('app.services.injuries_service.teams_static.get_teams')
    @patch('app.services.injuries_service._build_player_id_index')
    @patch('app.services.injuries_service._load_nbainjuries_payload')
    def test_get_normalized_injury_report_maps_team_abbreviation_and_player_name(
        self,
        mock_load_payload,
        mock_build_player_id_index,
        mock_get_teams,
    ):
        from app.services.injuries_service import get_normalized_injury_report

        mock_load_payload.return_value = [
            {
                'Player Name': 'James, LeBron',
                'Team': 'Los Angeles Lakers',
                'Current Status': 'Questionable',
                'Reason': 'Injury/Illness - Left Foot; Soreness',
                'Game Date': '03/23/2026',
            }
        ]
        mock_build_player_id_index.return_value = {'lebron james': 2544}
        mock_get_teams.return_value = [
            {
                'full_name': 'Los Angeles Lakers',
                'abbreviation': 'LAL',
                'nickname': 'Lakers',
                'city': 'Los Angeles',
            }
        ]

        injuries, raw_count = get_normalized_injury_report()

        self.assertEqual(raw_count, 1)
        self.assertEqual(len(injuries), 1)
        self.assertEqual(injuries[0]['player_id'], 2544)
        self.assertEqual(injuries[0]['player_name'], 'LeBron James')
        self.assertEqual(injuries[0]['team_abbr'], 'LAL')


class SchedulerTests(unittest.TestCase):
    @patch('app.services.scheduler_service.scheduler')
    def test_start_scheduler_registers_all_enabled_data_jobs(self, scheduler_mock):
        with patch('app.services.scheduler_service.scheduler_started', False):
            with patch.dict(
                os.environ,
                {
                    'SCHEDULE_JOB_ENABLED': 'true',
                    'SCOREBOARD_JOB_ENABLED': 'false',
                    'TEAMS_JOB_ENABLED': 'true',
                    'PLAYER_INDEX_JOB_ENABLED': 'true',
                    'PLAYER_GAME_LOGS_JOB_ENABLED': 'true',
                    'PLAYER_NEXT_GAMES_JOB_ENABLED': 'true',
                },
                clear=True,
            ):
                server.start_scheduler()

        self.assertEqual(scheduler_mock.add_job.call_count, 5)
        scheduler_mock.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
