import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone

from nba_api.stats.endpoints import (
    BoxScoreTraditionalV2,
    PlayerGameLogs,
    PlayerIndex,
    PlayerNextNGames,
    ScheduleLeagueV2,
    ScoreboardV2,
)
from nba_api.stats.static import teams as teams_static

from app.services.config import get_env_float, get_env_int
from app.services.injuries_service import get_normalized_injury_report
from app.services.schema_service import validate_payload_for_endpoint
from app.services.storage_service import upload_raw_payload

logger = logging.getLogger(__name__)


def persist_validated_payload(endpoint_name: str, payload: dict | list, params: dict | None = None, source: str = 'nba_api') -> str:
    validate_payload_for_endpoint(endpoint_name=endpoint_name, payload=payload)
    return upload_raw_payload(endpoint_name=endpoint_name, payload=payload, params=params, source=source)


def _call_nba_api_with_resilience(factory, call_name: str) -> dict:
    timeout_seconds = get_env_float('NBA_API_TIMEOUT_SECONDS', 15.0)
    max_retries = max(0, get_env_int('NBA_API_MAX_RETRIES', 2))
    delay_ms = max(0, get_env_int('NBA_API_REQUEST_DELAY_MS', 300))
    backoff_base_seconds = max(0.0, get_env_float('NBA_API_BACKOFF_BASE_SECONDS', 1.0))

    for attempt in range(max_retries + 1):
        try:
            payload = factory(timeout_seconds).get_dict()
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)
            return payload
        except Exception as exc:
            if attempt >= max_retries:
                raise
            wait_time = backoff_base_seconds * (2**attempt) + random.uniform(0, 0.25)
            logger.warning(
                'nba_api call failed. call=%s attempt=%d/%d error=%s retry_in=%.2fs',
                call_name,
                attempt + 1,
                max_retries + 1,
                str(exc),
                wait_time,
            )
            time.sleep(wait_time)


def _get_result_set(payload: dict, dataset_name: str) -> tuple[list, list]:
    for result_set in payload.get('resultSets', []):
        if result_set.get('name') == dataset_name:
            return result_set.get('headers', []), result_set.get('rowSet', [])
    return [], []


def _extract_scoreboard_game_ids(scoreboard_payload: dict) -> list[str]:
    headers, rows = _get_result_set(scoreboard_payload, 'GameHeader')
    if not headers:
        return []

    game_id_index = None
    for possible_header in ('GAME_ID', 'game_id'):
        if possible_header in headers:
            game_id_index = headers.index(possible_header)
            break

    if game_id_index is None:
        return []

    game_ids: list[str] = []
    for row in rows:
        if game_id_index < len(row):
            game_ids.append(str(row[game_id_index]))
    return game_ids


def _extract_player_ids_from_player_index(player_index_payload: dict) -> list[int]:
    headers, rows = _get_result_set(player_index_payload, 'PlayerIndex')
    if not headers:
        return []

    person_id_index = headers.index('PERSON_ID') if 'PERSON_ID' in headers else None
    roster_status_index = headers.index('ROSTER_STATUS') if 'ROSTER_STATUS' in headers else None
    if person_id_index is None:
        return []

    player_ids: list[int] = []
    for row in rows:
        if person_id_index >= len(row):
            continue
        if roster_status_index is not None and roster_status_index < len(row):
            try:
                roster_status = int(row[roster_status_index])
            except (ValueError, TypeError):
                roster_status = 0
            if roster_status != 1:
                continue
        try:
            player_ids.append(int(row[person_id_index]))
        except (TypeError, ValueError):
            continue
    return player_ids


def _extract_player_ids_from_boxscore(boxscore_payload: dict) -> set[int]:
    player_ids: set[int] = set()
    for result_set in boxscore_payload.get('resultSets', []):
        headers = result_set.get('headers', [])
        rows = result_set.get('rowSet', [])
        player_id_index = None
        for possible_header in ('PLAYER_ID', 'PERSON_ID'):
            if possible_header in headers:
                player_id_index = headers.index(possible_header)
                break

        if player_id_index is None:
            continue

        for row in rows:
            if player_id_index < len(row):
                try:
                    player_ids.add(int(row[player_id_index]))
                except (TypeError, ValueError):
                    continue
    return player_ids


