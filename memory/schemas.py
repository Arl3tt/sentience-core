# memory/schemas.py
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import time, uuid

@dataclass
class MemoryRecord:
    id: str
    text: str
    embedding_meta: Dict[str, Any]
    meta: Dict[str, Any]
    ts: float

    @staticmethod
    def create(text: str, meta: Optional[Dict]=None, embedding_meta: Optional[Dict]=None):
        return MemoryRecord(
            id=str(uuid.uuid4()),
            text=text,
            embedding_meta=embedding_meta or {},
            meta=meta or {},
            ts=time.time()
        )

    def to_dict(self):
        d = asdict(self)
        # ensure JSON serializable
        d["ts"] = float(self.ts)
        return d