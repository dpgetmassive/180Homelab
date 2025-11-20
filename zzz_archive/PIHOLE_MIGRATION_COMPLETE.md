# Pi-hole Migration - COMPLETE ✅

**Date:** 2025-11-16
**Status:** Successfully completed with High Availability

---

## Summary

Successfully migrated Pi-hole from VM 100 Docker to CT 111 LXC with High Availability (HA) configuration. The new Pi-hole includes a Virtual IP (VIP) at 10.16.1.15 for future failover capability.

---

## What Was Accomplished

### ✅ Pi-hole Migration (Docker → LXC)

**Source:** VM 100 @ 10.16.1.4 (Docker container)
**Target:** CT 111 (piholed) @ 10.16.1.16 (LXC)

1. **Created new Pi-hole LXC:**
   - Used Proxmox community script (https://community-scripts.github.io/ProxmoxVE/scripts?id=pihole)
   - CT 111 (piholed) @ 10.16.1.16
   - Pi-hole v6.2.2, FTL v6.2.2, Web UI v6.2

2. **Synced configuration from VM 100:**
   - Gravity database: 110,356 blocked domains (6.1 MB)
   - Custom DNS records: 10 *.gmdojo.tech entries → 10.16.1.50 (NPM)
   - Pi-hole settings and configuration files

3. **Updated DNS infrastructure:**
   - Disabled keepalived on VM 100 (freed 10.16.1.50 VIP)
   - NPM (CT 200) now owns 10.16.1.50
   - Updated 4 containers (108, 101, 129, 901) to use new Pi-hole
   - Added fallback DNS (1.1.1.1) to all containers

### ✅ High Availability Setup

**Installed keepalived on CT 111:**
- VIP: **10.16.1.15** (future-proof HA DNS)
- VRRP virtual_router_id: 15
- Priority: 100 (MASTER)
- Authentication: PASS (piholedns2025)

**Benefits:**
- Single DNS endpoint (10.16.1.15) for all clients
- Ready for second Pi-hole on future third Proxmox node
- Automatic failover when backup Pi-hole is added
- No client configuration changes needed for HA

---

## Technical Details

### Pi-hole Configuration (CT 111)

| Setting | Value |
|---------|-------|
| **IP Address** | 10.16.1.16/24 |
| **VIP (HA)** | 10.16.1.15/24 ✅ |
| **Hostname** | piholed |
| **CPU** | 2 cores |
| **RAM** | 2 GB |
| **Storage** | scratch-pve:8GB |
| **Pi-hole Version** | v6.2.2 |
| **FTL Version** | v6.2.2 |
| **Web UI** | http://10.16.1.16/admin ✅ |
| **DNS Port** | 53 ✅ |
| **Blocklists** | 110,356 domains ✅ |

### Keepalived Configuration

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

**Status:**
- Service: active (running)
- VIP: 10.16.1.15 active on eth0
- DNS: responding on both 10.16.1.16 and 10.16.1.15
- Ad blocking: working on both IPs

### Local DNS Records

All *.gmdojo.tech domains point to NPM @ 10.16.1.50:

| Domain | IP | Service |
|--------|-----|---------|
| firewall-node1.gmdojo.tech | 10.16.1.50 | Firewall |
| grafana.gmdojo.tech | 10.16.1.50 | Monitoring |
| home.gmdojo.tech | 10.16.1.50 | Homer Dashboard |
| nas.gmdojo.tech | 10.16.1.50 | NAS |
| npm.gmdojo.tech | 10.16.1.50 | Nginx Proxy Manager |
| pihole.gmdojo.tech | 10.16.1.50 | Pi-hole UI |
| plex.gmdojo.tech | 10.16.1.50 | Plex |
| pve.gmdojo.tech | 10.16.1.50 | Proxmox |
| status.gmdojo.tech | 10.16.1.50 | Status Page |
| unifi | 10.16.1.50 | UniFi Controller |

**Note:** Pi-hole v6 uses SQLite database for local DNS. Records were added via web UI at http://10.16.1.16/admin under "Local DNS" → "DNS Records".

### Container DNS Updates

All updated to use new Pi-hole with Cloudflare fallback:

```bash
# Updated containers:
pct set 108 --nameserver 10.16.1.16,1.1.1.1  # plexpunnisher (Plex)
pct set 101 --nameserver 10.16.1.16,1.1.1.1  # watchyourlani
pct set 129 --nameserver 10.16.1.16,1.1.1.1  # crafty-s (Minecraft)
pct set 901 --nameserver 10.16.1.16,1.1.1.1  # tailscale
```

**Result:** All containers now benefit from Pi-hole ad-blocking

---

## Migration Method

### Challenge: Large File Transfer

**Problem:** Proxmox `qm guest exec` cannot reliably transfer large binary files (6+ MB gravity.db).

**Solution:** HTTP server method

1. **On VM 100 (source):**
```bash
# Export gravity database from Docker
docker cp pihole:/etc/pihole/gravity.db /tmp/gravity.db

# Start HTTP server
cd /tmp
python3 -m http.server 8899 &
```

2. **On CT 111 (target):**
```bash
# Download via HTTP
cd /tmp
wget http://10.16.1.4:8899/gravity.db

# Install
systemctl stop pihole-FTL
cp /tmp/gravity.db /etc/pihole/
chown -R pihole:pihole /etc/pihole/
systemctl start pihole-FTL
```

**Result:** Successful transfer of 6.1 MB gravity database with 110,356 domains.

---

## Verification Tests

### DNS Resolution Testing

```bash
# Test DNS on VIP (10.16.1.15)
dig @10.16.1.15 google.com +short
# Result: 142.250.204.14 ✅

# Test DNS on real IP (10.16.1.16)
dig @10.16.1.16 google.com +short
# Result: 142.250.204.14 ✅
```

### Ad Blocking Testing

```bash
# Test ad blocking on VIP
dig @10.16.1.15 ads.google.com +short
# Result: 0.0.0.0 ✅ BLOCKED

# Test ad blocking on real IP
dig @10.16.1.16 ads.google.com +short
# Result: 0.0.0.0 ✅ BLOCKED
```

### Local DNS Testing

```bash
# Test custom DNS entries
dig @10.16.1.16 home.gmdojo.tech +short
# Result: 10.16.1.50 ✅

dig @10.16.1.16 plex.gmdojo.tech +short
# Result: 10.16.1.50 ✅
```

### VIP Status

```bash
# Check VIP active on CT 111
ip addr show eth0 | grep 10.16.1.15
# Result: inet 10.16.1.15/24 scope global secondary eth0 ✅

# Check keepalived running
systemctl status keepalived
# Result: active (running) ✅
```

---

## Network Architecture Changes

### Before Migration

```
DNS Infrastructure:
├── VM 100 @ 10.16.1.4 (Docker Pi-hole)
│   └── Keepalived VIP @ 10.16.1.50 ⚠️
├── CT 200 @ 10.16.1.50 (NPM - IP conflict!)
└── Router @ 10.16.1.1 (forwarding DNS)

Container DNS Settings:
├── Some using 10.16.1.50 (broken - NPM not DNS)
├── Some using 10.16.1.1 (router - no ad blocking)
└── Result: Mixed state, 5+ second timeouts
```

### After Migration

```
DNS Infrastructure:
├── CT 111 @ 10.16.1.16 (LXC Pi-hole) ✅
│   └── Keepalived VIP @ 10.16.1.15 ✅
├── CT 200 @ 10.16.1.50 (NPM) ✅ No conflict
└── Router @ 10.16.1.1 (forwarding DNS)

Container DNS Settings:
├── All using 10.16.1.16 (Pi-hole) ✅
├── Fallback: 1.1.1.1 (Cloudflare) ✅
└── Result: Fast DNS with ad blocking

Future State (when DHCP updated):
└── All clients use 10.16.1.15 (VIP)
    └── Ready for HA when 2nd Pi-hole added
```

---

## Critical Discovery: VM 100 Infrastructure

During this migration, we discovered that **VM 100 (dockc @ 10.16.1.4)** is the core infrastructure VM running many services:

### Services on VM 100

| Service | Port | Status | Next Steps |
|---------|------|--------|------------|
| **Pi-hole** | 53, 82 | ✅ **MIGRATED to CT 111** | Can stop Docker container |
| **Homer** | 81 | Running | Ready to migrate to CT 204 |
| **Uptime Kuma** | 3001 | Running | Ready to migrate to CT 201 |
| **Gotify** | 8085 | Running | Ready to migrate to CT 205 |
| **Twingate** | - | Running | Ready to migrate to CT 211 |
| **Cloudflared** | - | Running | Ready to migrate to CT 210 |
| **Traefik** | 80, 443 | Running | Not currently used |
| **Portainer** | 8000, 9443 | Running | Assess later |
| **Loki Stack** | Multiple | Running | Keep for now |
| **Transmission** | 9091, 51413 | Running | Keep on VM |
| **SABnzbd** | 8080 | Running | Keep on VM |
| **Sonarr** | 8989 | Running | Keep on VM |
| **NFS Server** | 2049, 111 | Running | Keep on VM |

**Note:** Keepalived on VM 100 has been disabled, freeing 10.16.1.50 for NPM.

---

## Lessons Learned

### What Worked Well

1. **Proxmox Community Scripts** - Quick, reliable Pi-hole deployment
2. **HTTP server method** - Overcame Proxmox file transfer limitations
3. **Keepalived for HA** - Simple VIP setup, ready for future failover
4. **Multiple verification tests** - Confirmed DNS, ad blocking, local DNS all working
5. **Conservative approach** - User manually added DNS records via web UI when automation failed

### Technical Challenges

1. **Pi-hole v6 Architecture Change**
   - Problem: v6 uses SQLite, not flat files for local DNS
   - Files like `custom.list` not automatically loaded
   - Solution: Manual entry via web UI or SQLite commands

2. **Proxmox File Transfer Limitations**
   - Problem: `qm guest exec` can't handle large binary files
   - Solution: HTTP server method for 6+ MB files

3. **VIP Conflicts**
   - Problem: Both VM 100 keepalived and CT 200 NPM wanted 10.16.1.50
   - Solution: Disabled VM 100 keepalived, NPM now owns 10.16.1.50

4. **Cluster Quorum**
   - Problem: 2-node cluster requires both nodes for config changes
   - Solution: User brought pve-itchy back online
   - Future: Need 3rd Proxmox node for proper HA

### Best Practices Applied

- ✅ Used community-maintained installation scripts
- ✅ Tested DNS resolution on both real IP and VIP
- ✅ Verified ad blocking functionality
- ✅ Added fallback DNS (1.1.1.1) to all containers
- ✅ Documented all configuration files and commands
- ✅ Set up HA infrastructure for future expansion

---

## Current Status

### Pi-hole (CT 111)
- **Status:** ✅ Running and fully functional
- **Web UI:** http://10.16.1.16/admin
- **Real IP:** 10.16.1.16 (active)
- **VIP:** 10.16.1.15 (active, HA ready)
- **Blocked domains:** 110,356
- **Ad blocking:** Working
- **Local DNS:** 10 custom entries working

### Old Pi-hole (VM 100)
- **Status:** 🟡 Docker container still running (can stop)
- **Keepalived:** ✅ Stopped and disabled
- **VIP 10.16.1.50:** Released to NPM

### NPM (CT 200)
- **Status:** ✅ Running
- **IP:** 10.16.1.50 (no longer conflicting)
- **Purpose:** Reverse proxy for *.gmdojo.tech domains

### Containers
- **CT 108, 101, 129, 901:** ✅ Updated to use new Pi-hole
- **DNS:** 10.16.1.16, fallback 1.1.1.1
- **Ad blocking:** Active

---

## User Action Items

### Immediate (Next 24 hours)

1. **Update DHCP scope on router:**
   - Current DNS: 10.16.1.4 (old Pi-hole)
   - **Change to: 10.16.1.15** (new Pi-hole VIP)
   - This enables HA for all DHCP clients

2. **Monitor Pi-hole stability:**
   - Check http://10.16.1.16/admin for query logs
   - Verify ad blocking working on client devices
   - Ensure no DNS resolution issues

3. **Optional: Update container DNS to VIP:**
   ```bash
   # Change containers from 10.16.1.16 to 10.16.1.15 (VIP)
   pct set 108 --nameserver 10.16.1.15,1.1.1.1
   pct set 101 --nameserver 10.16.1.15,1.1.1.1
   pct set 129 --nameserver 10.16.1.15,1.1.1.1
   pct set 901 --nameserver 10.16.1.15,1.1.1.1
   pct reboot 108 && pct reboot 101 && pct reboot 129 && pct reboot 901
   ```

### Short-term (This week)

1. **Stop old Pi-hole on VM 100:**
   ```bash
   ssh root@10.16.1.4
   docker stop pihole
   docker rm pihole
   ```

2. **Delete failed Pi-hole container:**
   ```bash
   pct destroy 203
   ```

3. **Continue VM 100 service migrations:**
   - Homer Dashboard → CT 204 @ 10.16.1.54
   - Uptime Kuma → CT 201 @ 10.16.1.51
   - Gotify → CT 205 @ 10.16.1.55

### Long-term (Future)

1. **Add third Proxmox node** for proper quorum and HA

2. **Build second Pi-hole on third node:**
   - Clone CT 111 configuration
   - Configure as keepalived BACKUP (priority 90)
   - VIP 10.16.1.15 will automatically failover

3. **Test HA failover:**
   - Stop CT 111
   - Verify VIP moves to backup Pi-hole
   - Confirm DNS continues working

---

## Rollback Procedure

If issues arise with new Pi-hole:

### Quick Revert (< 5 minutes)

1. **Restart old Pi-hole on VM 100:**
```bash
ssh root@10.16.1.4
docker start pihole
systemctl start keepalived  # Brings back VIP 10.16.1.50
```

2. **Update DHCP on router:**
   - Change DNS back to 10.16.1.4 or 10.16.1.50

3. **Revert container DNS:**
```bash
pct set 108 --nameserver 10.16.1.4,1.1.1.1
pct set 101 --nameserver 10.16.1.4,1.1.1.1
pct set 129 --nameserver 10.16.1.4,1.1.1.1
pct set 901 --nameserver 10.16.1.4,1.1.1.1
pct reboot 108 && pct reboot 101 && pct reboot 129 && pct reboot 901
```

4. **Stop CT 111:**
```bash
pct stop 111
```

**Result:** Back to working state with old Pi-hole in < 5 minutes.

---

## Files & Locations

### CT 111 (10.16.1.16) - New Pi-hole

```
/etc/pihole/
├── gravity.db (6.1 MB, 110,356 domains) ✅
├── pihole-FTL.conf (Pi-hole config)
└── custom.list (local DNS - not auto-loaded in v6)

/etc/keepalived/
└── keepalived.conf (VIP 10.16.1.15 config) ✅

/etc/dnsmasq.d/
└── Various dnsmasq configs
```

### VM 100 (10.16.1.4) - Old Infrastructure

```
Docker containers:
├── pihole (can stop/remove)
├── homer
├── uptime-kuma
├── gotify
├── cloudflared
├── twingate
├── traefik
└── ... (many others)

/etc/keepalived/keepalived.conf (disabled) ✅
```

### Backups

No backups created (Pi-hole is actively syncing gravity lists, old Docker Pi-hole still intact as fallback).

---

## Success Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| **Pi-hole Migration** |  |  |  |
| - New Pi-hole running | Yes | Yes | ✅ |
| - DNS resolution | Working | Working | ✅ |
| - Ad blocking | Working | Working | ✅ |
| - Blocklists synced | 110k+ | 110,356 | ✅ |
| - Local DNS entries | 10 | 10 | ✅ |
| - Container DNS updated | 4 | 4 | ✅ |
| **High Availability** |  |  |  |
| - VIP configured | Yes | 10.16.1.15 | ✅ |
| - Keepalived running | Yes | Yes | ✅ |
| - DNS on VIP | Working | Working | ✅ |
| - Ad blocking on VIP | Working | Working | ✅ |
| - Ready for 2nd Pi-hole | Yes | Yes | ✅ |
| **Infrastructure Cleanup** |  |  |  |
| - VM 100 keepalived | Disabled | Disabled | ✅ |
| - NPM 10.16.1.50 | No conflict | No conflict | ✅ |
| - Old Pi-hole | Can stop | Can stop | 🟡 |

---

## Future HA Architecture

```
DNS High Availability Setup:

VIP: 10.16.1.15
├── CT 111 @ 10.16.1.16 (pve-scratchy) - MASTER (priority 100) ✅ ACTIVE NOW
└── CT ### @ 10.16.1.## (pve-#### node 3) - BACKUP (priority 90) ⏳ FUTURE

When CT 111 fails:
└── VIP automatically moves to BACKUP Pi-hole
    └── Clients continue using 10.16.1.15 with zero downtime

Requires:
└── Third Proxmox node for proper cluster quorum
    └── Can survive one node failure
    └── HA VM/CT migration
```

---

## Next Steps: VM 100 Service Migrations

Now that Pi-hole is migrated, continue with VM 100 service consolidation:

**Priority 1 (Quick wins):**
1. Homer Dashboard → CT 204 @ 10.16.1.54
2. Uptime Kuma → CT 201 @ 10.16.1.51
3. Gotify → CT 205 @ 10.16.1.55

**Priority 2 (Remote access):**
4. Cloudflared → CT 210 @ 10.16.1.60
5. Twingate → CT 211 @ 10.16.1.61

**Priority 3 (Assess later):**
6. Traefik (not currently used)
7. Portainer (Docker management)
8. Loki monitoring stack

**Keep on VM 100:**
- Transmission, SABnzbd, Sonarr (media automation)
- NFS server (file shares)

See `SESSION_SUMMARY_2025-11-16.md` for full migration plan.

---

## Documentation Created

During this migration, the following documents were created/updated:

1. `PIHOLE_MIGRATION_IN_PROGRESS.md` - Original plan and VM 100 discovery
2. `SESSION_SUMMARY_2025-11-16.md` - Comprehensive session summary including Plex migration
3. `PIHOLE_MIGRATION_COMPLETE.md` - This document (final summary)

---

## Final Notes

**Migration completed successfully with High Availability!**

Pi-hole has been migrated from VM 100 Docker to CT 111 LXC with:
- ✅ 110,356 blocked domains (gravity database synced)
- ✅ 10 custom DNS entries for *.gmdojo.tech domains
- ✅ High Availability VIP at 10.16.1.15
- ✅ Keepalived configured for future failover
- ✅ 4 containers updated to use new Pi-hole
- ✅ NPM now owns 10.16.1.50 without conflict

**Infrastructure is production-ready** and prepared for future expansion with a second Pi-hole.

**User action required:** Update router DHCP scope to use 10.16.1.15 (VIP) for HA DNS.

**Next phase:** Continue VM 100 service migrations (Homer, Uptime Kuma, Gotify).

---

**Congratulations on completing this complex migration with High Availability!** 🎉🔒
