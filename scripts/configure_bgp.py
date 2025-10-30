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
        "network": {
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
    }
    network_root = bgp_config["network"]
    vrf_default = network_root["vrf"]["default"]["router"]["bgp"]
    if config.get("route_maps"):
        policy_root = network_root.setdefault("policy", {}).setdefault("route-map", {})
        for route_map in config["route_maps"]:
            rm_name = route_map["name"]
            policy_root[rm_name] = {"rule": {}}
            for entry in route_map.get("entries", []):
                seq = str(entry["sequence"])
                rule = {}
                if entry.get("match"):
                    rule["match"] = entry["match"]
                if entry.get("actions"):
                    rule["action"] = entry["actions"]
                policy_root[rm_name]["rule"][seq] = rule
    
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
            if neighbor["route_map"].get("in"):
                neighbor_cfg.setdefault("in", {})["route-map"] = neighbor["route_map"]["in"]
            if neighbor["route_map"].get("out"):
                neighbor_cfg.setdefault("out", {})["route-map"] = neighbor["route_map"]["out"]
        vrf_default["neighbor"][neighbor["ip"]] = neighbor_cfg
        
    
    # Add aggregate addresses for route summarization
    if config.get("aggregates"):
        af = vrf_default.setdefault("address-family", {}).setdefault("ipv4-unicast", {})
        af.setdefault("aggregate-route", {})
        for aggregate in config["aggregates"]:
            af["aggregate-route"][aggregate] = {}
    if config.get("prefix_lists"):
        prefix_root = network_root.setdefault("prefix-list", {})
        for plist in config["prefix_lists"]:
            prefix_root[plist["name"]] = {"rule": {}}
            for entry in plist.get("entries", []):
                seq = str(entry["sequence"])
                prefix_root[plist["name"]]["rule"][seq] = {
                    "action": entry["action"],
                    "match": {"prefix": entry["prefix"]}
                }
    
    # Apply configuration
    client.patch_config(revision, bgp_config)
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
