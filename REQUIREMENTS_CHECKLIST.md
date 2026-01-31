# Requirements Checklist

## Core Functionality
- [x] **Language**: Python
- [x] **Protocol**: TCP-based (HTTP or custom).
- [x] **Key-Value API**:
  - [x] `Set(key, value)`
  - [x] `Get(key)`
  - [x] `Delete(key)`
  - [x] `BulkSet([(key, value)])`
- [x] **Persistence**: Data persists across restarts.
- [x] **Client**: Python class with `Get`, `Set`, `Delete`, `BulkSet` methods.

## Quality Attributes
- [x] **Durability**: 100% durability (WAL + fsync).
- [x] **Performance**: High write throughput.
- [x] **ACID**: 
  - [x] Atomicity for Bulk Set.
  - [x] Isolation (concurrent writes don't corrupt).

## Testing Scenarios
- [x] **Basic Ops**:
  - [x] Set then Get.
  - [x] Set then Delete then Get.
  - [x] Get without setting.
  - [x] Set then Set (update) then Get.
  - [x] Set then exit (gracefully) then Get.
- [x] **Durability Tests**:
  - [x] Thread 1: Add data + check ack.
  - [x] Thread 2: Kill DB randomly (SIGKILL/-9 simulation).
  - [x] Verify acknowledged keys are present on restart.
- [x] **Concurrency Tests**: 
  - [x] Concurrent Bulk Sets on same keys.
- [x] **Benchmarks**:
  - [x] Write throughput (writes/sec) vs data size.

## Bonus Requirements
- [x] **Simulated Failures**: Debug parameter to simulate simulated filesystem write failures (except WAL).
- [x] **Replication** (Cluster of 3: 1 Primary, 2 Secondary):
  - [x] Replication Primary -> Secondary.
  - [x] Writes/Reads only on Primary.
  - [x] Election/Failover if Primary dies.
- [x] **Indexes**:
  - [x] Inverted index (Full text search on value).
  - [x] Word embedding index.
- [ ] **Master-less Replication**: (Optional/Advanced step).

## Deliverables
- [x] `README.md` (Usage, Install, Test, Troubleshooting).
- [x] `ASSUMPTIONS.md`.
- [x] `project_requirements.txt` (Source).
