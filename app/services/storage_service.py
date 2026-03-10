import json
import hashlib
from uuid import uuid4
from datetime import datetime, timezone
from urllib.parse import quote_plus

import boto3

from app.services.config import get_aws_account_id, get_env_bool, get_s3_bucket_name


def get_s3_client():
    return boto3.client('s3')


def _serialize_for_hash(params: dict | None) -> str:
    """Serialize request params deterministically for key hashing."""
    return json.dumps(params or {}, sort_keys=True, separators=(',', ':'))


def _build_object_key(endpoint_name: str, now_utc: datetime, params: dict | None) -> str:
    """Build partitioned S3 object key optimized for incremental processing."""
    request_hash = hashlib.sha256(_serialize_for_hash(params).encode('utf-8')).hexdigest()[:8]
    timestamp = now_utc.strftime('%Y%m%dT%H%M%SZ')
    return (
        f"raw/{endpoint_name}/"
        f"{now_utc.strftime('%Y')}/{now_utc.strftime('%m')}/"
        f"{now_utc.strftime('%d')}/{now_utc.strftime('%H')}/"
        f"{timestamp}_{request_hash}.json"
    )


def _build_upload_tags(endpoint_name: str) -> dict[str, str]:
    """Default tags attached to every new raw object upload."""
    return {
        'stage': 'raw',
        'source': 'nba_api',
        'endpoint': endpoint_name,
        'processed': 'false',
    }


def _to_tagging_query(tags: dict[str, str]) -> str:
    """Convert tags dict to S3 Tagging query string format."""
    return '&'.join(f"{quote_plus(key)}={quote_plus(value)}" for key, value in tags.items())


def upload_raw_payload(endpoint_name: str, payload: dict | list, params: dict | None = None) -> str:
    bucket_name = get_s3_bucket_name()
    aws_account_id = get_aws_account_id()
    now_utc = datetime.now(timezone.utc)
    key = _build_object_key(endpoint_name=endpoint_name, now_utc=now_utc, params=params)

    body = {
        'source': 'nba_api',
        'endpoint': endpoint_name,
        'fetched_at_utc': now_utc.isoformat(),
        'aws_account_id': aws_account_id,
        'schema_version': 'v1',
        'ingestion_id': str(uuid4()),
        'params': params or {},
        'payload': payload,
    }

    put_object_kwargs = {
        'Bucket': bucket_name,
        'Key': key,
        'Body': json.dumps(body).encode('utf-8'),
        'ContentType': 'application/json',
    }

    if get_env_bool('ENABLE_S3_OBJECT_TAGGING', True):
        put_object_kwargs['Tagging'] = _to_tagging_query(_build_upload_tags(endpoint_name))

    get_s3_client().put_object(
        **put_object_kwargs,
    )
    return key


def mark_object_processed(object_key: str, endpoint_name: str = 'unknown') -> None:
    """Mark a raw object as processed=true using S3 object tags."""
    if not get_env_bool('ENABLE_S3_OBJECT_TAGGING', True):
        return

    bucket_name = get_s3_bucket_name()

    get_s3_client().put_object_tagging(
        Bucket=bucket_name,
        Key=object_key,
        Tagging={
            'TagSet': [
                {'Key': 'stage', 'Value': 'raw'},
                {'Key': 'source', 'Value': 'nba_api'},
                {'Key': 'endpoint', 'Value': endpoint_name},
                {'Key': 'processed', 'Value': 'true'},
            ]
        },
    )


def mark_object_unprocessed(object_key: str, endpoint_name: str = 'unknown') -> None:
    """Mark a raw object as processed=false using S3 object tags."""
    if not get_env_bool('ENABLE_S3_OBJECT_TAGGING', True):
        return

    bucket_name = get_s3_bucket_name()

    get_s3_client().put_object_tagging(
        Bucket=bucket_name,
        Key=object_key,
        Tagging={
            'TagSet': [
                {'Key': 'stage', 'Value': 'raw'},
                {'Key': 'source', 'Value': 'nba_api'},
                {'Key': 'endpoint', 'Value': endpoint_name},
                {'Key': 'processed', 'Value': 'false'},
            ]
        },
    )
