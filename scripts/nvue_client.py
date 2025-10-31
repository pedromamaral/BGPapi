#!/usr/bin/env python3
import requests
import json
import time
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NVUEClient:
    """
    Client for interacting with NVUE REST API on Cumulus Linux switches
    """
    
    def __init__(self, host, username=None, password=None):
        """
        Initialize NVUE client
        
        Args:
            host: Switch IP address or hostname
            username: NVUE username (default: cumulus)
            password: NVUE password (default: cgrlab2)
        """
        self.username = username or os.getenv('CUMULUS_USER', 'cumulus')
        self.password = password or os.getenv('CUMULUS_PASSWORD', 'cgrlab2')
        self.auth = (self.username, self.password)
        self.host = host
        self.base_url = f"https://{host}:8765/nvue_v1"
        self.headers = {"Content-Type": "application/json"}
        
        # Test connection on init
        self._test_connection()
    
    def _test_connection(self):
        """Test if we can connect to the API"""
        try:
            r = requests.get(
                url=self.base_url,
                auth=self.auth,
                verify=False,
                timeout=5
            )
            if r.status_code == 200:
                print(f"✓ Connected to {self.host}")
            elif r.status_code == 401:
                raise Exception(f"Authentication failed on {self.host}. Check credentials.")
            else:
                raise Exception(f"Unexpected response: HTTP {r.status_code}")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to {self.host}:8765")
    
    def create_revision(self):
        """
        Create a new configuration revision
        
        Returns:
            revision_id: The ID of the new revision
        """
        try:
            r = requests.post(
                url=f"{self.base_url}/revision",
                auth=self.auth,
                verify=False,
                timeout=10
            )
            
            if r.status_code not in [200, 201]:
                print(f"ERROR: Failed to create revision")
                print(f"Status: {r.status_code}")
                print(f"Response: {r.text}")
                raise Exception(f"Failed to create revision: HTTP {r.status_code}")
            
            response = r.json()
            revision_id = list(response.keys())[0]
            return revision_id
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Connection error when creating revision")
            print(f"Details: {str(e)}")
            raise
    
    def patch_config(self, revision, payload, path="/"):
        """
        Apply configuration changes to a revision
        
        Args:
            revision: Revision ID
            payload: Configuration payload (dict)
            path: API path (default: "/")
        
        Returns:
            response object
        """
        try:
            query = {"rev": revision}
            
            r = requests.patch(
                url=f"{self.base_url}{path}",
                auth=self.auth,
                verify=False,
                data=json.dumps(payload),
                params=query,
                headers=self.headers,
                timeout=30
            )
            
            if r.status_code not in [200, 204]:
                print(f"ERROR: Patch failed with HTTP {r.status_code}")
                print(f"Response: {r.text}")
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Connection error during patch")
            print(f"Details: {str(e)}")
            raise
    
    def apply_revision(self, revision):
        """
        Apply a revision to make changes active
        
        Args:
            revision: Revision ID to apply
        
        Returns:
            True if successful, False otherwise
        """
        try:
            apply_payload = {
                "state": "apply",
                "auto-prompt": {"ays": "ays_yes"}
            }
            
            url = f"{self.base_url}/revision/{revision}"
            r = requests.patch(
                url=url,
                auth=self.auth,
                verify=False,
                data=json.dumps(apply_payload),
                headers=self.headers,
                timeout=30
            )
            
            if r.status_code not in [200, 201]:
                print(f"ERROR: Apply failed with HTTP {r.status_code}")
                print(f"Response: {r.text}")
                return False
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Connection error during apply")
            print(f"Details: {str(e)}")
            raise
    
    def wait_for_apply(self, revision, retries=30, delay=2):
        """
        Wait for a revision to be fully applied
        
        Args:
            revision: Revision ID to monitor
            retries: Number of retries (default: 30)
            delay: Delay between retries in seconds (default: 2)
        
        Returns:
            True if applied successfully, False if timeout or error
        """
        for attempt in range(retries):
            try:
                r = requests.
