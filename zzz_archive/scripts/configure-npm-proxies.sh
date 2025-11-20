#!/bin/bash
# Script to configure NPM proxy hosts via API
# This creates all proxy hosts for gmdojo.tech domain programmatically

set -e

NPM_HOST="10.16.1.50"
NPM_PORT="81"
NPM_EMAIL="dp@getmassive.com.au"
NPM_PASSWORD=""  # Set this or pass as environment variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== NPM Proxy Host Configuration Script ===${NC}"
echo ""

# Check if password is provided
if [ -z "$NPM_PASSWORD" ]; then
    echo -e "${YELLOW}NPM admin password not set.${NC}"
    echo "Please set NPM_PASSWORD environment variable or edit this script."
    echo "Example: export NPM_PASSWORD='your_password'"
    exit 1
fi

# Step 1: Get JWT token
echo "Step 1: Authenticating with NPM API..."
TOKEN_RESPONSE=$(curl -s -X POST "http://${NPM_HOST}:${NPM_PORT}/api/tokens" \
    -H "Content-Type: application/json" \
    -d "{\"identity\":\"${NPM_EMAIL}\",\"secret\":\"${NPM_PASSWORD}\"}")

TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}Failed to authenticate with NPM API${NC}"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Authenticated successfully${NC}"
echo ""

# Step 2: Get SSL certificate ID for *.gmdojo.tech
echo "Step 2: Finding SSL certificate ID..."
CERT_RESPONSE=$(curl -s -X GET "http://${NPM_HOST}:${NPM_PORT}/api/nginx/certificates" \
    -H "Authorization: Bearer ${TOKEN}")

CERT_ID=$(echo "$CERT_RESPONSE" | python3 -c "import sys, json; certs = json.load(sys.stdin); print(next((c['id'] for c in certs if '*.gmdojo.tech' in c.get('domain_names', [])), ''))" 2>/dev/null)

if [ -z "$CERT_ID" ]; then
    echo -e "${RED}Failed to find *.gmdojo.tech SSL certificate${NC}"
    echo "Please ensure the wildcard SSL certificate is created in NPM first."
    exit 1
fi

echo -e "${GREEN}✓ Found SSL certificate ID: ${CERT_ID}${NC}"
echo ""

# Step 3: Create proxy hosts
echo "Step 3: Creating proxy hosts..."
echo ""

# Function to create proxy host
create_proxy_host() {
    local domain=$1
    local forward_scheme=$2
    local forward_host=$3
    local forward_port=$4
    local websockets=$5
    local advanced_config=$6

    echo -n "Creating $domain... "

    PROXY_DATA=$(cat <<EOF
{
  "domain_names": ["$domain"],
  "forward_scheme": "$forward_scheme",
  "forward_host": "$forward_host",
  "forward_port": $forward_port,
  "access_list_id": 0,
  "certificate_id": $CERT_ID,
  "ssl_forced": true,
  "hsts_enabled": true,
  "hsts_subdomains": false,
  "http2_support": true,
  "block_exploits": true,
  "caching_enabled": $([ "$forward_scheme" == "https" ] && echo "true" || echo "false"),
  "allow_websocket_upgrade": $websockets,
  "advanced_config": "$advanced_config",
  "enabled": true,
  "meta": {}
}
EOF
)

    RESPONSE=$(curl -s -X POST "http://${NPM_HOST}:${NPM_PORT}/api/nginx/proxy-hosts" \
        -H "Authorization: Bearer ${TOKEN}" \
        -H "Content-Type: application/json" \
        -d "$PROXY_DATA")

    if echo "$RESPONSE" | grep -q '"id"'; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo "Error: $RESPONSE"
    fi
}

# Create proxy hosts
create_proxy_host "pve.gmdojo.tech" "https" "10.16.1.22" 8006 true "proxy_ssl_verify off;"
create_proxy_host "uptime.gmdojo.tech" "http" "10.16.1.4" 3001 true ""
create_proxy_host "grafana.gmdojo.tech" "http" "10.16.1.4" 3002 true ""
create_proxy_host "nas.gmdojo.tech" "https" "10.16.1.6" 443 true "proxy_ssl_verify off;"
create_proxy_host "pihole.gmdojo.tech" "http" "10.16.1.4" 82 false "location / { proxy_pass http://10.16.1.4:82/admin/; }"
create_proxy_host "home.gmdojo.tech" "http" "10.16.1.4" 81 false ""
create_proxy_host "npm.gmdojo.tech" "http" "10.16.1.50" 81 false ""
create_proxy_host "status.gmdojo.tech" "http" "10.16.1.4" 3001 true ""

echo ""
echo -e "${GREEN}=== Proxy hosts created successfully! ===${NC}"
echo ""
echo "Test the proxy hosts with:"
echo "  curl -I https://pve.gmdojo.tech"
echo "  curl -I https://uptime.gmdojo.tech"
echo "  curl -I https://grafana.gmdojo.tech"
echo ""
echo "Access NPM admin at: http://10.16.1.50:81"
