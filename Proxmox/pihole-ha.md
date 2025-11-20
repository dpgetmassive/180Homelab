# Pi-hole High Availability Setup

Quick reference for the Pi-hole HA DNS infrastructure in 180 Homelab.

## Overview

Two Pi-hole instances with keepalived providing automatic failover via Virtual IP (VIP) for DNS services.

## Infrastructure

### Pi-hole Nodes
- **piholed** (10.16.1.16) - Primary Pi-hole
  - Hostname: piholed
  - Interface: eth0
  - Priority: 100 (MASTER)
  - Pi-hole version: v6.2.2

- **n100uck** (10.16.1.18) - Secondary Pi-hole
  - Hostname: n100uck
  - Interface: enp3s0
  - Priority: 90 (BACKUP)
  - Pi-hole version: v6.2.2
  - Also runs: corosync-qnetd for Proxmox cluster

### Virtual IP
- **VIP**: 10.16.1.15
- **Purpose**: Floating DNS service IP
- **Protocol**: VRRP (Virtual Router Redundancy Protocol)
- **Auth Password**: piholedns2025

## DNS Configuration

### Upstream DNS Servers
- Primary: 1.1.1.1 (Cloudflare)
- Secondary: 1.0.0.1 (Cloudflare)

### Pi-hole Settings
- Interface listening: Single interface mode
- DNSSEC: Disabled
- Domain: pihole.local
- Query logging: Enabled
- Cache size: 10000

## Keepalived Configuration

### Primary (10.16.1.16)
```bash
# /etc/keepalived/keepalived.conf
vrrp_instance DNS_VIP {
    state MASTER
    interface eth0
    virtual_router_id 15
    priority 100
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass piholedns2025
    }
    virtual_ipaddress {
        10.16.1.15/24
    }
}
```

### Secondary (10.16.1.18)
```bash
# /etc/keepalived/keepalived.conf
vrrp_instance DNS_VIP {
    state BACKUP
    interface enp3s0
    virtual_router_id 15
    priority 90
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass piholedns2025
    }
    virtual_ipaddress {
        10.16.1.15/24
    }
}
```

## Status Commands

### Check VIP Location
```bash
# On primary
ssh pihole-primary 'ip a show eth0 | grep 10.16.1.15'

# On secondary
ssh pihole-secondary 'ip a show enp3s0 | grep 10.16.1.15'
```

### Keepalived Status
```bash
# Service status
systemctl status keepalived

# View logs
journalctl -u keepalived -f

# Check VRRP state
systemctl status keepalived | grep "STATE"
```

### Pi-hole Status
```bash
# Pi-hole version
pihole -v

# DNS service status
systemctl status pihole-FTL

# Query statistics
pihole -c
```

### Test DNS Resolution
```bash
# Via VIP
dig @10.16.1.15 google.com

# Via primary
dig @10.16.1.16 google.com

# Via secondary
dig @10.16.1.18 google.com
```

## Failover Testing

### Manual Failover Test
```bash
# 1. Check initial VIP location (should be on primary)
ssh pihole-primary 'ip a show eth0 | grep 10.16.1.15'

# 2. Stop keepalived on primary
ssh pihole-primary 'systemctl stop keepalived'

# 3. Wait 5 seconds and verify VIP moved to secondary
sleep 5
ssh pihole-secondary 'ip a show enp3s0 | grep 10.16.1.15'

# 4. Test DNS still works
dig @10.16.1.15 google.com

# 5. Restart keepalived on primary
ssh pihole-primary 'systemctl start keepalived'

# 6. Verify VIP returned to primary
sleep 5
ssh pihole-primary 'ip a show eth0 | grep 10.16.1.15'
```

### Expected Behavior
- VIP starts on primary (highest priority)
- When primary fails, VIP moves to secondary within 1-3 seconds
- When primary recovers, VIP returns to primary
- DNS queries continue working throughout failover

## Gravity Sync (Optional)

Gravity Sync installed on primary for configuration replication to secondary.

### Configuration
```bash
# /etc/gravity-sync/gravity-sync.conf
REMOTE_HOST="10.16.1.18"
REMOTE_USER="root"
PIHOLE_DIR="/etc/pihole"
```

### Manual Sync Commands
```bash
# Compare configurations
ssh pihole-primary 'gravity-sync compare'

# Push from primary to secondary
ssh pihole-primary 'gravity-sync push'

# Pull from secondary to primary
ssh pihole-primary 'gravity-sync pull'
```

### Alternative: Teleporter
Use Pi-hole's built-in Teleporter feature for manual backup/restore:
1. Access primary web UI: http://10.16.1.16/admin
2. Settings → Teleporter → Generate backup
3. Apply backup to secondary via web UI

## Troubleshooting

### VIP Not Moving
```bash
# Check keepalived is running on both hosts
systemctl status keepalived

# Verify VRRP authentication matches
grep auth_pass /etc/keepalived/keepalived.conf

# Check for firewall blocking VRRP (protocol 112)
iptables -L -n | grep 112
```

### DNS Not Resolving
```bash
# Check Pi-hole FTL service
systemctl status pihole-FTL

# Check Pi-hole logs
pihole -t

# Verify listening interfaces
pihole-FTL --config
```

### Split Brain (VIP on Both Hosts)
```bash
# Check for network issues
ping -c 3 10.16.1.16
ping -c 3 10.16.1.18

# Restart keepalived on secondary
ssh pihole-secondary 'systemctl restart keepalived'
```

## Web Interfaces

### Via VIP (Automatically follows active node)
- http://10.16.1.15/admin

### Direct Access
- Primary: http://10.16.1.16/admin
- Secondary: http://10.16.1.18/admin

## Files and Directories

### Keepalived
- Config: `/etc/keepalived/keepalived.conf`
- Logs: `journalctl -u keepalived`

### Pi-hole
- Config: `/etc/pihole/pihole.toml`
- Gravity DB: `/etc/pihole/gravity.db`
- Custom DNS: `/etc/pihole/custom.list`
- Logs: `/var/log/pihole/`

### Gravity Sync
- Config: `/etc/gravity-sync/gravity-sync.conf`
- Binary: `/usr/local/bin/gravity-sync`

## SSH Access

Configured in ~/.ssh/config:
```
Host pihole-primary
    HostName 10.16.1.16
    User root

Host pihole-secondary
    HostName 10.16.1.18
    User root
```

## References

- VIP: 10.16.1.15
- Virtual Router ID: 15
- Advertisement interval: 1 second
- Upstream DNS: Cloudflare (1.1.1.1, 1.0.0.1)
