#!/bin/bash
# Script to add DNS records to Pi-hole programmatically
# Usage: ./add-pihole-dns.sh

PIHOLE_HOST="10.16.1.4"
PIHOLE_PORT="82"
PIHOLE_PASSWORD="hhfjnJ/LMj+lLFf3yxhYdU2vLCwmHCJk5jN6PNTadrY="

# Array of DNS records to add
declare -a DNS_RECORDS=(
    "uptime.gmdojo.tech:10.16.1.50"
    "grafana.gmdojo.tech:10.16.1.50"
    "nas.gmdojo.tech:10.16.1.50"
    "pihole.gmdojo.tech:10.16.1.50"
    "home.gmdojo.tech:10.16.1.50"
    "status.gmdojo.tech:10.16.1.50"
    "npm.gmdojo.tech:10.16.1.50"
)

echo "Adding DNS records to Pi-hole..."

# Note: This script documents the approach
# For now, add via Pi-hole custom.list file on Docker host
for record in "${DNS_RECORDS[@]}"; do
    domain="${record%%:*}"
    ip="${record##*:}"
    echo "Adding: $domain → $ip"

    # Add to custom.list via Docker
    ssh dp@${PIHOLE_HOST} "docker exec pihole sh -c 'echo \"$ip $domain\" >> /etc/pihole/custom.list'"
done

echo "Reloading Pi-hole DNS..."
ssh dp@${PIHOLE_HOST} "docker exec pihole pihole reloaddns"

echo "DNS records added successfully!"
