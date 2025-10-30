#!/bin/bash

# Define all routers with their OOB IPs
declare -A ROUTERS
ROUTERS=(
    [r1]="192.168.200.4"
    [r2]="192.168.200.3"
    [r3]="192.168.200.6"
    [r4]="192.168.200.7"
    [r5]="192.168.200.5"
    [r6]="192.168.200.8"
)

echo "=========================================="
echo "  BGP Lab - API Access Setup (Cumulus 5.6)"
echo "=========================================="
echo ""
API_USER="nvueadmin"
API_PASS="nvueadmin"
# Function to setup a single router
setup_router() {
    local name=$1
    local ip=$2
    
    echo "[$name] Configuring API access at $ip..."
    
    ssh -tt -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        cumulus@$ip "API_USER='$API_USER' API_PASS='$API_PASS' bash -s" <<'EOSSH'
sudo ztp -d >/dev/null 2>&1 || true

# Set user role and password via NVUE
echo "  → Ensuring API user ${API_USER} exists..."
if nv show system aaa user "${API_USER}" >/dev/null 2>&1; then
    echo "  → User already present. Updating role and password..."
else
    echo "  → Creating API user ${API_USER}..."
fi

nv set system aaa user "${API_USER}" role system-admin
nv set system aaa user "${API_USER}" password "${API_PASS}"

echo "  → Applying configuration..."
if ! nv config apply; then
    echo "  ✗ Failed to apply NVUE configuration"
    exit 1
fi

# Test API access
echo "  → Testing API..."
response=$(curl -s -o /dev/null -w "%{http_code}" -u "${API_USER}:${API_PASS}" --insecure https://127.0.0.1:8765/nvue_v1/)

if [ "$response" = "200" ]; then
    echo "  ✓ API authentication working (HTTP $response)"
    exit 0
else
    echo "  ✗ API returned HTTP $response"
    exit 1
fi
EOSSH
    
    if [ $? -eq 0 ]; then
        echo "[$name] ✓ Configuration successful"
    else
        echo "[$name] ✗ Configuration failed"
        return 1
    fi
    echo ""
}

# Setup all routers
success_count=0
fail_count=0

for name in "${!ROUTERS[@]}"; do
    ip="${ROUTERS[$name]}"
    if setup_router "$name" "$ip"; then
        ((success_count++))
    else
        ((fail_count++))
    fi
done

# Summary
echo "=========================================="
echo "  Setup Summary"
echo "=========================================="
echo "✓ Successful: $success_count"
echo "✗ Failed: $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo "All routers configured successfully!"
    exit 0
else
    echo "Some routers failed configuration. Check output above."
    exit 1
fi
