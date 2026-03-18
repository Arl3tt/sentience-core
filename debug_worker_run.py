import threading, time, json, os
from core import queue
from core.tools import sandbox_worker

os.environ['REDIS_URL'] = 'redis://localhost:6379/1'
os.environ['SANDBOX_QUEUE_NAME'] = 'test_queue'
os.environ['SANDBOX_SECRET_KEY'] = 'test-secret-key-123'
os.environ['SANDBOX_USE_REDIS'] = 'true'

queue._redis = None
stop_event = threading.Event()

thr = threading.Thread(target=sandbox_worker.main, kwargs={'redis_url':None,'stop_event':stop_event}, daemon=True)
thr.start()

# Give worker time
time.sleep(0.5)
job_id = queue.enqueue_job('python -c "print(\'hello\')"', metadata={'test_id':'1'})
print('enqueued', job_id)

# poll for result
r = queue._get_redis()
for i in range(20):
    v = r.get(f'sandbox:results:{job_id}')
    print('poll', i, v)
    if v:
        print('got', v)
        break
    time.sleep(0.5)

stop_event.set()
thr.join(timeout=2)
print('done')
