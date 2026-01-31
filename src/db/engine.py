import os
import json
import threading
import time
from typing import Optional, List, Tuple, Dict, Any
import logging
from src.db.indexes import IndexManager

logger = logging.getLogger(__name__)

class KVStore:
    def __init__(self, data_dir: str = "data", wal_file: str = "wal.log", snapshot_file: str = "db.snapshot"):
        self.data_dir = data_dir
        self.wal_path = os.path.join(data_dir, wal_file)
        self.snapshot_path = os.path.join(data_dir, snapshot_file)
        
        self._data: Dict[str, Any] = {}
        self.indexer = IndexManager()
        self._lock = threading.RLock()
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.load()

    def load(self):
        """Recover state from snapshot and WAL."""
        with self._lock:
            # 1. Load Snapshot if exists
            if os.path.exists(self.snapshot_path):
                try:
                    with open(self.snapshot_path, "r") as f:
                        self._data = json.load(f)
                        logger.info(f"Loaded snapshot with {len(self._data)} keys.")
                except (json.JSONDecodeError, OSError) as e:
                    logger.error(f"Failed to load snapshot: {e}")
                    self._data = {}

            # 2. Replay WAL
            if os.path.exists(self.wal_path):
                valid_entries = 0
                corrupt_entries = 0
                try:
                    with open(self.wal_path, "r") as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                record = json.loads(line)
                                self._apply_record(record)
                                valid_entries += 1
                            except json.JSONDecodeError:
                                corrupt_entries += 1
                                # Logic: Stop or Skip? Usually stop if strict, but for simple app, maybe skip or just assume tail corruption.
                                logger.warning("Corrupt WAL entry found, ignoring.")
                    logger.info(f"Replayed WAL: {valid_entries} valid, {corrupt_entries} corrupt.")
                except Exception as e:
                     logger.error(f"Error reading WAL: {e}")

    def _apply_record(self, record: Dict[str, Any]):
        """Apply a single record to the in-memory store."""
        op = record.get("op")
        if op == "SET":
            k, v = record["k"], record["v"]
            old_v = self._data.get(k)
            self._data[k] = v
            self.indexer.update(k, v, old_v)
        elif op == "DEL":
            k = record["k"]
            old_v = self._data.get(k)
            self._data.pop(k, None)
            self.indexer.remove(k, old_v)
        elif op == "BULK":
            for k, v in record.get("data", []):
                old_v = self._data.get(k)
                self._data[k] = v
                self.indexer.update(k, v, old_v)

    def _append_wal(self, record: Dict[str, Any], sync: bool = True):
        """Append record to WAL and fsync."""
        try:
            line = json.dumps(record) + "\n"
            with open(self.wal_path, "a") as f:
                f.write(line)
                if sync:
                    f.flush()
                    os.fsync(f.fileno())
            return True
        except Exception as e:
            logger.error(f"WAL write failed: {e}")
            return False

    def get(self, key: str) -> Any:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, value: Any, debug_simulate_error: bool = False) -> bool:
        with self._lock:
            # Simulation of failure (Bonus)
            if debug_simulate_error:
                import random
                if random.random() < 0.01: # 1% chance
                     # Simulate "disk error" or just return False to say it wasn't saved?
                     # Requirements say: "make write calls randomly happen or not (to simulate... issues... Except for WAL since it happens synchronously)"
                     # Actually, the requirement says "Except for WAL since it happens synchronously." 
                     # Wait, if WAL is sync, then we shouldn't fail the WAL write?
                     # The example code shows `_save` checking the parameter.
                     # I will assume this means we pretend the write didn't succeed.
                     return False

            record = {"op": "SET", "k": key, "v": value}
            if self._append_wal(record):
                self._apply_record(record)
                return True
            return False

    def delete(self, key: str) -> bool:
        with self._lock:
            record = {"op": "DEL", "k": key}
            if self._append_wal(record):
                self._apply_record(record)
                return True
            return False

    def bulk_set(self, items: List[Tuple[str, Any]], debug_simulate_error: bool = False) -> bool:
        with self._lock:
            if debug_simulate_error:
                import random
                if random.random() < 0.01:
                    return False
            
            # Atomic: Write one big record.
            record = {"op": "BULK", "data": items}
            if self._append_wal(record):
                self._apply_record(record)
                return True
            return False

    def create_snapshot(self):
        """Compact WAL into a snapshot."""
        with self._lock:
            temp_path = self.snapshot_path + ".tmp"
            try:
                with open(temp_path, "w") as f:
                    json.dump(self._data, f)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_path, self.snapshot_path)
                # Clear WAL
                with open(self.wal_path, "w") as f:
                    f.flush()
                    os.fsync(f.fileno())
                logger.info("Snapshot created and WAL cleared.")
                return True
            except Exception as e:
                logger.error(f"Snapshot creation failed: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return False
