from __future__ import annotations

import importlib
import json
import re
from datetime import datetime
from typing import Any

from nba_api.stats.endpoints import PlayerIndex
from nba_api.stats.static import teams as teams_static


def _normalize_name(name: str) -> str:
    lowered = name.lower().strip()
    lowered = re.sub(r"[\.,'\-]", ' ', lowered)
    lowered = re.sub(r'\s+', ' ', lowered)
    return lowered


def _canonical_player_name(name: str) -> str:
    text = str(name or '').strip()
    if ',' in text:
        last, first = [part.strip() for part in text.split(',', 1)]
        if first and last:
            return f'{first} {last}'
    return text


def _build_team_abbreviation_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for team in teams_static.get_teams():
        full_name = str(team.get('full_name') or '').strip()
        abbreviation = str(team.get('abbreviation') or '').strip().upper()
        nickname = str(team.get('nickname') or '').strip()
        city = str(team.get('city') or '').strip()

        if full_name and abbreviation:
            index[full_name.lower()] = abbreviation
        if nickname and abbreviation:
            index[nickname.lower()] = abbreviation
        if city and nickname and abbreviation:
            index[f'{city} {nickname}'.lower()] = abbreviation
    return index


def _build_player_id_index() -> dict[str, int]:
    payload = PlayerIndex(active_nullable='0').get_dict()
    result_sets = payload.get('resultSets', [])

    headers: list[str] = []
    rows: list[list[Any]] = []
    for result_set in result_sets:
        if result_set.get('name') == 'PlayerIndex':
            headers = result_set.get('headers', [])
            rows = result_set.get('rowSet', [])
            break

    if not headers or not rows:
        return {}

    index: dict[str, int] = {}
    try:
        person_id_idx = headers.index('PERSON_ID')
        first_idx = headers.index('PLAYER_FIRST_NAME')
        last_idx = headers.index('PLAYER_LAST_NAME')
    except ValueError:
        return {}

    for row in rows:
        if max(person_id_idx, first_idx, last_idx) >= len(row):
            continue
        person_id = row[person_id_idx]
        first = str(row[first_idx] or '').strip()
        last = str(row[last_idx] or '').strip()
        if not first and not last:
            continue
        full_name = _normalize_name(f'{first} {last}'.strip())
        if full_name and isinstance(person_id, int):
            index[full_name] = person_id

    return index


def _extract_entries(raw_payload: Any) -> list[dict[str, Any]]:
    if isinstance(raw_payload, list):
        return [item for item in raw_payload if isinstance(item, dict)]

    if not isinstance(raw_payload, dict):
        return []

    for key in ('injuries', 'data', 'players', 'items', 'results'):
        value = raw_payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    nested = raw_payload.get('report')
    if isinstance(nested, dict):
        for key in ('injuries', 'players', 'items'):
            value = nested.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

    if all(isinstance(v, dict) for v in raw_payload.values()):
        return list(raw_payload.values())

    return []


