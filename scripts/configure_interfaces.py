#!/usr/bin/env python3
import sys
import json
from nvue_client import NVUEClient

def configure_interfaces(host, interfaces_config):
    """Configure IP addresses on interfaces"""
    client = NVUEClient(host)
    
    print(f"Configuring interfaces on {host}")
    revision = client.create_revision()
    print(f"Created revision: {revision}")
    
    # Build interface configuration
    config = {"interface": {}}
    
    for iface in interfaces_config:
        config["interface"][iface["name"]] = {
            "ip": {
                "address": {
                    iface["ip"]: {}
                }
            },
            "type": "swp"
        }
    
    # Apply configuration
    client.patch_config(revision, config)
    client.apply_revision(revision)
    
    if client.wait_for_apply(revision):
        print(f"✓ Interfaces configured successfully on {host}")
        return True
    else:
        print(f"✗ Failed to configure interfaces on {host}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: configure_interfaces.py <host> <config_json>")
        sys.exit(1)
    
    host = sys.argv[1]
    config = json.loads(sys.argv[2])
    sys.exit(0 if configure_interfaces(host, config) else 1)
