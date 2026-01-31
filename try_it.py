import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_demo():
    print(f"Connecting to {BASE_URL}...")
    
    # 1. Set a key
    print("\n1. Setting key 'my_key' to 'Hello World'...")
    resp = requests.post(f"{BASE_URL}/set", json={"key": "my_key", "value": "Hello World"})
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")

    # 2. Get the key
    print("\n2. Getting key 'my_key'...")
    resp = requests.get(f"{BASE_URL}/get/my_key")
    print(f"   Response: {resp.json()}")

    # 3. Bulk Set
    print("\n3. Bulk setting user data...")
    users = [
        ("user:1", {"name": "Alice", "role": "admin"}),
        ("user:2", {"name": "Bob", "role": "dev"}),
        ("user:3", {"name": "Charlie", "role": "manager"})
    ]
    resp = requests.post(f"{BASE_URL}/bulk", json={"items": users})
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.json()}")

    # 4. Get one of the users
    print("\n4. Getting key 'user:2'...")
    resp = requests.get(f"{BASE_URL}/get/user:2")
    print(f"   Response: {resp.json()}")

    # 5. Delete a key
    print("\n5. Deleting key 'my_key'...")
    resp = requests.delete(f"{BASE_URL}/delete/my_key")
    print(f"   Status: {resp.status_code}")
    
    # 6. Verify deletion
    print("\n6. Verifying deletion...")
    resp = requests.get(f"{BASE_URL}/get/my_key")
    if resp.status_code == 404:
        print("   Success! Key not found (404).")
    else:
        print(f"   Unexpected: {resp.json()}")

if __name__ == "__main__":
    try:
        run_demo()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running on port 8000?")
