import requests
from typing import Any, List, Tuple, Optional

class DatabaseClient:
    """
    Client for the NoSQL KV Store.
    
    Args:
        host (str): Database host (default: localhost).
        port (int): Database port (default: 8000).
    """

    def __init__(self, host: str = "localhost", port: int = 8000):
        self.base_url = f"http://{host}:{port}"
        self.session = requests.Session()

    def get(self, key: str) -> Any:
        """
        Retrieve a value by key.
        
        Args:
            key (str): The key to retrieve.
            
        Returns:
            Any: The value if found, or None if not found.
        """
        try:
            resp = self.session.get(f"{self.base_url}/get/{key}")
            if resp.status_code == 200:
                return resp.json()["value"]
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
        except requests.RequestException:
            return None

    def set(self, key: str, value: Any, debug: bool = False) -> bool:
        """
        Set a key-value pair.
        
        Args:
            key (str): The key.
            value (Any): The value (must be JSON serializable).
            debug (bool): If True, simulate random write failure.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            payload = {"key": key, "value": value, "debug": debug}
            resp = self.session.post(f"{self.base_url}/set", json=payload)
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key.
        
        Args:
            key (str): The key to delete.
            
        Returns:
            bool: True if operation received (even if key didn't exist).
        """
        try:
            resp = self.session.delete(f"{self.base_url}/delete/{key}")
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def bulk_set(self, items: List[Tuple[str, Any]], debug: bool = False) -> bool:
        """
        Set multiple key-value pairs atomically.
        
        Args:
            items (List[Tuple[str, Any]]): List of (key, value) tuples.
            debug (bool): If True, simulate random write failure.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            payload = {"items": items, "debug": debug}
            resp = self.session.post(f"{self.base_url}/bulk", json=payload)
            resp.raise_for_status()
            return True
        except requests.RequestException:
            return False
