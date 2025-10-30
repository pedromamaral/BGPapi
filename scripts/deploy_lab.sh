#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_DIR="${PROJECT_ROOT}/configs"

# Router OOB IP addresses (adjust based on your NVIDIA Air OOB network)
declare -A ROUTERS
ROUTERS[r1]="192.168.200.4"
ROUTERS[r2]="192.168.200.3"
ROUTERS[r3]="192.168.200.6"
ROUTERS[r4]="192.168.200.7"
ROUTERS[r5]="192.168.200.5"
ROUTERS[r6]="192.168.200.6"

echo "=== BGP Lab Deployment ==="
echo

# Configure each router
for router in r1 r2 r3 r4 r5 r6; do
    echo "Configuring ${router}..."
    host=${ROUTERS[$router]}
    config_file="${CONFIG_DIR}/${router}/config.json"
    
    if [ ! -f "$config_file" ]; then
        echo "Warning: Config file not found for ${router}"
        continue
    fi
    
    # Read configuration
    config=$(cat "$config_file")
    
    # Extract individual configurations
    interfaces=$(echo $config | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['interfaces']))")
    ospf=$(echo $config | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['ospf']))")
    bgp=$(echo $config | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin)['bgp']))")
    
    # Configure interfaces
    echo "  - Configuring interfaces..."
    python3 "${PROJECT_ROOT}/scripts/configure_interfaces.py" "$host" "$interfaces"
    
    # Configure OSPF
    echo "  - Configuring OSPF..."
    python3 "${PROJECT_ROOT}/scripts/configure_ospf.py" "$host" "$ospf"
    
    # Configure BGP
    echo "  - Configuring BGP..."
    python3 "${PROJECT_ROOT}/scripts/configure_bgp.py" "$host" "$bgp"
    
    echo "✓ ${router} configuration complete"
    echo
done

echo "=== Deployment Complete ==="
