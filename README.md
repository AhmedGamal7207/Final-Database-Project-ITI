# NoSQL Key-Value Store

A persistent, distributed key-value store built in Python with support for replication, atomic bulk writes, and basic indexing.

# My Data
Name: Ahmed Gamal Ahmed

Track: AI - Intake 46 - Alexandria

Subject: Final Database Project Submission

## Features

- **Core**: Set, Get, Delete, Bulk Set.
- **Persistence**: Append-only Write Ahead Log (WAL) + Snapshots. 100% Durability.
- **Replication**: Leader-Follower replication (Cluster of 3). Automatic failover.
- **Indexing**: Inverted index (full-text search) and Vector Embeddings on values.
- **ACID**: Atomic Bulk Writes, Serialized isolation.

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Installation

```bash
git clone <repo>
cd final_project
pip install -r requirements.txt
```

## Configuration

Environment variables:
- `DB_PORT`: Port to listen on (default: 8000)
- `DB_DATA_DIR`: Directory for data storage (default: `data`)
- `DB_NODE_ID`: Unique integer ID for the node (default: 0)
- `DB_PEERS`: Comma-separated list of peer URLs for replication.

## Running the Server

### Single Node
```bash
python main.py --port 8000
```

### HOW TO TEST PROJECT
After running
```bash
python main.py --port 8000
```
Navigate to localhost/docs, you will try all operations

### Cluster (3 Nodes)
Run each command in a separate terminal:

Node 0:
```bash
python main.py --port 8000 --node-id 0 --peers http://localhost:8001,http://localhost:8002
```

Node 1:
```bash
python main.py --port 8001 --node-id 1 --peers http://localhost:8000,http://localhost:8002
```

Node 2:
```bash
python main.py --port 8002 --node-id 2 --peers http://localhost:8000,http://localhost:8001
```

## Usage (Python Client)

```python
from src.client.client import DatabaseClient

client = DatabaseClient(port=8000)

# Set
client.set("key", "value")

# Get
print(client.get("key"))

# Bulk Set
client.bulk_set([("k1", "v1"), ("k2", "v2")])

# Delete
client.delete("key")
```

## Testing

Run the automated test suite:

```bash
python -m pytest tests/
```

Individual tests:
- Core functionality: `python -m pytest tests/test_core.py`
- Durability (Kill tests): `python -m pytest tests/test_durability.py`
- Replication (Failover): `python -m pytest tests/test_replication.py`

## Benchmarks

Run the benchmark script:

```bash
python tests/benchmark.py
```

## Troubleshooting

- **No Leader Elected**: Ensure all nodes are running and `peers` arguments are correct (no spaces, valid URLs).
- **Data Dir Locked**: If a process crashes hard, check for leftover `.lock` files (though this implementation relies on process existence).
- **Process Kill**: On Windows, we use `terminate` or `kill`. On Linux, standard signals apply.

## Architecture

- **Server**: FastAPI + Uvicorn.
- **Engine**: In-memory dict backed by append-only WAL.
- **Replication**: Simplified Raft-like Leader Election and Log Replication.
