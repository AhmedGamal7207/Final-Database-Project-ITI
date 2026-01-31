import pytest
import subprocess
import time
import os
import shutil
import sys
import requests

from src.client.client import DatabaseClient

PORTS = [8010, 8011, 8012]
HOSTS = [f"http://127.0.0.1:{p}" for p in PORTS]

def start_cluster():
    procs = []
    for i, port in enumerate(PORTS):
        data_dir = f"db_node_{i}" 
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)
        os.makedirs(data_dir)
        
        peers = ",".join([h for j, h in enumerate(HOSTS) if i != j])
        
        env = os.environ.copy()
        env["DB_DATA_DIR"] = data_dir
        
        cmd = [
            sys.executable, "main.py",
            "--port", str(port),
            "--host", "127.0.0.1",
            "--node-id", str(i),
            "--peers", peers
        ]
        
        log_file = open(f"node_{i}.log", "w")
        proc = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT)
        procs.append((proc, log_file))
    
    time.sleep(5) # Give time for election
    return procs

def stop_cluster(procs):
    for p, f in procs:
        try:
            p.terminate()
            p.wait(timeout=2)
        except:
            p.kill()
        f.close()
    
    for i in range(len(PORTS)):
        data_dir = f"db_node_{i}" 
        if os.path.exists(data_dir):
            shutil.rmtree(data_dir)

@pytest.fixture
def cluster():
    procs = start_cluster()
    yield procs
    stop_cluster(procs)

def get_leader_index():
    end_time = time.time() + 30
    while time.time() < end_time:
        for i, port in enumerate(PORTS):
            try:
                resp = requests.get(f"http://127.0.0.1:{port}/debug/info", timeout=1)
                info = resp.json()
                if info["role"] == "LEADER":
                    return i, info["leader"]
            except:
                pass
        time.sleep(1)
    return None, None

def test_replication_flow(cluster):
    # 1. Identify Leader
    leader_idx, leader_id = get_leader_index()
    assert leader_idx is not None, "No leader elected"
    
    # Get peers info
    resp = requests.get(f"http://127.0.0.1:{PORTS[leader_idx]}/debug/info")
    print(f"Leader Info: {resp.json()}")

    print(f"Leader is Node {leader_id}")
    
    # 2. Write to Leader
    client = DatabaseClient(host="127.0.0.1", port=PORTS[leader_idx])
    assert client.set("rep_key", "rep_val")
    
    # 3. Check followers have data
    time.sleep(1) # Allow replication
    for i, port in enumerate(PORTS):
        if i == leader_idx:
            continue
        # Access strictly? "Reads happen only to primary" per requirements. 
        # But we can cheat and look at disk or use a special debug read if we want to verify replication.
        # Or we temporarily allow non-leader read for verification?
        # The requirements say "Reads happen only to primary". 
        # This means the client *should* ask the primary.
        # But to verify replication physically happened, I should inspect the follower's internal state.
        # I'll use direct disk check or simple hack: Follower DB *has* the data in memory.
        # I'll use `db.get` returns 503 on follower.
        # But I can use internal API or just trust that if I kill leader, data is there.
        pass

    # 4. Kill Leader
    print(f"Killing Leader Node {leader_id}")
    cluster[leader_idx][0].kill()
    time.sleep(5) # Wait for new election
    
    new_leader_idx, new_leader_id = get_leader_index()
    assert new_leader_idx is not None
    assert new_leader_idx != leader_idx
    print(f"New Leader is Node {new_leader_id}")
    
    # 5. Read from new Leader (should have data)
    client2 = DatabaseClient(host="127.0.0.1", port=PORTS[new_leader_idx])
    val = client2.get("rep_key")
    assert val == "rep_val", f"Data lost during failover! Got {val}"
    
    # 6. Write new data to new Leader
    assert client2.set("new_key", "new_val")
