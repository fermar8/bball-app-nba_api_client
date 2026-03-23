from __future__ import annotations

import importlib
import json
import re
from datetime import datetime
from typing import Any

from nba_api.stats.endpoints import PlayerIndex


def _normalize_name(name: str) -> str:
    lowered = name.lower().strip()
    lowered = re.sub(r"[\.,'\-]", ' ', lowered)
    lowered = re.sub(r'\s+', ' ', lowered)
    return lowered


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
        if callable(get_reportdata):
            report = get_reportdata(datetime.now())
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

    normalized: list[dict[str, Any]] = []
    for entry in entries:
        player_name = _read_field(entry, 'player_name', 'playerName', 'name', 'player')
        if not player_name:
            continue

        team_abbr = _read_field(entry, 'team', 'team_abbr', 'teamAbbr', 'abbr')
        raw_status = _read_field(entry, 'status', 'injury_status', 'injuryStatus', 'designation')
        reason = _read_field(entry, 'reason', 'description', 'comment', 'details', 'injury')
        report_date = _read_field(entry, 'date', 'report_date', 'reportDate', 'updated_at', 'timestamp')

        status = _normalize_status(raw_status=raw_status, raw_reason=reason)
        availability = _status_to_availability(status)
        reason_type = _reason_type(reason)

        normalized_name = _normalize_name(player_name)
        player_id = player_id_index.get(normalized_name)

        normalized.append(
            {
                'player_id': player_id,
                'player_name': player_name,
                'team_abbr': team_abbr,
                'status': status,
                'availability': availability,
                'reason_type': reason_type,
                'reason': reason,
                'report_date': report_date,
            }
        )

    return normalized, len(entries)
