"""Set processed tag state for an S3 raw object.

Usage:
  python scripts/set_object_processed_state.py --key <s3_object_key> --processed true|false [--endpoint <endpoint_name>]
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.config import load_environment
from app.services.storage_service import mark_object_processed, mark_object_unprocessed


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off'}:
        return False
    raise argparse.ArgumentTypeError("--processed must be true/false")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Set S3 raw object processed tag state')
    parser.add_argument('--key', required=True, help='S3 object key to update')
    parser.add_argument('--processed', required=True, type=parse_bool, help='Target processed value: true or false')
    parser.add_argument('--endpoint', default='unknown', help='Endpoint name used in endpoint tag (default: unknown)')
    return parser.parse_args()


def main() -> None:
    load_environment()
    args = parse_args()

    if args.processed:
        mark_object_processed(object_key=args.key, endpoint_name=args.endpoint)
        print(f"Set processed=true for key: {args.key}")
    else:
        mark_object_unprocessed(object_key=args.key, endpoint_name=args.endpoint)
        print(f"Set processed=false for key: {args.key}")


if __name__ == '__main__':
    main()
