import os

from dotenv import load_dotenv


def load_environment() -> None:
    load_dotenv()


REQUIRED_ENV_VARS = ('S3_BUCKET_NAME', 'AWS_ACCOUNT_ID')


def get_missing_required_env_vars() -> list[str]:
    missing_vars: list[str] = []
    for env_var in REQUIRED_ENV_VARS:
        if not os.environ.get(env_var, '').strip():
            missing_vars.append(env_var)
    return missing_vars


def get_env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def get_env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_s3_bucket_name() -> str:
    value = os.environ.get('S3_BUCKET_NAME', '').strip()
    if not value:
        raise ValueError('Missing required environment variable: S3_BUCKET_NAME')
    return value


def get_aws_account_id() -> str:
    value = os.environ.get('AWS_ACCOUNT_ID', '').strip()
    if not value:
        raise ValueError('Missing required environment variable: AWS_ACCOUNT_ID')
    return value


def is_debug_mode() -> bool:
    return get_env_bool('FLASK_DEBUG', False)


def should_start_scheduler() -> bool:
    return (
        get_env_bool('ENABLE_IN_PROCESS_SCHEDULER', True)
        and os.environ.get('WERKZEUG_RUN_MAIN') != 'false'
    )


def endpoint_persist_enabled() -> bool:
    return get_env_bool('ENABLE_ENDPOINT_S3_UPLOAD', True)
