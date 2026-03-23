"""Application entrypoint for the NBA API client server."""

import logging

from app import create_app
from app.services.config import get_missing_required_env_vars, is_debug_mode, should_start_scheduler
from app.services.ingestion_service import (
    persist_validated_payload,
    run_injury_report_raw_ingestion,
    run_player_game_logs_raw_ingestion,
    run_player_index_raw_ingestion,
    run_player_next_n_games_raw_ingestion,
    run_schedule_raw_ingestion,
    run_scoreboard_raw_ingestion,
    run_teams_raw_ingestion,
    safe_job_runner,
)
from app.services.scheduler_service import scheduler, start_scheduler
from app.services.storage_service import get_s3_client, upload_raw_payload

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

app = create_app()


if __name__ == '__main__':
    missing_vars = get_missing_required_env_vars()
    if missing_vars:
        logging.warning('Missing required env vars for storage: %s', ','.join(missing_vars))

    if should_start_scheduler():
        start_scheduler()
    app.run(host='0.0.0.0', port=5000, debug=is_debug_mode())
