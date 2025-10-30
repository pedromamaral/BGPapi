#!/usr/bin/env python3
import sys
import json
from nvue_client import NVUEClient

def configure_bgp(host, config):
    client = NVUEClient(host)
    
    # Create revision
    revision = client.create_revision()
    print(f"Created revision: {revision}")
    
    # Build BGP configuration payload
    bgp_config = {
        "vrf": {
            "default": {
                "router": {
                    "bgp": {
                        "autonomous-system": config["as_number"],
                        "router-id": config["router_id"],
                        "enable": "on",
                        "neighbor": {}
                    }
                }
            }
        }
    }
    
    # Add BGP neighbors
    for neighbor in config.get("neighbors", []):
        bgp_config["vrf"]["default"]["router"]["bgp"]["neighbor"][neighbor["ip"]] = {
            "remote-as": neighbor["remote_as"],
            "type": neighbor.get("type", "numbered")
        }
    
    # Add aggregate addresses for route summarization
    if config.get("aggregates"):
        bgp_config["vrf"]["default"]["router"]["bgp"]["address-family"] = {
            "ipv4-unicast": {
                "aggregate-route": {}
            }
        }
        for aggregate in config["aggregates"]:
            bgp_config["vrf"]["default"]["router"]["bgp"]["address-family"]["ipv4-unicast"]["aggregate-route"][aggregate] = {}
    
    # Apply configuration
    client.apply_config(revision, bgp_config)
    print("Configuration staged")
    
    # Apply revision
    client.apply_revision(revision)
    print("Applying configuration...")
    
    # Wait for apply
    if client.wait_for_apply(revision):
        print("Configuration applied successfully")
        return 0
    else:
        print("Configuration apply timeout")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: configure_bgp.py <host> <config_json>")
        sys.exit(1)
    
    host = sys.argv[1]
    config = json.loads(sys.argv[2])
    sys.exit(configure_bgp(host, config))
