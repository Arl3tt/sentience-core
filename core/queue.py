"""
Lightweight Redis-backed job queue for sandbox tasks.

Jobs are simple JSON objects with an HMAC signature to ensure only
producers that know the secret can enqueue meaningful jobs.

API:
 - enqueue_job(command: str, metadata: dict=None) -> job_id
 - pop_job(block: bool=True, timeout: int=0) -> dict | None

"""
import json
import os
import hmac
import hashlib
import uuid
import time
import logging
from typing import Optional, List, Any, Dict, Tuple, Union, cast

import redis
from redis.client import Redis
from redis.typing import KeyT

from config import REDIS_URL, REDIS_PASSWORD, SANDBOX_QUEUE_NAME, SANDBOX_SECRET_KEY


_redis: Optional[Redis] = None


def _get_redis():
    global _redis
    if _redis is None:
        retries = 3
        retry_delay = 1.0
        last_error = None

        logging.info("Initializing Redis connection")
        for attempt in range(retries):
            try:
                # Use from_url if URL provided, otherwise fallback to host/port env style
                if REDIS_URL:
                    _redis = redis.Redis.from_url(REDIS_URL, password=REDIS_PASSWORD, decode_responses=True)
                else:
                    _redis = redis.Redis(decode_responses=True)

                # Test the connection
                _redis.ping()
                logging.info("Successfully connected to Redis")
                break

            except Exception as e:
                last_error = e
                if attempt < retries - 1:
                    logging.warning("Redis connection attempt %d failed: %s. Retrying in %.1f seconds...",
                                 attempt + 1, str(e), retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logging.error("Failed to connect to Redis after %d attempts: %s", retries, str(e))
                    raise RuntimeError(f"Failed to connect to Redis: {str(e)}") from last_error
    return _redis


def _sign(payload: str) -> str:
    return hmac.new(SANDBOX_SECRET_KEY.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()


def enqueue_job(command: str, metadata: Optional[dict] = None) -> str:
    """Enqueue a sandbox job and return a job id."""
    logging.info("Creating new sandbox job with command: %s", command)
    job_id = str(uuid.uuid4())
    payload = {
        "id": job_id,
        "command": command,
        "metadata": metadata or {},
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    sig = _sign(payload_json)
    item = json.dumps({"payload": payload_json, "sig": sig})
    r = _get_redis()
    if r is None:
        raise RuntimeError("Redis connection not available")
    try:
        r.lpush(SANDBOX_QUEUE_NAME, item)
        logging.info("Successfully enqueued job %s", job_id)
        return job_id
    except Exception as e:
        logging.error("Failed to enqueue job %s: %s", job_id, str(e))
        raise


def pop_job(block: bool = True, timeout: int = 0) -> Optional[dict]:
    """Pop a job from Redis. Returns the payload dict or None if none available."""
    logging.debug("Attempting to pop job (block=%s, timeout=%d)", block, timeout)
    r = _get_redis()
    if r is None:
        logging.error("Redis connection not available")
        return None

    try:
        if block:
            try:
                # Explicitly handle the Redis response format and typing
                response: Optional[Tuple[bytes, bytes]] = cast(Optional[Tuple[bytes, bytes]], r.brpop([SANDBOX_QUEUE_NAME], timeout=timeout))
                if not response:
                    logging.debug("No job available after blocking")
                    return None
                # Response is a tuple of (queue_name, item)
                _, item_bytes = response
                item = item_bytes.decode('utf-8')
            except Exception as e:
                logging.error("Error in brpop: %s", str(e))
                return None
        else:
            # rpop returns str since we use decode_responses=True
            item = cast(Optional[str], r.rpop(SANDBOX_QUEUE_NAME))
            if not item:
                logging.debug("No job available")
                return None

        # At this point item is guaranteed to be str
        obj: Dict[str, Any] = json.loads(item)
        payload_json = obj.get('payload')
        sig = obj.get('sig')

        if not payload_json or not sig:
            logging.warning("Invalid job format: missing payload or signature")
            return None

        expected = _sign(payload_json)
        if not hmac.compare_digest(expected, sig):
            logging.warning("Invalid job signature")
            return None

        payload = json.loads(payload_json)
        logging.info("Successfully popped job %s", payload.get('id'))
        return payload

    except Exception as e:
        logging.error("Error popping job: %s", str(e))
        return None


def push_result(job_id: str, result: dict) -> None:
    """Store result under sandbox:results:<job_id> (expires after some time)."""
    logging.info("Storing result for job %s: %s", job_id, result)
    r = _get_redis()
    if r is None:
        raise RuntimeError("Redis connection not available")
    key = f"sandbox:results:{job_id}"
    try:
        r.set(key, json.dumps(result), ex=3600)
        logging.info("Successfully stored result for job %s", job_id)
    except Exception as e:
        logging.error("Failed to store result for job %s: %s", job_id, str(e))
        raise
