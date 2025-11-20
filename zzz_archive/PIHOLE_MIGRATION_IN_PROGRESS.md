# Pi-hole Migration - In Progress

**Date:** 2025-11-16
**Status:** 🔄 Installing Pi-hole on new LXC

---

## Critical Discovery: VM 100 Infrastructure

While preparing to migrate Homer Dashboard, discovered that **VM 100 (dockc @ 10.16.1.4)** is the core infrastructure VM running ALL services targeted for migration:

### Services Running on VM 100

| Service | Port | Purpose | Migration Target |
|---------|------|---------|------------------|
| **Pi-hole** | 53 (DNS), 82 (Web) | DNS + Ad blocking | CT 203 @ 10.16.1.53 (IN PROGRESS) |
| **Homer** | 81 | Dashboard | CT 204 @ 10.16.1.54 |
| **Uptime Kuma** | 3001 | Uptime monitoring | CT 201 @ 10.16.1.51 |
| **Gotify** | 8085 | Notifications | CT 205 @ 10.16.1.55 |
| **Twingate** | - | Remote access | CT 211 @ 10.16.1.61 |
| **Cloudflared** | - | Cloudflare tunnel | CT 210 @ 10.16.1.60 |
| **Traefik** | 80, 443 | Reverse proxy | Keep or migrate to NPM |
| **Portainer** | 8000, 9443 | Docker management | Keep or decommission |
| **Loki Stack** | Multiple | Monitoring (Grafana, Prometheus, Loki, InfluxDB, Telegraf, Promtail, UnPoller) | TBD |
| **Transmission** | 9091, 51413 | Torrent client | Keep on VM |
| **SABnzbd** | 8080 | Usenet client | Keep on VM |
| **Sonarr** | 8989 | TV automation | Keep on VM |
| **Speedtest** | 8088, 8443 | Speed testing | TBD |
| **NFS Server** | 2049, 111 | File sharing | Keep on VM |

### Keepalived Discovery

VM 100 is running **keepalived** providing a Virtual IP at **10.16.1.50**:
- VIP is configured in `/etc/keepalived/keepalived.conf`
- VRRP virtual_router_id 51, priority 255
- VIP: 10.16.1.50/24 on interface ens18

This explains why containers were configured to use 10.16.1.50 for DNS - **it was correct!** Pi-hole was accessible via this floating IP.

---

## DNS "Fix" Was Actually a Break

**Previous assumption:** 10.16.1.50 wasn't providing DNS (wrong!)

**Reality:**
- Pi-hole Docker container on VM 100 listens on 0.0.0.0:53
- Accessible via both 10.16.1.4 and 10.16.1.50
- Containers using 10.16.1.50 were getting **Pi-hole DNS with ad-blocking**
- We switched them to 10.16.1.1 (router) which **removed ad-blocking**

**Impact:**
- CT 108, 101, 129, 901 now use router DNS (10.16.1.1)
- Lost ad-blocking capability
- But DNS still works (router forwards to upstream)

**Fix:** Once new Pi-hole on CT 203 is ready, point containers to 10.16.1.53

---

## Current Pi-hole Migration Plan

### Step 1: Create New Pi-hole LXC ✅

**CT 203 Created:**
- IP: 10.16.1.53/24
- Hostname: pihole
- Cores: 2
- RAM: 2 GB
- Storage: scratch-pve:8GB
- Started: Yes

### Step 2: Install Pi-hole 🔄

**Installation in progress:**
- Using official Pi-hole automated installer
- Running unattended installation
- ETA: ~5-10 minutes

### Step 3: Sync Configuration ⏳

**Configuration to copy from VM 100:**
- Gravity database (blocklists)
- Custom DNS records
- DHCP settings (if enabled)
- Local DNS records
- Whitelist/blacklist
- Group assignments
- Client configurations

**Method:** Copy `/etc/pihole/` and `/etc/dnsmasq.d/` from Docker container

### Step 4: Testing ⏳

1. Test DNS resolution: `dig @10.16.1.53 google.com`
2. Test ad blocking: `dig @10.16.1.53 ads.google.com`
3. Verify web interface: http://10.16.1.53/admin
4. Compare block stats with VM 100

### Step 5: Update DHCP Scope ⏳

**Current DHCP server (router):**
- Scope: 10.16.1.0/24
- Current DNS: 10.16.1.4 (VM 100)
- **Update to:** 10.16.1.53 (CT 203)

**Impact:**
- New DHCP leases will get new Pi-hole
- Existing leases will renew over time
- Can manually release/renew on critical devices

### Step 6: Update Container DNS ⏳

