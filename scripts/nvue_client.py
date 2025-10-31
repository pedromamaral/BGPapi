#!/usr/bin/env python3
import json
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NVUEClient:
    def __init__(self, host, username="cumulus", password="cgrlab2"):
        self.auth = (username, password)
        self.base_url = f"https://{host}:8765/nvue_v1"
        self.headers = {"Content-Type": "application/json"}
        
    def create_revision(self):
        r = requests.post(f"{self.base_url}/revision", auth=self.auth, verify=False)
        r.raise_for_status()
        payload = r.json()
        if "revision" in payload:
            info = payload["revision"]
            if isinstance(info, dict) and "id" in info:
                return str(info["id"])
            return str(info)
        return str(next(iter(payload)))
    
    def patch_config(self, revision, payload, path="/"):
        if not path.startswith("/"):
            path = f"/{path}"
        r = requests.patch(
            f"{self.base_url}{path}",
            params={"rev": revision},
            auth=self.auth,
            headers=self.headers,
            data=json.dumps(payload),
            verify=False
        )
        if r.status_code >= 400:
            print(f"Patch response: {r.status_code}")
            print(f"Error: {r.text}")
        r.raise_for_status()
    
    def apply_revision(self, revision):
        r = requests.post(
            f"{self.base_url}/revision/{revision}/apply",
            auth=self.auth,
            verify=False
        )
        r.raise_for_status()
    
    def wait_for_apply(self, revision, retries=30):
        for _ in range(retries):
            details = self.get_revision(revision)
            state = details.get("state")
            print(f"Revision state: {state}")
            if state == "applied":
                return True
            if state in {"invalid", "apply_failed"}:
                return False
            time.sleep(2)
        return False

    def get_revision(self, revision):
        r = requests.get(
            f"{self.base_url}/revision/{revision}",
            auth=self.auth,
            verify=False
        )
        r.raise_for_status()
        return r.json()

    def get_config(self, path="/", revision="applied"):
        if not path.startswith("/"):
            path = f"/{path}"
        r = requests.get(
            f"{self.base_url}{path}",
            params={"rev": revision},
            auth=self.auth,
            verify=False
        )
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    print("NVUE Client Library loaded successfully")
