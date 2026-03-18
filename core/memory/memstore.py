# memstore: episodic sqlite + semantic embeddings with chroma fallback
import os
import sqlite3
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from config import CHROMA_PERSIST
from config import EPISODIC_DB
MODEL = SentenceTransformer('all-MiniLM-L6-v2')

USE_CHROMA = True
try:
    import chromadb
    from chromadb.config import Settings
    client = chromadb.Client(Settings(chroma_db_impl='duckdb+parquet', persist_directory=CHROMA_PERSIST))
    COLLECTION = 'copilot_memory'
    try:
        collection = client.get_collection(COLLECTION)
    except Exception:
        collection = client.create_collection(COLLECTION)
except Exception as e:
    print('[memstore] chroma init failed, falling back to sqlite', e)
    USE_CHROMA = False
    collection = None

if not os.path.exists('data'):
    os.makedirs('data', exist_ok=True)
conn = sqlite3.connect(EPISODIC_DB, check_same_thread=False)
cur = conn.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT,
    content TEXT,
    metadata TEXT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
)""")
conn.commit()

# Ensure schema includes expected columns (migrate older DBs used by tests)
cur.execute("PRAGMA table_info('episodes')")
cols = [r[1] for r in cur.fetchall()]
if 'role' not in cols:
    try:
        cur.execute("ALTER TABLE episodes ADD COLUMN role TEXT")
        conn.commit()
    except Exception:
        pass
if 'metadata' not in cols:
    try:
        cur.execute("ALTER TABLE episodes ADD COLUMN metadata TEXT")
        conn.commit()
    except Exception:
        pass

WORKING_MEMORY = []


def add_episode(role, content, metadata=None):
    meta = json.dumps(metadata or {})
    cur.execute('INSERT INTO episodes (role, content, metadata) VALUES (?, ?, ?)', (role, content, meta))
    conn.commit()
    WORKING_MEMORY.append({'role': role, 'content': content, 'meta': metadata})
    return True


def ingest_document(doc_id, text, metadata=None):
    emb = MODEL.encode(text).astype(np.float32).tolist()
    if USE_CHROMA and collection:
        collection.add(ids=[doc_id], documents=[text], metadatas=[metadata or {}], embeddings=[emb])
        add_episode('ingest', f'ingested {doc_id}', {'doc_id': doc_id})
        return {'status': 'ok', 'id': doc_id}
    else:
        add_episode('ingest_fallback', f'ingested_fallback {doc_id}', metadata or {})
        cur.execute('INSERT INTO episodes (role, content, metadata) VALUES (?, ?, ?)',
                    ('doc', text, json.dumps(metadata or {})))
        conn.commit()
        return {'status': 'ok', 'id': cur.lastrowid}


def semantic_search(query, top_k=5):
    qv = MODEL.encode(query)
    if USE_CHROMA and collection:
        qv_list = qv.astype(np.float32).tolist()
        try:
            res = collection.query(query_embeddings=[qv_list], n_results=top_k, include=['documents', 'metadatas'])
            hits = []
            if res is not None and isinstance(res, dict):
                docs = res.get('documents', [])
                metas = res.get('metadatas', [])
                if docs and isinstance(docs, list) and len(docs) > 0 and isinstance(docs[0], list):
                    for i in range(len(docs[0])):
                        hit = {
                            'id': str(i),
                            'doc': docs[0][i],
                            'meta': metas[0][i] if metas and len(metas) > 0 else {}
                        }
                        hits.append(hit)
        except Exception as e:
            print(f"Error in chromadb query: {e}")
            hits = []
        return hits
    else:
        cur.execute('SELECT id, content FROM episodes ORDER BY id DESC LIMIT 400')
        rows = cur.fetchall()
        scored = []
        qv_np = qv.astype(np.float32)
        for r in rows:
            text = r[1]
            emb = MODEL.encode(text).astype(np.float32)
            score = float(np.dot(qv_np, emb) / (np.linalg.norm(qv_np)*np.linalg.norm(emb)+1e-8))
            scored.append((score, r[0], text))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{'id': s[1], 'doc': s[2], 'score': float(s[0])} for s in scored[:top_k]]