**Containers to update:**
- CT 108 (plexpunnisher) - currently 10.16.1.1
- CT 101 (watchyourlani) - currently 10.16.1.1
- CT 129 (crafty-s) - currently 10.16.1.1
- CT 901 (tailscale) - currently 10.16.1.1

**Command:**
```bash
pct set <VMID> --nameserver 10.16.1.53,1.1.1.1
pct reboot <VMID>
```

### Step 7: Disable Keepalived ⏳

**After confirming new Pi-hole works:**
```bash
# On VM 100
systemctl stop keepalived
systemctl disable keepalived
```

**Result:** 10.16.1.50 VIP will disappear, all DNS traffic moves to 10.16.1.53

---

## Migration Sequence

**Priority order for VM 100 service migrations:**

1. ✅ **Pi-hole** → CT 203 (CURRENT)
   - Most critical (DNS impacts everything)
   - DHCP scope dependency
   - Must work before disabling keepalived

2. **Homer Dashboard** → CT 204
   - Simple static site
   - Low risk
   - Quick win

3. **Uptime Kuma** → CT 201
   - Simple Docker app
   - Database migration needed

4. **Gotify** → CT 205
   - Simple notification service
   - Database migration needed

5. **Cloudflared** → CT 210
   - Tunnel configuration
   - Medium complexity

6. **Twingate** → CT 211
   - VPN service
   - Auth tokens needed

7. **Traefik** → Keep or migrate to NPM
   - Complex routing rules
   - Many service dependencies
   - Consider consolidating with NPM

8. **Monitoring Stack** → TBD
   - Loki, Grafana, Prometheus, etc.
   - Very complex
   - May keep on VM or create dedicated monitoring VM

9. **Media Services** → Keep on VM 100
   - Transmission, SABnzbd, Sonarr
   - Well integrated
   - No immediate need to migrate

10. **NFS Server** → Keep on VM 100
    - Critical file shares
    - Don't break what works

---

## Files & Locations

### VM 100 (10.16.1.4)
```
/var/lib/docker/volumes/pihole/...     # Pi-hole Docker volume
/etc/keepalived/keepalived.conf         # VIP configuration
/dockerland/Homer/assets/              # Homer config (backed up: 1.7 MB)
```

### CT 203 (10.16.1.53)
```
/etc/pihole/                           # Pi-hole config (after install)
/etc/dnsmasq.d/                        # DNS config (after install)
/var/www/html/admin/                   # Pi-hole web UI
```

### Backups Created
```
VM 100:/tmp/homer-assets-backup.tar.gz  # Homer config (1.7 MB)
```

---

## Network Architecture

### Current State
- **Primary DNS:** 10.16.1.4 (VM 100 - Pi-hole Docker)
- **VIP DNS:** 10.16.1.50 (keepalived VIP → VM 100)
- **DHCP DNS:** 10.16.1.4 (configured in router)
- **Container DNS:** Mixed (some use 10.16.1.1, some used 10.16.1.50)

### Target State
- **Primary DNS:** 10.16.1.53 (CT 203 - Pi-hole LXC)
- **VIP DNS:** Disabled (keepalived stopped)
- **DHCP DNS:** 10.16.1.53 (CT 203)
- **Container DNS:** 10.16.1.53 (CT 203)
- **Fallback DNS:** 1.1.1.1 (Cloudflare)

---

## Rollback Plan

If new Pi-hole on CT 203 fails:

1. **Immediate:** Point DNS back to VM 100
   ```bash
   # Update DHCP to use 10.16.1.4
   # Update containers: pct set <VMID> --nameserver 10.16.1.4,1.1.1.1
   ```

2. **If keepalived already stopped:**
   ```bash
   ssh root@10.16.1.4
   systemctl start keepalived
   # 10.16.1.50 VIP will return
   ```

3. **Stop CT 203:**
   ```bash
   pct stop 203
   # Prevents confusion
   ```

---

## Current Status

- ✅ CT 203 created and started
- 🔄 Pi-hole installing on CT 203 (in progress)
- ⏳ Configuration sync pending
- ⏳ Testing pending
- ⏳ DHCP update pending
- ⏳ Container DNS update pending
- ⏳ Keepalived disable pending

**ETA to completion:** ~20-30 minutes after Pi-hole install finishes

---

## Next Steps

Once Pi-hole installation completes:
1. Set Pi-hole web password
2. Copy configuration from VM 100
3. Run gravity update
4. Test DNS resolution and ad blocking
5. Update DHCP scope on router
6. Update container DNS settings
7. Disable keepalived on VM 100
8. Monitor for 24 hours
9. Proceed with Homer migration if stable
