from fastapi import FastAPI, HTTPException, Body, Request
from pydantic import BaseModel
from typing import Any, List, Optional, Tuple
import uvicorn
import os
import signal
import sys
import asyncio
from src.db.engine import KVStore
from src.db.replication import ReplicationManager, Role

app = FastAPI(title="NoSQL KV Store")

# Configuration
data_dir = os.getenv("DB_DATA_DIR", "data")
node_id = int(os.getenv("DB_NODE_ID", "0"))
peers_str = os.getenv("DB_PEERS", "")
peers = [p.strip() for p in peers_str.split(",")] if peers_str else []

db = KVStore(data_dir=data_dir)
repl_manager = None

@app.on_event("startup")
async def startup_event():
    global repl_manager
    repl_manager = ReplicationManager(node_id, peers, db)
    # If no peers, we are effectively a single node leader
    if not peers:
        repl_manager.role = Role.LEADER
    else:
        # Start monitoring loop
        await repl_manager.start()

class SetRequest(BaseModel):
    key: str
    value: Any
    debug: Optional[bool] = False

class BulkSetRequest(BaseModel):
    items: List[Tuple[str, Any]]
    debug: Optional[bool] = False

# --- Middleware / Dependency to check Leader ---
def ensure_leader():
    if repl_manager.role != Role.LEADER:
        raise HTTPException(status_code=503, detail=f"Not Leader. Current Leader: {repl_manager.leader}")

# --- Client Operations ---

@app.get("/get/{key}")
async def get_key(key: str):
    ensure_leader()
    val = db.get(key)
    if val is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"key": key, "value": val}

@app.post("/set")
async def set_key(req: SetRequest):
    ensure_leader()
    success = db.set(req.key, req.value, debug_simulate_error=req.debug)
    if not success:
        raise HTTPException(status_code=500, detail="Write failed")
    
    # Replicate
    await repl_manager.replicate_to_peers({"op": "SET", "k": req.key, "v": req.value})
    
    return {"status": "ok", "key": req.key}

@app.delete("/delete/{key}")
async def delete_key(key: str):
    ensure_leader()
    success = db.delete(key)
    # Replicate
    if success:
        await repl_manager.replicate_to_peers({"op": "DEL", "k": key})
    return {"status": "ok", "key": key}

@app.post("/bulk")
async def bulk_set(req: BulkSetRequest):
    ensure_leader()
    success = db.bulk_set(req.items, debug_simulate_error=req.debug)
    if not success:
        raise HTTPException(status_code=500, detail="Bulk write failed")
    
    # Replicate
    await repl_manager.replicate_to_peers({"op": "BULK", "data": req.items})
    
    return {"status": "ok", "count": len(req.items)}

@app.post("/snapshot")
def manual_snapshot():
    ensure_leader()
    if db.create_snapshot():
        return {"status": "ok"}
    raise HTTPException(status_code=500, detail="Snapshot failed")

# --- Internal Replication Endpoints ---

@app.post("/internal/heartbeat")
async def receive_heartbeat(payload: dict = Body(...)):
    repl_manager.receive_heartbeat(payload["term"], payload["leader_id"])
    return {"status": "ok"}

@app.post("/internal/vote")
async def receive_vote(payload: dict = Body(...)):
    granted = repl_manager.receive_vote_request(payload["term"], payload["candidate_id"])
    return {"vote_granted": granted}

@app.post("/internal/replicate")
async def receive_replication(record: dict = Body(...)):
    # Direct apply to DB (bypass leader check as we are follower receiving from leader)
    # Note: validation that it came from leader is skipped for simplicity
    db._apply_record(record)
    # Also persist to WAL on secondary for durability!
    db._append_wal(record, sync=True)
    return {"status": "ack"}

# --- Utils ---

@app.post("/shutdown")
def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting_down"}

@app.get("/debug/info")
def debug_info():
    return {
        "node_id": node_id,
        "role": repl_manager.role.value,
        "leader": repl_manager.leader,
        "term": repl_manager.term,
        "peers": peers
    }

@app.get("/")
def root():
    return {
        "message": "NoSQL KV Store is running",
        "node_id": node_id,
        "role": repl_manager.role.value if repl_manager else "Unknown",
        "docs": "/docs"
    }

def run_server(host="0.0.0.0", port=8000):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run_server()
