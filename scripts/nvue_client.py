#!/usr/bin/env python3
import requests
import json
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NVUEClient:
    def __init__(self, host, username="cumulus", password="cumulus"):
        self.auth = (username, password)
        self.base_url = f"https://{host}:8765/nvue_v1"
        self.headers = {"Content-Type": "application/json"}
        
    def create_revision(self):
        """Create a new configuration revision"""
        r = requests.post(
            url=f"{self.base_url}/revision",
            auth=self.auth,
            verify=False
        )
        response = r.json()
        return list(response.keys())[0]
    
    def patch_config(self, revision, payload, path="/"):
        """Apply configuration changes"""
        query = {"rev": revision}
        r = requests.patch(
            url=f"{self.base_url}{path}",
            auth=self.auth,
            verify=False,
            data=json.dumps(payload),
            params=query,
            headers=self.headers
        )
        print(f"Patch response: {r.status_code}")
        if r.status_code not in [200, 204]:
            print(f"Error: {r.text}")
        return r
    
    def apply_revision(self, revision):
        """Apply the revision"""
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
            headers=self.headers
        )
        return r
    
    def wait_for_apply(self, revision, retries=30):
        """Wait for configuration to be applied"""
        for i in range(retries):
            r = requests.get(
                url=f"{self.base_url}/revision/{revision}",
                auth=self.auth,
                verify=False
            )
            response = r.json()
            state = response.get("state")
            print(f"Revision state: {state}")
            if state == "applied":
                return True
            elif state == "apply_failed":
                print(f"Apply failed: {response}")
                return False
            time.sleep(2)
        return False
    
    def get_config(self, path="/", revision="applied"):
        """Get current configuration"""
        r = requests.get(
            url=f"{self.base_url}{path}",
            params={"rev": revision},
            auth=self.auth,
            verify=False
        )
        return r.json()

if __name__ == "__main__":
    print("NVUE Client Library loaded successfully")
