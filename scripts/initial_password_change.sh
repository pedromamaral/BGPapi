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
echo "  Old password: $OLD_PASSWORD"
echo "  New password: $NEW_PASSWORD"
echo "=========================================="
echo ""

# Install dependencies
echo "Checking dependencies..."
if ! command -v expect &> /dev/null; then
    echo "Installing expect..."
    sudo apt-get update -qq
    sudo apt-get install -y expect
fi

if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    sudo apt-get install -y sshpass
fi

echo ""

# Function to change password using expect
change_password() {
    local name=$1
    local ip=$2
    
    echo "[$name] Connecting to $ip..."
    
    # Create expect script on the fly
    expect << EOF
set timeout 30
log_user 0

# Try to connect
spawn ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null cumulus@$ip

# Handle different scenarios
expect {
    # Scenario 1: Forced password change on first login
    "Password change required" {
        send "$OLD_PASSWORD\r"
        expect "New password:"
        send "$NEW_PASSWORD\r"
        expect "Retype new password:"
        send "$NEW_PASSWORD\r"
        expect "$ "
    }
    
    # Scenario 2: Password expired
    "You are required to change your password immediately" {
        send "$OLD_PASSWORD\r"
        expect {
            "New password:" {
                send "$NEW_PASSWORD\r"
                expect "Retype new password:"
                send "$NEW_PASSWORD\r"
                expect "$ "
            }
            "(current) UNIX password:" {
                send "$OLD_PASSWORD\r"
                expect "New password:"
                send "$NEW_PASSWORD\r"
                expect "Retype new password:"
                send "$NEW_PASSWORD\r"
                expect "$ "
            }
        }
    }
    
    # Scenario 3: Normal login
    "password:" {
        send "$OLD_PASSWORD\r"
        expect "$ "
    }
    
    timeout {
        puts "[$name] ✗ Connection timeout"
        exit 1
    }
}

# Now we're logged in, configure everything
send "echo 'cumulus:$NEW_PASSWORD' | sudo chpasswd\r"
expect "$ "

send "nv set system aaa user cumulus role system-admin\r"
expect "$ "

send "nv set system aaa user cumulus password $NEW_PASSWORD\r"
expect "$ "

send "nv config apply\r"
expect "$ "

# Wait for config to apply
send "sleep 5\r"
expect "$ "

send "exit\r"
expect eof
EOF
    
    if [ $? -eq 0 ]; then
        echo "[$name] ✓ Password changed to: $NEW_PASSWORD"
        
        # Test API access with new password
        sleep 2
        response=$(curl -s -o /dev/null -w "%{http_code}" -u "cumulus:$NEW_PASSWORD" --insecure https://$ip:8765/nvue_v1/)
        
        if [ "$response" = "200" ]; then
            echo "[$name] ✓ API access verified"
        else
            echo "[$name] ⚠ API returned HTTP $response"
        fi
        
        return 0
    else
        echo "[$name] ✗ Failed to change password"
        return 1
    fi
}

# Process all routers
success_count=0
fail_count=0

for name in "${!ROUTERS[@]}"; do
    if change_password "$name" "${ROUTERS[$name]}"; then
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
else
    echo "Some routers failed. Manual intervention may be required."
    exit 1
fi
