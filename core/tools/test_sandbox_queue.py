"""
Integration tests for sandbox queue and worker.

Tests the full flow:
1. Redis queue operations (enqueue, pop, sign/verify)
2. Worker processing of jobs
3. Sandbox execution and result storage
"""
import os
import json
import time
import uuid
import signal
import subprocess
from typing import Generator, AsyncGenerator
import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
import redis

from core import queue as core_queue
from core.tools import sandbox_runner

# Test config - override in env if needed
TEST_REDIS_URL = os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/1')
TEST_QUEUE = f'test:sandbox:jobs:{uuid.uuid4()}'
TEST_SECRET = 'test-secret-key-123'


@pytest.fixture
def redis_conn():
    """Redis connection fixture using test DB."""
    r = redis.Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    # Clear test queue and any results
    r.delete(TEST_QUEUE)
    keys = r.keys('sandbox:results:test:*')
    if keys:
        r.delete(*keys)
    yield r
    # Cleanup
    r.delete(TEST_QUEUE)
    keys = r.keys('sandbox:results:test:*')
    if keys:
        r.delete(*keys)


@pytest.fixture
def queue_config(redis_conn):
    """Configure queue module to use test instance."""
    old_url = os.environ.get('REDIS_URL')
    old_queue = os.environ.get('SANDBOX_QUEUE_NAME')
    old_secret = os.environ.get('SANDBOX_SECRET_KEY')
    old_use_redis = os.environ.get('SANDBOX_USE_REDIS')
    
    os.environ['REDIS_URL'] = TEST_REDIS_URL
    os.environ['SANDBOX_QUEUE_NAME'] = TEST_QUEUE
    os.environ['SANDBOX_SECRET_KEY'] = TEST_SECRET
    os.environ['SANDBOX_USE_REDIS'] = 'true'
    
    # Reset module state
    core_queue._redis = None
    # Ensure module-level config values reflect test env
    try:
        core_queue.SANDBOX_QUEUE_NAME = TEST_QUEUE
        core_queue.SANDBOX_SECRET_KEY = TEST_SECRET
    except Exception:
        pass
    
    yield
    
    if old_url:
        os.environ['REDIS_URL'] = old_url
    else:
        del os.environ['REDIS_URL']
    if old_queue:
        os.environ['SANDBOX_QUEUE_NAME'] = old_queue
    else:
        del os.environ['SANDBOX_QUEUE_NAME']
    if old_secret:
        os.environ['SANDBOX_SECRET_KEY'] = old_secret
    else:
        del os.environ['SANDBOX_SECRET_KEY']
    if old_use_redis:
        os.environ['SANDBOX_USE_REDIS'] = old_use_redis
    else:
        del os.environ['SANDBOX_USE_REDIS']
    
@pytest_asyncio.fixture
async def worker_process(queue_config) -> AsyncGenerator[object, None]:
    """Start a worker in a background thread for test duration (in-process)."""
    import threading
    from core.tools import sandbox_worker

    stop_event = threading.Event()

    # Start worker in a daemon thread so it shares in-process redis stub
    try:
        with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write('FIXTURE before starting worker thread\n')
    except Exception:
        pass

    t = threading.Thread(target=sandbox_worker.main, kwargs={'redis_url': TEST_REDIS_URL, 'sandbox_queue_name': TEST_QUEUE, 'stop_event': stop_event}, daemon=True)
    t.start()

    try:
        with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f'FIXTURE after starting worker thread alive={t.is_alive()} ident={t.ident}\n')
    except Exception:
        pass

    # Give it a moment to initialize
    await asyncio.sleep(1)
    # Write a fixture-side marker so we can see the thread was started
    try:
        with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
            dbg.write(f'FIXTURE started worker thread alive={t.is_alive()} ident={t.ident}\n')
    except Exception:
        pass

    try:
        yield t
    finally:
        try:
            with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(f'FIXTURE teardown setting stop_event alive={t.is_alive()}\n')
        except Exception:
            pass
        stop_event.set()
        t.join(timeout=5)
        try:
            with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(f'FIXTURE teardown worker alive_after_join={t.is_alive()}\n')
        except Exception:
            pass


@pytest.mark.timeout(70)
@pytest.mark.asyncio
async def test_enqueue_and_process(redis_conn, queue_config, worker_process):
    """Test full flow: enqueue job -> worker processes -> check result."""
    # Enqueue a test job
    job_id = core_queue.enqueue_job('python -c "print(\'test-output\')"',
                                  metadata={'test_id': 'test1'})
    
    # Wait for result (up to 30s; Docker sandbox execution takes time)
    result = None
    for _ in range(60):
        result_json = redis_conn.get(f'sandbox:results:{job_id}')
        if result_json:
            result = json.loads(result_json)
            break
        await asyncio.sleep(0.5)
    
    assert result is not None, "No result found"
    assert result['status'] == 'success'
    assert 'test-output' in result['output']
    assert result['code'] == 0


@pytest.mark.timeout(30)
@pytest.mark.asyncio
async def test_invalid_signature(redis_conn, queue_config, worker_process):
    """Test worker rejects jobs with invalid signatures."""
    # Manually push an unsigned job
    job_id = str(uuid.uuid4())
    payload = {
        'id': job_id,
        'command': 'echo bad-job',
        'metadata': {}
    }
    redis_conn.lpush(
        TEST_QUEUE,
        json.dumps({
            'payload': json.dumps(payload),
            'sig': 'invalid-sig'
        })
    )
    
    # Wait a bit - result should never appear
    await asyncio.sleep(2)
    assert redis_conn.get(f'sandbox:results:{job_id}') is None


@pytest.mark.timeout(70)
@pytest.mark.asyncio
async def test_job_timeout(redis_conn, queue_config, worker_process):
    """Test jobs that exceed their timeout."""
    job_id = core_queue.enqueue_job(
        'python -c "import time; time.sleep(10)"',
        metadata={'timeout': 1}  # 1s timeout
    )
    
    # Wait for result (up to 30s; Docker sandbox execution takes time)
    result = None
    for _ in range(60):
        result_json = redis_conn.get(f'sandbox:results:{job_id}')
        if result_json:
            result = json.loads(result_json)
            break
        await asyncio.sleep(0.5)
    
    assert result is not None, "No result found"
    assert result['status'] == 'timeout'


@pytest.mark.timeout(70)
@pytest.mark.asyncio
async def test_concurrent_jobs(redis_conn, queue_config, worker_process):
    """Test multiple jobs can be processed."""
    job_ids = []
    for i in range(3):
        job_id = core_queue.enqueue_job(
            f'python -c "print(\'job-{i}\')"',
            metadata={'job_num': i}
        )
        job_ids.append(job_id)
    
    # Wait for all results (up to 60s; Docker sandbox execution takes time)
    results = {}
    for _ in range(120):  # 60 seconds max
        for job_id in job_ids:
            if job_id not in results:
                result_json = redis_conn.get(f'sandbox:results:{job_id}')
                if result_json:
                    results[job_id] = json.loads(result_json)
        if len(results) == len(job_ids):
            break
        await asyncio.sleep(0.5)
    
    assert len(results) == len(job_ids), "Not all jobs completed"
    for job_id in job_ids:
        assert results[job_id]['status'] == 'success'