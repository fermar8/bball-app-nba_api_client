import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.services.config import get_env_bool, get_env_int
from app.services.ingestion_service import (
    run_injury_report_raw_ingestion,
    run_player_game_logs_raw_ingestion,
    run_player_index_raw_ingestion,
    run_player_next_n_games_raw_ingestion,
    run_schedule_raw_ingestion,
    run_scoreboard_raw_ingestion,
    run_teams_raw_ingestion,
    safe_job_runner,
)

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone='UTC')
scheduler_started = False


def _register_cron_job(job_id: str, job_func, hour_env: str, minute_env: str, default_hour: int, default_minute: int) -> None:
    hour = get_env_int(hour_env, default_hour)
    minute = get_env_int(minute_env, default_minute)
    scheduler.add_job(
        lambda: safe_job_runner(job_id, job_func),
        trigger='cron',
        id=job_id,
        replace_existing=True,
        hour=hour,
        minute=minute,
    )
    logger.info('Scheduler registered job %s at %02d:%02d UTC', job_id, hour, minute)


def start_scheduler() -> None:
    global scheduler_started
    if scheduler_started:
        return

    schedule_enabled = get_env_bool('SCHEDULE_JOB_ENABLED', False)
    scoreboard_enabled = get_env_bool('SCOREBOARD_JOB_ENABLED', False)
    teams_enabled = get_env_bool('TEAMS_JOB_ENABLED', False)
    player_index_enabled = get_env_bool('PLAYER_INDEX_JOB_ENABLED', False)
    player_game_logs_enabled = get_env_bool('PLAYER_GAME_LOGS_JOB_ENABLED', False)
    player_next_games_enabled = get_env_bool('PLAYER_NEXT_GAMES_JOB_ENABLED', False)
    injury_report_enabled = get_env_bool('INJURY_REPORT_JOB_ENABLED', False)

    if schedule_enabled:
        _register_cron_job(
            job_id='schedule_raw_ingestion',
            job_func=run_schedule_raw_ingestion,
            hour_env='SCHEDULE_JOB_HOUR_UTC',
            minute_env='SCHEDULE_JOB_MINUTE_UTC',
            default_hour=3,
            default_minute=0,
        )
        if get_env_bool('SCHEDULE_JOB_RUN_ON_STARTUP', False):
            safe_job_runner('schedule_raw_ingestion_startup', run_schedule_raw_ingestion)

    if scoreboard_enabled:
        _register_cron_job(
            job_id='scoreboard_raw_ingestion',
            job_func=run_scoreboard_raw_ingestion,
            hour_env='SCOREBOARD_JOB_HOUR_UTC',
            minute_env='SCOREBOARD_JOB_MINUTE_UTC',
            default_hour=5,
            default_minute=0,
        )
        if get_env_bool('SCOREBOARD_JOB_RUN_ON_STARTUP', False):
            safe_job_runner('scoreboard_raw_ingestion_startup', run_scoreboard_raw_ingestion)

    if teams_enabled:
        _register_cron_job(
            job_id='teams_raw_ingestion',
            job_func=run_teams_raw_ingestion,
            hour_env='TEAMS_JOB_HOUR_UTC',
            minute_env='TEAMS_JOB_MINUTE_UTC',
            default_hour=4,
            default_minute=0,
        )

    if player_index_enabled:
        _register_cron_job(
            job_id='player_index_raw_ingestion',
            job_func=run_player_index_raw_ingestion,
            hour_env='PLAYER_INDEX_JOB_HOUR_UTC',
            minute_env='PLAYER_INDEX_JOB_MINUTE_UTC',
            default_hour=4,
            default_minute=30,
        )

    if player_game_logs_enabled:
        _register_cron_job(
            job_id='player_game_logs_raw_ingestion',
            job_func=run_player_game_logs_raw_ingestion,
            hour_env='PLAYER_GAME_LOGS_JOB_HOUR_UTC',
            minute_env='PLAYER_GAME_LOGS_JOB_MINUTE_UTC',
            default_hour=6,
            default_minute=0,
        )

    if player_next_games_enabled:
        _register_cron_job(
            job_id='player_next_games_raw_ingestion',
            job_func=run_player_next_n_games_raw_ingestion,
            hour_env='PLAYER_NEXT_GAMES_JOB_HOUR_UTC',
            minute_env='PLAYER_NEXT_GAMES_JOB_MINUTE_UTC',
            default_hour=6,
            default_minute=30,
        )

    if injury_report_enabled:
        _register_cron_job(
            job_id='injury_report_raw_ingestion',
            job_func=run_injury_report_raw_ingestion,
            hour_env='INJURY_REPORT_JOB_HOUR_UTC',
            minute_env='INJURY_REPORT_JOB_MINUTE_UTC',
            default_hour=22,
            default_minute=0,
        )
        if get_env_bool('INJURY_REPORT_JOB_RUN_ON_STARTUP', False):
            safe_job_runner('injury_report_raw_ingestion_startup', run_injury_report_raw_ingestion)

    if (
        schedule_enabled
        or scoreboard_enabled
        or teams_enabled
        or player_index_enabled
        or player_game_logs_enabled
        or player_next_games_enabled
        or injury_report_enabled
    ):
        scheduler.start()
        scheduler_started = True
        logger.info('In-process scheduler started')
    else:
        logger.info('Scheduler is disabled. Enable jobs with *_JOB_ENABLED=true')
