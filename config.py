from dotenv import load_dotenv
import os
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SANDBOX_ENABLED = True
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
CHROMA_PERSIST = os.getenv('CHROMA_PERSIST', './data/chroma')
EPISODIC_DB = os.getenv('EPISODIC_DB', './data/episodes.sqlite')
SAFE_MODE = os.getenv('SAFE_MODE', 'true').lower() in ('1','true','yes')
# Memory system safety gate - requires confirmation before writing memories
HUMAN_CONFIRM_WRITES = os.getenv('HUMAN_CONFIRM_WRITES', 'false').lower() in ('1','true','yes')
HOST = os.getenv('HOST','127.0.0.1')
PORT = int(os.getenv('PORT','8000'))
if not OPENAI_API_KEY:
    raise EnvironmentError('Set OPENAI_API_KEY in .env')

# Redis-backed sandbox queue configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
# When True, sandbox commands will be enqueued to Redis and run by worker containers
SANDBOX_USE_REDIS = os.getenv('SANDBOX_USE_REDIS', 'false').lower() in ('1','true','yes')
# Queue name and secret key for signing jobs
SANDBOX_QUEUE_NAME = os.getenv('SANDBOX_QUEUE_NAME', 'sandbox:jobs')
SANDBOX_SECRET_KEY = os.getenv('SANDBOX_SECRET_KEY', os.getenv('SECRET_KEY', 'change-me'))
