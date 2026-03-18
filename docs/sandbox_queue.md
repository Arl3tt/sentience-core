# Redis-backed sandbox queue and worker

This repo now includes a lightweight Redis-backed job queue for offloading sandbox runs to worker containers.

Key points:

- Jobs are signed with HMAC using `SANDBOX_SECRET_KEY` to prevent unauthenticated enqueueing.
- The host can enqueue jobs (via `core.queue.enqueue_job`) and workers (service `worker`) will pull and execute them.
- Results are stored in Redis under the key `sandbox:results:<job_id>` and expire after 1 hour.

Environment variables

- `REDIS_URL` - Redis connection string (default: `redis://localhost:6379/0`).
- `REDIS_PASSWORD` - Optional Redis password.
- `SANDBOX_USE_REDIS` - If `true`, `core.tools.sandbox_runner.run_in_sandbox` will enqueue jobs instead of running them locally.
- `SANDBOX_QUEUE_NAME` - Redis list name for jobs (default `sandbox:jobs`).
- `SANDBOX_SECRET_KEY` - Secret used to HMAC-sign jobs. Must be set the same for producers and workers.

Run locally with docker-compose (from repo root):

```powershell
set SANDBOX_SECRET_KEY=your-secret-here
cd docker
docker-compose -f docker-compose.yml up --build
```

This will start a `redis` service and a `worker` service. The `sandbox` service is used by the runner when a job executes inside Docker.

To run the worker alone (without docker-compose), ensure `redis` is reachable, set the env vars and run:

```powershell
set REDIS_URL=redis://localhost:6379/0
set SANDBOX_SECRET_KEY=your-secret-here
python -u core/tools/sandbox_worker.py
```

Notes

- The `docker/seccomp.json` shipped is a conservative profile; depending on the workload you may need to relax syscalls for some tools. Test in a staging environment first.
- The resource limits in `docker/docker-compose.yml` are intentionally conservative (256Mi, 0.5 CPU). Adjust via env or compose if needed.
