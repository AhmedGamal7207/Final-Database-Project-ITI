# Assumptions and Decisions

## General
- **OS Compatibility**: The development environment is Windows. "SIGKILL (-9)" is a Unix concept. On Windows, we will use `subprocess.Popen.kill()` which creates a hard termination similar to SIGKILL.
- **Python Version**: Python 3.10+ will be used.

## Architecture
- **Communication Protocol**: HTTP via REST API using `FastAPI` and `Uvicorn`.
  - *Reason*: Meets "TCP (HTTP is ok)" requirement, provides robust "production-quality" validation (Pydantic), and is easy to start with. We can optimize loop/workers for throughput.
- **Persistence**: 
  - **WAL (Write Ahead Log)**: Append-only file for all modify operations. Flushed to disk (`os.fsync`) before acknowledging the client.
  - **Snapshot**: Occasional saving of the full KV dump to speed up startup.
  - **In-Memory Store**: Python `dict` for O(1) reads.
- **Concurrency**:
  - `asyncio` for the server to handle concurrent connections efficiently.
  - Explicit locking (`asyncio.Lock`) around Critical Sections (Write operations) to ensure ACID properties for BulkSet and avoid race conditions.

## Replication (Bonus)
- **Consensus**: We will implement a simplified Primary-Backup replication.
- **Election**: A simple heartbeat/timeout mechanism. If heartbeat fails, highest Node ID becomes Primary (Bully algorithm or simplistic preference) for simplicity, or we check who has the latest WAL.

## Indexing (Bonus)
- **Full Text**: Simple inverted index mapping token -> set of keys. Updated synchronously or asynchronously depending on impact.
- **Word Embedding**: We will use a lightweight library or simple mock if a full ML model is too heavy for the scope, but requirements imply standard usage. We might use `sentence-transformers` if allowed, otherwise a simple bag-of-words or random vectors for strict demonstration if model loading is too slow. *Decision*: Will try to use a small pre-trained model if possible, or a basic hash-based embedding for purely functional demo if libraries are heavy.

## Testing
- Tests will launch the server as a subprocess to be able to kill it externally.