def _resolve_target_dates() -> list[str]:
    explicit_date = os.environ.get('PLAYER_PARTICIPANT_GAME_DATE')
    if explicit_date:
        return [explicit_date]

    lookback_days = max(1, get_env_int('PLAYER_PARTICIPANT_LOOKBACK_DAYS', 1))
    current_date = datetime.now(timezone.utc).date()
    dates: list[str] = []
    for days_back in range(1, lookback_days + 1):
        target_date = current_date - timedelta(days=days_back)
        dates.append(target_date.strftime('%m/%d/%Y'))
    return dates


def _resolve_player_ids_for_participant_jobs() -> tuple[list[int], str, str]:
    discovered_player_ids: set[int] = set()
    target_dates = _resolve_target_dates()

    for game_date in target_dates:
        scoreboard_payload = _call_nba_api_with_resilience(
            lambda timeout: ScoreboardV2(game_date=game_date, timeout=timeout),
            call_name=f'scoreboard_v2 game_date={game_date}',
        )
        game_ids = _extract_scoreboard_game_ids(scoreboard_payload)
        for game_id in game_ids:
            boxscore_payload = _call_nba_api_with_resilience(
                lambda timeout, gid=game_id: BoxScoreTraditionalV2(game_id=gid, timeout=timeout),
                call_name=f'boxscore_traditional_v2 game_id={game_id}',
            )
            discovered_player_ids.update(_extract_player_ids_from_boxscore(boxscore_payload))

    ordered_ids = sorted(discovered_player_ids)
    max_players = get_env_int('PLAYER_JOB_MAX_PLAYERS_PER_RUN', 150)
    if max_players > 0:
        ordered_ids = ordered_ids[:max_players]

    if not ordered_ids:
        player_index_payload = _call_nba_api_with_resilience(
            lambda timeout: PlayerIndex(timeout=timeout),
            call_name='player_index fallback_for_participants',
        )
        fallback_ids = sorted(_extract_player_ids_from_player_index(player_index_payload))
        if max_players > 0:
            fallback_ids = fallback_ids[:max_players]
        ordered_ids = fallback_ids

    target_dates_sorted = sorted(target_dates)
    date_from = target_dates_sorted[0]
    date_to = target_dates_sorted[-1]
    return ordered_ids, date_from, date_to


def _raise_if_consecutive_failures_exceeded(consecutive_failures: int) -> None:
    max_consecutive_failures = max(1, get_env_int('NBA_API_MAX_CONSECUTIVE_ERRORS', 5))
    if consecutive_failures >= max_consecutive_failures:
        raise RuntimeError(
            f'Aborting ingestion after {consecutive_failures} consecutive nba_api failures '
            f'(NBA_API_MAX_CONSECUTIVE_ERRORS={max_consecutive_failures})'
        )


def run_schedule_raw_ingestion() -> str:
    endpoint_name = 'schedule_league_v2'
    logger.info('Starting %s raw ingestion job', endpoint_name)

    season_year = os.environ.get('SCHEDULE_DEFAULT_SEASON_YEAR')
    params: dict[str, str] = {}

    if season_year:
        year = int(season_year)
        season = f"{year}-{str(year + 1)[-2:]}"
        params['season'] = season
        response = ScheduleLeagueV2(season=season)
    else:
        response = ScheduleLeagueV2()

    payload = response.get_dict()
    key = persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params=params)
    logger.info('Completed %s raw ingestion job. s3_key=%s', endpoint_name, key)
    return key


def run_scoreboard_raw_ingestion() -> str:
    endpoint_name = 'scoreboard_v2'
    logger.info('Starting %s raw ingestion job', endpoint_name)

    game_date = os.environ.get('SCOREBOARD_GAME_DATE')
    params: dict[str, str] = {}

    if game_date:
        params['game_date'] = game_date
        response = ScoreboardV2(game_date=game_date)
    else:
        response = ScoreboardV2()

    payload = response.get_dict()
    key = persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params=params)
    logger.info('Completed %s raw ingestion job. s3_key=%s', endpoint_name, key)
    return key


def run_teams_raw_ingestion() -> str:
    endpoint_name = 'teams_static'
    logger.info('Starting %s raw ingestion job', endpoint_name)
    payload = teams_static.get_teams()
    key = persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params={})
    logger.info('Completed %s raw ingestion job. s3_key=%s', endpoint_name, key)
    return key


