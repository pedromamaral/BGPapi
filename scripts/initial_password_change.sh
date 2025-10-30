#!/bin/bash

# Configuration
OLD_PASSWORD="cumulus"
NEW_PASSWORD="cgrlab2"

# Router definitions
declare -A ROUTERS
ROUTERS=(
    [r1]="192.168.200.4"
    [r2]="192.168.200.3"
    [r3]="192.168.200.6"
    [r4]="192.168.200.7"
    [r5]="192.168.200.5"
    [r6]="192.168.200.6"
)

echo "=========================================="
echo "  Password Change Script"
echo "  New password: $NEW_PASSWORD"
echo "=========================================="
echo ""

# Function to change password on a single router
change_password() {
    local name=$1
    local ip=$2
    
    echo "[$name] Connecting to $ip..."
    
    # SSH with old password and change to new password
    sshpass -p "$OLD_PASSWORD" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 cumulus@$ip << EOSSH
# Change the Linux system password
echo "cumulus:$NEW_PASSWORD" | sudo chpasswd

# Set NVUE role and password for API access
nv set system aaa user cumulus role system-admin
nv set system aaa user cumulus password $NEW_PASSWORD
nv config apply

# Wait for changes to apply
sleep 3

# Verify password change worked (try sudo with new password)
echo "$NEW_PASSWORD" | sudo -S whoami > /dev/null 2>&1
if [ \$? -eq 0 ]; then
    echo "  ✓ Password changed successfully"
    exit 0
else
    echo "  ✗ Password change verification failed"
    exit 1
fi
EOSSH
    
    if [ $? -eq 0 ]; then
        echo "[$name] ✓ Password changed to: $NEW_PASSWORD"
        
        # Test API access with new password
        response=$(curl -s -o /dev/null -w "%{http_code}" -u "cumulus:$NEW_PASSWORD" --insecure https://$ip:8765/nvue_v1/)
        
        if [ "$response" = "200" ]; then
            echo "[$name] ✓ API access verified"
        else
            echo "[$name] ⚠ API returned HTTP $response (may need time to propagate)"
        fi
        
        return 0
    else
        echo "[$name] ✗ Failed to change password"
        return 1
    fi
    echo ""
}

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get update -qq
    sudo apt-get install -y sshpass
    echo ""
fi

# Change password on all routers
success_count=0
fail_count=0

for name in "${!ROUTERS[@]}"; do
    ip="${ROUTERS[$name]}"
    if change_password "$name" "$ip"; then
        ((success_count++))
    else
        ((fail_count++))
    fi
    echo ""
done

# Summary
echo "=========================================="
echo "  Summary"
echo "=========================================="
echo "✓ Successful: $success_count"
echo "✗ Failed: $fail_count"
echo ""

if [ $fail_count -eq 0 ]; then
    echo "All passwords changed successfully!"
    echo ""
    echo "New credentials:"
    echo "  Username: cumulus"
    echo "  Password: $NEW_PASSWORD"
    echo ""
    echo "⚠ IMPORTANT: Update your scripts to use the new password!"
else
    echo "Some routers failed. Check output above."
    exit 1
fi
