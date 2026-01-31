import pytest
import subprocess
import time
import os
import shutil
import sys
from src.client.client import DatabaseClient

DB_PORT = 8001
DATA_DIR = "test_data_core"

def start_server():
    env = os.environ.copy()
    env["DB_DATA_DIR"] = DATA_DIR
    # Run the module to ensure imports work
    proc = subprocess.Popen(
        [sys.executable, "main.py", "--port", str(DB_PORT)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2) # Wait for startup
    return proc

def stop_server(proc):
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()

@pytest.fixture(scope="module")
def server():
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
    os.makedirs(DATA_DIR)
    
    proc = start_server()
    yield proc
    stop_server(proc)
    # Cleanup after all tests
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)

@pytest.fixture
def client():
    return DatabaseClient(port=DB_PORT)

def test_set_get(server, client):
    assert client.set("foo", "bar")
    assert client.get("foo") == "bar"

def test_set_delete_get(server, client):
    assert client.set("del_me", "val")
    assert client.delete("del_me")
    assert client.get("del_me") is None

def test_get_non_existent(server, client):
    assert client.get("missing") is None

def test_set_update_get(server, client):
    client.set("update_key", "val1")
    assert client.get("update_key") == "val1"
    client.set("update_key", "val2")
    assert client.get("update_key") == "val2"

def test_bulk_set(server, client):
    items = [("k1", "v1"), ("k2", "v2"), ("k3", "v3")]
    assert client.bulk_set(items)
    assert client.get("k1") == "v1"
    assert client.get("k2") == "v2"
    assert client.get("k3") == "v3"

def test_persistence_restart():
    # This test needs to control the server restart manually, so we don't use the module fixture
    # We use a unique data dir for this test
    local_data_dir = "test_data_persist"
    if os.path.exists(local_data_dir):
        shutil.rmtree(local_data_dir)
    os.makedirs(local_data_dir)

    env = os.environ.copy()
    env["DB_DATA_DIR"] = local_data_dir
    
    # 1. Start Server
    proc = subprocess.Popen([sys.executable, "main.py", "--port", "8002"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    try:
        c = DatabaseClient(port=8002)
        c.set("persist_key", "persist_val")
        assert c.get("persist_key") == "persist_val"
    finally:
        # 2. Stop Server (Graceful)
        proc.terminate()
        proc.wait()
    
    time.sleep(1)

    # 3. Restart Server
    proc = subprocess.Popen([sys.executable, "main.py", "--port", "8002"], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    try:
        c = DatabaseClient(port=8002)
        # 4. Get data
        assert c.get("persist_key") == "persist_val"
    finally:
        proc.terminate()
        proc.wait()
        if os.path.exists(local_data_dir):
            shutil.rmtree(local_data_dir)