def run_player_index_raw_ingestion() -> str:
    endpoint_name = 'player_index'
    logger.info('Starting %s raw ingestion job', endpoint_name)
    payload = _call_nba_api_with_resilience(
        lambda timeout: PlayerIndex(timeout=timeout),
        call_name='player_index',
    )
    key = persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params={})
    logger.info('Completed %s raw ingestion job. s3_key=%s', endpoint_name, key)
    return key


def run_player_game_logs_raw_ingestion() -> list[str]:
    endpoint_name = 'player_game_logs'
    logger.info('Starting %s raw ingestion job', endpoint_name)

    player_ids, date_from, date_to = _resolve_player_ids_for_participant_jobs()
    if not player_ids:
        logger.info('No players discovered for %s job window %s-%s', endpoint_name, date_from, date_to)
        return []

    season = os.environ.get('PLAYER_GAME_LOGS_SEASON')
    keys: list[str] = []
    consecutive_failures = 0
    for player_id in player_ids:
        params: dict[str, str | int] = {
            'player_id': player_id,
            'date_from': date_from,
            'date_to': date_to,
        }
        kwargs = {
            'player_id_nullable': player_id,
            'date_from_nullable': date_from,
            'date_to_nullable': date_to,
        }
        if season:
            params['season'] = season
            kwargs['season_nullable'] = season

        try:
            payload = _call_nba_api_with_resilience(
                lambda timeout, _kwargs=kwargs: PlayerGameLogs(timeout=timeout, **_kwargs),
                call_name=f'player_game_logs player_id={player_id}',
            )
            keys.append(persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params=params))
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            logger.exception('Failed player_game_logs fetch for player_id=%s error=%s', player_id, str(exc))
            _raise_if_consecutive_failures_exceeded(consecutive_failures)

    logger.info(
        'Completed %s raw ingestion job. persisted=%d date_from=%s date_to=%s',
        endpoint_name,
        len(keys),
        date_from,
        date_to,
    )
    return keys


def run_player_next_n_games_raw_ingestion() -> list[str]:
    endpoint_name = 'player_next_n_games'
    logger.info('Starting %s raw ingestion job', endpoint_name)

    player_ids, date_from, date_to = _resolve_player_ids_for_participant_jobs()
    if not player_ids:
        logger.info('No players discovered for %s job window %s-%s', endpoint_name, date_from, date_to)
        return []

    season = os.environ.get('PLAYER_NEXT_GAMES_SEASON')
    number_of_games = max(1, get_env_int('PLAYER_NEXT_GAMES_NUMBER_OF_GAMES', 5))
    keys: list[str] = []
    consecutive_failures = 0

    for player_id in player_ids:
        params: dict[str, str | int] = {'player_id': player_id, 'number_of_games': number_of_games}
        kwargs = {'player_id': player_id, 'number_of_games': number_of_games}
        if season:
            params['season'] = season
            kwargs['season_all'] = season

        try:
            payload = _call_nba_api_with_resilience(
                lambda timeout, _kwargs=kwargs: PlayerNextNGames(timeout=timeout, **_kwargs),
                call_name=f'player_next_n_games player_id={player_id}',
            )
            keys.append(persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params=params))
            consecutive_failures = 0
        except Exception as exc:
            consecutive_failures += 1
            logger.exception('Failed player_next_n_games fetch for player_id=%s error=%s', player_id, str(exc))
            _raise_if_consecutive_failures_exceeded(consecutive_failures)

    logger.info(
        'Completed %s raw ingestion job. persisted=%d date_from=%s date_to=%s',
        endpoint_name,
        len(keys),
        date_from,
        date_to,
    )
    return keys


def run_injury_report_raw_ingestion() -> str:
    endpoint_name = 'injury_report'
    logger.info('Starting %s raw ingestion job', endpoint_name)

    injuries, raw_count = get_normalized_injury_report()
    payload = {
        'source': 'nbainjuries',
        'raw_entries_count': raw_count,
        'count': len(injuries),
        'injuries': injuries,
        'updated_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    }

    key = persist_validated_payload(endpoint_name=endpoint_name, payload=payload, params={}, source='nbainjuries')
    logger.info('Completed %s raw ingestion job. s3_key=%s', endpoint_name, key)
    return key


def safe_job_runner(job_name: str, job_func):
    try:
        job_func()
    except Exception as exc:
        logger.exception('Job failed: %s error=%s', job_name, str(exc))
