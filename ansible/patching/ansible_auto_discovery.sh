#!/bin/bash
#
# Ansible Asset Auto-Discovery Script
# Discovers Proxmox VMs, LXC containers, and network hosts
# Automatically updates Ansible inventory
#

set -euo pipefail

# Configuration
ANSIBLE_DIR="/opt/ansible"
INVENTORY_FILE="$ANSIBLE_DIR/inventories/homelab.yml"
INVENTORY_BACKUP="$ANSIBLE_DIR/inventories/homelab.yml.backup"
DISCOVERY_LOG="/var/log/ansible-discovery.log"
PVE_HOSTS="pve-scratchy:10.16.1.22 pve-itchy:10.16.1.8"
NETWORK_RANGE="10.16.1.0/24"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DISCOVERY_LOG"
}

# Backup existing inventory
backup_inventory() {
    if [ -f "$INVENTORY_FILE" ]; then
        cp "$INVENTORY_FILE" "$INVENTORY_BACKUP"
        log "Backed up inventory to $INVENTORY_BACKUP"
    fi
}

# Discover Proxmox VMs and LXC containers
discover_proxmox_assets() {
    log "Discovering Proxmox assets..."

    local pve_vms=()
    local pve_cts=()

    for pve_entry in $PVE_HOSTS; do
        IFS=':' read -r pve_host pve_ip <<< "$pve_entry"

        log "Scanning $pve_host ($pve_ip)..."

        # Discover VMs
        while IFS='|' read -r vmid status name; do
            if [ -n "$vmid" ] && [ "$vmid" != "VMID" ]; then
                # Get VM IP via guest agent if available
                vm_ip=$(ssh -o ConnectTimeout=5 root@"$pve_ip" "qm guest cmd $vmid network-get-interfaces 2>/dev/null" | grep -oP '"ip-address":\s*"\K[0-9.]+' | head -1 || echo "")

                if [ -z "$vm_ip" ]; then
                    # Try to get IP from MAC/ARP
                    vm_mac=$(ssh root@"$pve_ip" "qm config $vmid" | grep -oP 'net0:.*,macaddr=\K[A-F0-9:]+' || echo "")
                    if [ -n "$vm_mac" ]; then
                        vm_ip=$(arp -n | grep -i "$vm_mac" | awk '{print $1}' || echo "")
                    fi
                fi

                pve_vms+=("$vmid|$name|$status|$vm_ip|$pve_host")
                log "  Found VM: $vmid ($name) - Status: $status - IP: ${vm_ip:-unknown}"
            fi
        done < <(ssh root@"$pve_ip" "qm list" | tail -n +2 | awk '{print $1"|"$3"|"$2}')

        # Discover LXC Containers
        while IFS='|' read -r ctid status name; do
            if [ -n "$ctid" ] && [ "$ctid" != "VMID" ]; then
                # Get container IP
                ct_ip=$(ssh root@"$pve_ip" "pct exec $ctid -- ip -4 addr show scope global 2>/dev/null | grep -oP 'inet \K[0-9.]+' | head -1" 2>/dev/null || echo "")

                pve_cts+=("$ctid|$name|$status|$ct_ip|$pve_host")
                log "  Found CT: $ctid ($name) - Status: $status - IP: ${ct_ip:-unknown}"
            fi
        done < <(ssh root@"$pve_ip" "pct list" | tail -n +2 | awk '{print $1"|"$3"|"$2}')
    done

    # Export for later use
    printf '%s\n' "${pve_vms[@]}" > /tmp/discovered_vms.txt
    printf '%s\n' "${pve_cts[@]}" > /tmp/discovered_containers.txt
}

# Discover network hosts (for non-Proxmox assets)
discover_network_hosts() {
    log "Scanning network $NETWORK_RANGE..."

    # Use nmap for host discovery
    nmap -sn -oG - "$NETWORK_RANGE" 2>/dev/null | grep "Status: Up" | awk '{print $2}' > /tmp/discovered_ips.txt

    local host_count=$(wc -l < /tmp/discovered_ips.txt)
    log "Found $host_count active hosts on network"
}