def _read_field(entry: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = entry.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _normalize_status(raw_status: str | None, raw_reason: str | None) -> str:
    text = f'{raw_status or ""} {raw_reason or ""}'.lower()

    if any(token in text for token in ('susp', 'suspended')):
        return 'out'
    if any(token in text for token in ('out', 'inactive', 'not available', 'unavailable')):
        return 'out'
    if 'questionable' in text:
        return 'questionable'
    if 'doubtful' in text:
        return 'doubtful'
    if any(token in text for token in ('probable', 'gtd', 'game time decision')):
        return 'probable'
    if any(token in text for token in ('available', 'active', 'healthy')):
        return 'available'
    return 'unknown'


def _status_to_availability(status: str) -> str:
    if status == 'out':
        return 'no'
    if status in {'questionable', 'doubtful', 'probable'}:
        return 'doubtful'
    if status == 'available':
        return 'yes'
    return 'doubtful'


def _reason_type(raw_reason: str | None) -> str:
    text = (raw_reason or '').lower()
    if 'susp' in text:
        return 'suspension'
    if any(token in text for token in ('injury', 'illness', 'knee', 'ankle', 'hamstring', 'calf', 'wrist', 'foot', 'back')):
        return 'injury'
    if any(token in text for token in ('personal', 'bereavement')):
        return 'personal'
    if any(token in text for token in ('coach', 'decision')):
        return 'coach_decision'
    if any(token in text for token in ('inactive', 'not with team', 'nwt')):
        return 'inactive'
    return 'unknown'


def _find_latest_valid_timestamp(check_reportvalid, gen_url) -> datetime | None:
    """
    Scan backwards in 15-minute steps (up to 48 hours) to find the most recently
    published NBA injury report. The NBA only publishes PDFs at scheduled times,
    not at every minute, so datetime.now() often resolves to a non-existent file.
    """
    import logging
    logger = logging.getLogger(__name__)
    now = datetime.now()
    # Snap to the nearest past 15-minute boundary to start probing
    snapped = now.replace(second=0, microsecond=0, minute=(now.minute // 15) * 15)
    step = 0
    max_steps = 48 * 4  # 48 hours in 15-min steps
    while step < max_steps:
        candidate = snapped - __import__('datetime').timedelta(minutes=15 * step)
        try:
            if check_reportvalid(candidate):
                logger.info('Found valid injury report at %s', candidate)
                return candidate
        except Exception:
            pass
        step += 1
    return None


def _load_nbainjuries_payload() -> Any:
    try:
        module = importlib.import_module('nbainjuries')
    except ImportError as exc:
        raise RuntimeError('nbainjuries dependency is not installed.') from exc
    except Exception as exc:
        raise RuntimeError(f'nbainjuries could not initialize. Ensure Java is installed and JAVA_HOME is set. Details: {str(exc)}') from exc

    injury_mod = getattr(module, 'injury', None)
    if injury_mod is not None:
        get_reportdata = getattr(injury_mod, 'get_reportdata', None)
        check_reportvalid = getattr(injury_mod, 'check_reportvalid', None)
        if callable(get_reportdata):
            timestamp = datetime.now()
            if callable(check_reportvalid):
                valid_ts = _find_latest_valid_timestamp(check_reportvalid, None)
                if valid_ts is not None:
                    timestamp = valid_ts
                else:
                    raise RuntimeError(
                        'No published NBA injury report found in the last 48 hours. '
                        'The NBA may not have published one yet today.'
                    )
            report = get_reportdata(timestamp)
            if isinstance(report, str):
                return json.loads(report)
            return report

    for function_name in ('get_injuries', 'fetch_injuries', 'load_injuries', 'injuries'):
        function = getattr(module, function_name, None)
        if callable(function):
            return function()

    class_name_candidates = ('NBAInjuries', 'Injuries', 'InjuryReport')
    method_name_candidates = ('get_injuries', 'fetch', 'run', 'to_dict', 'to_json')

    for class_name in class_name_candidates:
        cls = getattr(module, class_name, None)
        if cls is None:
            continue
        instance = cls()
        for method_name in method_name_candidates:
            method = getattr(instance, method_name, None)
            if callable(method):
                return method()

    raise RuntimeError('Unable to locate a supported API in nbainjuries module.')


def get_normalized_injury_report() -> tuple[list[dict[str, Any]], int]:
    raw_payload = _load_nbainjuries_payload()
    entries = _extract_entries(raw_payload)
    player_id_index = _build_player_id_index()
    team_abbr_index = _build_team_abbreviation_index()

    normalized: list[dict[str, Any]] = []
    for entry in entries:
        # nbainjuries uses title-case keys with spaces ("Player Name", "Current Status", etc.)
        # so check both those and generic snake_case / camelCase variants.
        player_name = _read_field(entry, 'Player Name', 'player_name', 'playerName', 'name', 'player')
        if not player_name:
            continue

        raw_team = _read_field(entry, 'Team', 'team', 'team_abbr', 'teamAbbr', 'abbr')
        raw_status = _read_field(entry, 'Current Status', 'status', 'injury_status', 'injuryStatus', 'designation')
        reason = _read_field(entry, 'Reason', 'reason', 'description', 'comment', 'details', 'injury')
        report_date = _read_field(entry, 'Game Date', 'date', 'report_date', 'reportDate', 'updated_at', 'timestamp')

        status = _normalize_status(raw_status=raw_status, raw_reason=reason)
        availability = _status_to_availability(status)
        reason_type = _reason_type(reason)

        canonical_player_name = _canonical_player_name(player_name)
        normalized_name = _normalize_name(canonical_player_name)
        player_id = player_id_index.get(normalized_name)
        team_abbr = team_abbr_index.get((raw_team or '').lower(), raw_team)

        normalized.append(
            {
                'player_id': player_id,
            'player_name': canonical_player_name,
                'team_abbr': team_abbr,
                'status': status,
                'availability': availability,
                'reason_type': reason_type,
                'reason': reason,
                'report_date': report_date,
            }
        )

    return normalized, len(entries)
