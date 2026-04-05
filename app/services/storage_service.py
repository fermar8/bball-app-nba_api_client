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


def _params_hash(params: dict | None) -> str:
    return hashlib.sha256(_serialize_for_hash(params).encode('utf-8')).hexdigest()[:8]


def _build_object_key(endpoint_name: str, now_utc: datetime, params: dict | None) -> str:
    """Build partitioned S3 object key optimized for incremental processing."""
    request_hash = _params_hash(params)
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


def upload_raw_payload(endpoint_name: str, payload: dict | list, params: dict | None = None, source: str = 'nba_api') -> str:
    bucket_name = get_s3_bucket_name()
    aws_account_id = get_aws_account_id()
    now_utc = datetime.now(timezone.utc)
    key = _build_object_key(endpoint_name=endpoint_name, now_utc=now_utc, params=params)

    body = {
        'source': source,
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
        tags = _build_upload_tags(endpoint_name)
        tags['source'] = source
        put_object_kwargs['Tagging'] = _to_tagging_query(tags)

    get_s3_client().put_object(
        **put_object_kwargs,
    )
    return key


def get_latest_endpoint_payload(endpoint_name: str, params: dict | None = None) -> tuple[dict | list, str]:
    bucket_name = get_s3_bucket_name()
    prefix = f'raw/{endpoint_name}/'

    listing = get_s3_client().list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    contents = listing.get('Contents', [])
    if params is not None:
        expected_hash = _params_hash(params)
        contents = [
            item
            for item in contents
            if str(item.get('Key', '')).endswith(f'_{expected_hash}.json')
        ]
    if not contents:
        raise FileNotFoundError(f'No persisted payloads found for endpoint: {endpoint_name}')

    latest = max(contents, key=lambda item: item.get('LastModified', datetime.min.replace(tzinfo=timezone.utc)))
    object_key = latest['Key']

    obj = get_s3_client().get_object(Bucket=bucket_name, Key=object_key)
    raw_body = obj['Body'].read().decode('utf-8')
    parsed = json.loads(raw_body)
    payload = parsed.get('payload')
    if payload is None:
        raise ValueError(f'Persisted object has no payload field: {object_key}')
    return payload, object_key


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