# Generate updated inventory
generate_inventory() {
    log "Generating updated inventory..."

    cat > "$INVENTORY_FILE" <<'EOF'
---
all:
  vars:
    ansible_user: root
    ansible_python_interpreter: /usr/bin/python3

  children:
    proxmox_hosts:
      hosts:
        pve-scratchy:
          ansible_host: 10.16.1.22
          cores: 12
          ram_gb: 48
        pve-itchy:
          ansible_host: 10.16.1.8
          cores: 8
          ram_gb: 32

    truenas:
      hosts:
        truenas-primary:
          ansible_host: 10.16.1.6
          role: primary
        truenas-dr:
          ansible_host: 10.16.1.20
          role: disaster_recovery

    infrastructure:
      hosts:
        n100uck:
          ansible_host: 10.16.1.18
          ansible_connection: local
          services:
            - monitoring_dashboard
            - ansible_control_node
        npm:
          ansible_host: 10.16.1.50
          ct_id: 200
          services:
            - nginx_proxy_manager

    containers:
      hosts:
EOF

    # Add discovered containers
    if [ -f /tmp/discovered_containers.txt ]; then
        while IFS='|' read -r ctid name status ip pve_host; do
            if [ "$status" = "running" ] && [ -n "$ip" ]; then
                # Generate safe hostname from name
                hostname=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-')

                cat >> "$INVENTORY_FILE" <<EOF
        $hostname:
          ansible_host: $ip
          ct_id: $ctid
          pve_host: $pve_host
EOF
            fi
        done < /tmp/discovered_containers.txt
    fi

    # Add VMs section
    cat >> "$INVENTORY_FILE" <<'EOF'

    vms:
      hosts:
EOF

    # Add discovered VMs
    if [ -f /tmp/discovered_vms.txt ]; then
        while IFS='|' read -r vmid name status ip pve_host; do
            if [ "$status" = "running" ] && [ -n "$ip" ]; then
                # Generate safe hostname from name
                hostname=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr -cd '[:alnum:]-')

                cat >> "$INVENTORY_FILE" <<EOF
        $hostname:
          ansible_host: $ip
          vm_id: $vmid
          pve_host: $pve_host
EOF
            fi
        done < /tmp/discovered_vms.txt
    fi

    log "Inventory updated: $INVENTORY_FILE"
}

# Verify inventory syntax
verify_inventory() {
    log "Verifying inventory syntax..."

    if ansible-inventory -i "$INVENTORY_FILE" --list > /dev/null 2>&1; then
        log "Inventory syntax is valid"
        return 0
    else
        log "ERROR: Invalid inventory syntax, restoring backup"
        cp "$INVENTORY_BACKUP" "$INVENTORY_FILE"
        return 1
    fi
}

# Test connectivity to discovered hosts
test_connectivity() {
    log "Testing connectivity to discovered hosts..."

    ansible all -i "$INVENTORY_FILE" -m ping --one-line 2>&1 | tee -a "$DISCOVERY_LOG"
}

# Generate discovery report
generate_report() {
    local report_file="/opt/ansible/reports/discovery-$(date +%Y-%m-%d).txt"

    {
        echo "========================================="
        echo "Ansible Asset Discovery Report"
        echo "Generated: $(date)"
        echo "========================================="
        echo ""
        echo "Discovered Assets:"
        echo "-----------------"

        echo ""
        echo "VMs ($(wc -l < /tmp/discovered_vms.txt)):"
        if [ -f /tmp/discovered_vms.txt ]; then
            cat /tmp/discovered_vms.txt | while IFS='|' read -r vmid name status ip pve_host; do
                printf "  - %-20s VM%-4s %-10s %-15s %s\n" "$name" "$vmid" "$status" "${ip:-unknown}" "$pve_host"
            done
        fi

        echo ""
        echo "Containers ($(wc -l < /tmp/discovered_containers.txt)):"
        if [ -f /tmp/discovered_containers.txt ]; then
            cat /tmp/discovered_containers.txt | while IFS='|' read -r ctid name status ip pve_host; do
                printf "  - %-20s CT%-4s %-10s %-15s %s\n" "$name" "$ctid" "$status" "${ip:-unknown}" "$pve_host"
            done
        fi

        echo ""
        echo "========================================="
    } | tee "$report_file"

    log "Discovery report saved: $report_file"
}

# Main execution
main() {
    log "========================================="
    log "Starting Ansible Asset Auto-Discovery"
    log "========================================="

    # Create reports directory if needed
    mkdir -p "$(dirname "$DISCOVERY_LOG")"
    mkdir -p "/opt/ansible/reports"

    # Backup current inventory
    backup_inventory

    # Run discovery
    discover_proxmox_assets
    discover_network_hosts

    # Generate and verify new inventory
    generate_inventory

    if verify_inventory; then
        test_connectivity
        generate_report
        log "Auto-discovery completed successfully"
    else
        log "Auto-discovery failed - inventory reverted"
        exit 1
    fi

    log "========================================="
}

# Run main function
main "$@"
