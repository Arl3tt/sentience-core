#!/usr/bin/env python3
"""
sandbox_worker.py

Simple worker that pulls sandbox jobs from Redis and executes them using the
existing sandbox runner. Results are stored back in Redis under
`sandbox:results:<job_id>`.

Run with:
  python -u core/tools/sandbox_worker.py

"""
import time
import argparse
import logging
import os

from core import queue
from core.tools import sandbox_runner

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')


def main(redis_url: str | None = None, sandbox_queue_name: str | None = None, stop_event=None):
    # Log configuration
    logging.info("Starting sandbox worker with config:")
    logging.info("  REDIS_URL: %s", os.environ.get('REDIS_URL'))
    logging.info("  SANDBOX_QUEUE_NAME: %s", os.environ.get('SANDBOX_QUEUE_NAME'))
    logging.info("  SANDBOX_USE_REDIS: %s", os.environ.get('SANDBOX_USE_REDIS'))

    try:
        if redis_url:
            os.environ['REDIS_URL'] = redis_url
        if sandbox_queue_name:
            os.environ['SANDBOX_QUEUE_NAME'] = sandbox_queue_name
        # Write a short worker-start marker to the debug log so tests can see the
        # worker actually started in-process and which Redis instance it will use.
        try:
            with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                dbg.write(
                    f"WORKER START pid={os.getpid()} "
                    f"REDIS_URL={os.environ.get('REDIS_URL')} "
                    f"QUEUE={os.environ.get('SANDBOX_QUEUE_NAME')}\n"
                )
        except Exception:
            pass

        while True:
            if stop_event is not None and getattr(stop_event, 'is_set', lambda: False)():
                logging.info("Stop event set, worker exiting")
                break
            # Log that we're checking for jobs
            logging.debug("Polling queue...")
            try:
                with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                    dbg.write(
                        f"WORKER POLL pid={os.getpid()} -> "
                        f"queue_store: {getattr(queue._get_redis(), '_store', None)}\n"
                    )
            except Exception:
                pass
            try:
                # Mark that the worker is about to call pop_job
                try:
                    with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write(f'WORKER POP_ATTEMPT pid={os.getpid()}\n')
                except Exception:
                    pass

                job = queue.pop_job(block=True, timeout=5)
                try:
                    with open('queue_debug.log', 'a', encoding='utf-8') as dbg:
                        dbg.write(f'WORKER POP_RETURN pid={os.getpid()} job={job}\n')
                except Exception:
                    pass
                if not job:
                    logging.debug("No job found")
                    continue
            except Exception:
                logging.exception("Unhandled error while popping job, continuing")
                time.sleep(0.5)
                continue

            job_id = job.get('id')
            if not isinstance(job_id, str):
                logging.error("Invalid job ID: %s", job_id)
                continue
            command = job.get('command')
            if not isinstance(command, str):
                logging.error("Invalid command for job %s: %s", job_id, command)
                continue

            metadata = job.get('metadata', {})
            logging.info("Got job %s: %s", job_id, command)

            # Execute the command in the sandbox and capture the result
            try:
                timeout = metadata.get('timeout', 30)
                res = sandbox_runner.run_in_sandbox(command, timeout=timeout)
                logging.info("Job %s execution complete: %s", job_id, res)
            except Exception:
                logging.exception("Job %s failed during execution", job_id)
                res = {"status": "error", "error": "execution exception"}

            # Store result
            queue.push_result(job_id, res)
            logging.info("Job %s complete, status=%s", job_id, res.get('status'))

    except KeyboardInterrupt:
        logging.info("Worker shutting down (keyboard interrupt)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--redis-url', help='Redis URL (optional, uses config.REDIS_URL by default)')
    args = parser.parse_args()
    main(args.redis_url)
