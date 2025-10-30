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
    if config.get("route_maps"):
        bgp_config["route-map"] = {}
        for route_map in config["route_maps"]:
            rm_name = route_map["name"]
            bgp_config["route-map"][rm_name] = {"rule": {}}
            for entry in route_map.get("entries", []):
                seq = str(entry["sequence"])
                rule = {}
                if entry.get("match"):
                    rule["match"] = entry["match"]
                if entry.get("actions"):
                    rule["action"] = entry["actions"]
                bgp_config["route-map"][rm_name]["rule"][seq] = rule
    
    # Add BGP neighbors
    for neighbor in config.get("neighbors", []):
        neighbor_cfg = {
            "remote-as": neighbor["remote_as"],
            "type": neighbor.get("type", "numbered")
        }
        if neighbor.get("update_source"):
            neighbor_cfg["update-source"] = neighbor["update_source"]
        if neighbor.get("next_hop_self"):
            neighbor_cfg.setdefault("address-family", {}).setdefault(
                "ipv4-unicast", {}
            )["next-hop-self"] = neighbor["next_hop_self"]
        if neighbor.get("route_map"):
            neighbor_cfg["route-map"] = {}
            if neighbor["route_map"].get("in"):
                neighbor_cfg["route-map"].setdefault("import", {})["name"] = neighbor["route_map"]["in"]
            if neighbor["route_map"].get("out"):
                neighbor_cfg["route-map"].setdefault("export", {})["name"] = neighbor["route_map"]["out"]
        bgp_config["vrf"]["default"]["router"]["bgp"]["neighbor"][neighbor["ip"]] = neighbor_cfg
        
    
    # Add aggregate addresses for route summarization
    if config.get("aggregates"):
        bgp_config["vrf"]["default"]["router"]["bgp"]["address-family"] = {
            "ipv4-unicast": {
                "aggregate-route": {}
            }
        }
        for aggregate in config["aggregates"]:
            bgp_config["vrf"]["default"]["router"]["bgp"]["address-family"]["ipv4-unicast"]["aggregate-route"][aggregate] = {}
    
    # Add prefix lists
    if config.get("prefix_lists"):
        bgp_config.setdefault("prefix-list", {})
        for plist in config["prefix_lists"]:
            bgp_config["prefix-list"][plist["name"]] = {"rule": {}}
            for entry in plist.get("entries", []):
                seq = str(entry["sequence"])
                bgp_config["prefix-list"][plist["name"]]["rule"][seq] = {
                    "action": entry["action"],
                    "match": {"prefix": entry["prefix"]}
                }
    
    # Apply configuration
    client.patch_config(revision, bgp_config, path="/network")
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
