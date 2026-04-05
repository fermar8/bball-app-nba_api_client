from flask import jsonify, request


def parse_int_query_param(param_name: str):
    value = request.args.get(param_name)
    if value is None:
        return None, jsonify({'success': False, 'error': f'Missing required parameter: {param_name}'}), 400
    try:
        return int(value), None, None
    except ValueError:
        return None, jsonify({'success': False, 'error': f'Invalid {param_name}. Must be an integer.'}), 400


def should_persist_raw_from_request() -> bool:
    value = request.args.get('persist_raw', 'false')
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}
