#!/usr/bin/env python3
import sys
import json
from nvue_client import NVUEClient

def configure_ospf(host, ospf_config):
    """Configure OSPF on a router"""
    client = NVUEClient(host)
    
    print(f"Configuring OSPF on {host}")
    revision = client.create_revision()
    
    config = {
        "vrf": {
            "default": {
                "router": {
                    "ospf": {
                        "enable": "on",
                        "router-id": ospf_config["router_id"],
                        "area": {
                            str(ospf_config["area"]): {
                                "network": {}
                            }
                        }
                    }
                }
            }
        }
    }
    
    # Add networks to OSPF
    for network in ospf_config.get("networks", []):
        config["vrf"]["default"]["router"]["ospf"]["area"][str(ospf_config["area"])]["network"][network] = {}
    
    client.patch_config(revision, config)
    client.apply_revision(revision)
    
    if client.wait_for_apply(revision):
        print(f"✓ OSPF configured successfully on {host}")
        return True
    else:
        print(f"✗ Failed to configure OSPF on {host}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: configure_ospf.py <host> <config_json>")
        sys.exit(1)
    
    host = sys.argv[1]
    config = json.loads(sys.argv[2])
    sys.exit(0 if configure_ospf(host, config) else 1)
