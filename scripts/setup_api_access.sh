#!/bin/bash

PASSWORD="cgrlab2"

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
echo "  NVUE API Authentication Setup"
echo "=========================================="
echo ""

for name in "${!ROUTERS[@]}"; do
    ip="${ROUTERS[$name]}"
    echo "[$name] Configuring $ip..."
    
    ssh cumulus@$ip << 'EOF'
# Clear any pending NVUE config
nv config apply empty 2>/dev/null || true

# Create password file using openssl
password_hash=$(openssl passwd -apr1 cgrlab2)
echo "cumulus:${password_hash}" | sudo tee /etc/nginx/.htpasswd > /dev/null

# Set permissions (make readable by nginx)
sudo chmod 644 /etc/nginx/.htpasswd

# Verify file was created
if [ -f /etc/nginx/.htpasswd ]; then
    echo "  ✓ htpasswd file created"
    sudo ls -l /etc/nginx/.htpasswd
else
    echo "  ✗ htpasswd file not found"
    exit 1
fi

# Restart nginx
sudo systemctl restart nginx
sleep 3

# Test API locally
response=$(curl -s -o /dev/null -w "%{http_code}" -u "cumulus:cgrlab2" --insecure https://127.0.0.1:8765/nvue_v1/)

if [ "$response" = "200" ]; then
    echo "  ✓ API working (HTTP $response)"
    exit 0
else
    echo "  ✗ API returned HTTP $response"
    exit 1
fi
EOF
    
    if [ $? -eq 0 ]; then
        # Test from oob-mgmt-server
        sleep 2
        response=$(curl -s -o /dev/null -w "%{http_code}" -u "cumulus:$PASSWORD" --insecure https://$ip:8765/nvue_v1/)
        
        if [ "$response" = "200" ]; then
            echo "[$name] ✓ Accessible from oob-mgmt (HTTP $response)"
        else
            echo "[$name] ⚠ HTTP $response from oob-mgmt"
        fi
    else
        echo "[$name] ✗ Configuration failed"
    fi
    echo ""
done

echo "=========================================="
echo "  Verification"
echo "=========================================="

success=0
fail=0

for name in "${!ROUTERS[@]}"; do
    ip="${ROUTERS[$name]}"
    response=$(curl -s -o /dev/null -w "%{http_code}" -u "cumulus:$PASSWORD" --insecure https://$ip:8765/nvue_v1/)
    
    if [ "$response" = "200" ]; then
        echo "[$name] ✓ HTTP $response"
        ((success++))
    else
        echo "[$name] ✗ HTTP $response"
        ((fail++))
    fi
done

echo ""
if [ $fail -eq 0 ]; then
    echo "✓ All $success routers ready!"
    echo ""
    echo "Credentials: cumulus / $PASSWORD"
    exit 0
else
    echo "⚠ $success working, $fail failed"
    exit 1
fi
