# Phase 2+ Migration Plan - Refined Based on User Feedback

**Date:** 2025-11-16
**Status:** Ready to begin
**Based on:** Complete infrastructure inventory + user decisions

---

## Executive Summary

After reviewing the complete infrastructure inventory, the migration plan has been refined:

**Services to Migrate to LXC:** 13 services
**Services to Remove/Decommission:** 11 services
**Services to Keep in Docker:** 2 services (Twingate, Cloudflared)
**VMs to Decommission:** 2 VMs (100, 109, potentially 112)

**Timeline:** 6-8 weeks
**Resource Impact:** Slight increase in RAM (3-4 GB), better isolation and management

---

## Key Findings from Investigation

### 1. Plex is Already in LXC! ✅
- **CT 108 "plexpunnisher"** @ 10.16.1.36
- Already running Plex Media Server in LXC
- 4 GB RAM, 64 GB disk
- Hardware acceleration configured (GPU passthrough)
- **VM 112 (deb-srv-plex)** appears to be old/unused → **Decommission**

### 2. VM 107 (deb-util-01) @ 10.16.1.24
- Has Tailscale installed
- Could not access without different credentials
- **Action:** User to investigate what utilities are needed
- May be duplicate Tailscale (CT 901 already has Tailscale)

### 3. Cloudflared Tunnel - Keep in Docker
**Reasoning:**
- Stateless service (no persistent data)
- Docker restart policies provide auto-recovery
- Easy updates (pull new image)
- Isolated from host system
- **Alternative:** If decommissioning all Docker, can migrate to LXC with systemd service

### 4. Twingate Connector - Keep in Docker (for now)
**Reasoning:**
- Zero-trust network access connector
- Designed to run in containers
- Requires specific networking capabilities
- **Action:** Research if it can run in LXC, but likely best in Docker

---

## Services Migration Matrix

### Migrate to LXC (13 services)

| Priority | Service | Current | Target LXC | Complexity | Week |
|----------|---------|---------|-----------|------------|------|
| ⭐⭐⭐ | Uptime Kuma | VM 100:3001 | CT 201 @ 10.16.1.51 | Low | 1 |
| ⭐⭐⭐ | Homer Dashboard | VM 100:81 | CT 204 @ 10.16.1.54 | Low | 1 |
| ⭐⭐⭐ | Gotify | VM 100:8085 | CT 205 @ 10.16.1.55 | Low | 2 |
| ⭐⭐ | Grafana | VM 100:3002 | CT 202 @ 10.16.1.52 | Medium | 3 |
| ⭐⭐ | Prometheus | VM 100:9090 | CT 202 (same) | Medium | 3 |
| ⭐⭐ | Loki | VM 100:3100 | CT 202 (same) | Medium | 3 |
| ⭐⭐ | InfluxDB | VM 100:8086 | CT 202 (same) | Medium | 3 |
| ⭐⭐ | Promtail | VM 100:1514 | CT 202 (same) | Low | 3 |
| ⭐⭐ | Unpoller | VM 100:9130 | CT 202 (same) | Low | 3 |
| ⭐⭐ | Pi-hole | VM 100:82 | CT 203 @ 10.16.1.53 | High | 4-5 |
| ⭐ | Sonarr | VM 100:8989 | CT 206 @ 10.16.1.56 | Low | 6 |
| ⭐ | Sabnzbd | VM 100:8080 | CT 207 @ 10.16.1.57 | Low | 6 |
| ⭐ | Transmission | VM 100:9091 | CT 208 @ 10.16.1.58 | Low | 6 |
| - | Speedtest Tracker | VM 100:8088 | CT 209 @ 10.16.1.59 | Low | 7 |

### Keep in Docker (2 services)

| Service | Location | Reasoning | Action |
|---------|----------|-----------|--------|
| Cloudflared Tunnel | VM 100 | Stateless, auto-recovery, easy updates | Keep |
| Twingate Connector | VM 100 | Zero-trust connector, container-native | Research LXC compatibility |

### Remove/Decommission (11 services + 3 VMs)

| Service/VM | Current Location | Reason | When |
|------------|------------------|--------|------|
| Minecraft Server | VM 100:25565 | No longer needed | Week 1 |
| Homepage Dashboard | VM 100:3000 | Duplicate (keeping Homer) | Week 1 |
| Code-server | VM 100:8445 | No longer needed | Week 1 |
| Watchtower | VM 100 | Manual updates preferred | Week 1 |
| Portainer CE | VM 100:9443 | No longer needed | After migration |
| Portainer EE | VM 109:9443 | No longer needed | After migration |
| Vaultwarden | VM 109:9445 | No longer needed | Week 1 |
| CUPS Printing | VM 109 | No longer needed | Week 1 |
| OpenVPN-AS | VM 109:943,1194 | No longer needed | Week 1 |
| Nexterm | VM 109:6989 | No longer needed | Week 1 |
| Pi-hole Dev | VM 109:80 | Consolidate to production | Week 4 |
| **Traefik** | VM 100:80,443 | Replace with NPM | After Phase 2 |
| **VM 112** | deb-srv-plex | Old Plex VM (unused) | After verification |
| **VM 109** | docka | After removing all services | Week 8 |
| **VM 100** | dockc | After migration complete | Week 8 |

---

## Revised Phase Timeline

### Week 1: Quick Wins & Cleanup
**Goal:** Remove unused services, free up resources

1. **Stop and remove unused services on VM 109:**
   - Vaultwarden (no longer needed)
   - CUPS printing (no longer needed)
   - OpenVPN-AS (no longer needed)
   - Nexterm (no longer needed)

2. **Stop and remove on VM 100:**
   - Minecraft server (no longer needed)
   - Homepage dashboard (keeping Homer)
   - Code-server (no longer needed)
   - Watchtower (manual updates)

3. **Verify VM 112 is unused:**
   - Check if Plex traffic goes to CT 108 (plexpunnisher)
   - If confirmed unused, power off VM 112
   - Monitor for 1 week, then delete

**Outcome:** ~8 services removed, VM 109 almost empty, VM 112 potentially off

---

### Week 2: Foundation Services Migration

**Priority 1: Uptime Kuma** (Public-facing)
- Create LXC CT 201 @ 10.16.1.51
- Specs: 512 MB RAM, 5 GB disk, Debian 12
- Install Uptime Kuma (native or Docker)
- Export data from VM 100 Docker container
- Import into new LXC
- Update NPM proxy: uptime.gmdojo.tech → 10.16.1.51:3001
- Update Cloudflare Tunnel: status.gmdojo.tech → https://10.16.1.50 → NPM → Uptime Kuma
- Test internal and public access
- Monitor for 3 days
- Remove Docker container on VM 100

**Priority 2: Homer Dashboard**
- Create LXC CT 204 @ 10.16.1.54
- Specs: 256 MB RAM, 2 GB disk, Debian 12
- Install Homer (nginx + static files)
- Copy config from VM 100 Docker volume
- **Update all service URLs** from `*.local.getmassive.com.au` → `*.gmdojo.tech`
- Update NPM proxy: home.gmdojo.tech → 10.16.1.54:8080
- Test all links
- Monitor for 3 days
- Remove Docker container

**Priority 3: Gotify Notifications**
- Create LXC CT 205 @ 10.16.1.55
- Specs: 256 MB RAM, 2 GB disk, Debian 12
- Install Gotify
- Export SQLite database from VM 100
- Import into new LXC
- Update all services that send notifications to use new URL
- Create NPM proxy: gotify.gmdojo.tech → 10.16.1.55:80
- Test notifications from various services
- Monitor for 3 days
- Remove Docker container

**Outcome:** 3 key services migrated, NPM proxies tested and working

---

### Weeks 3-4: Monitoring Stack Migration

**Decision:** Single LXC for entire stack (recommended)

**Create Monitoring LXC CT 202 @ 10.16.1.52**
- Specs: 4 GB RAM, 50 GB disk, Debian 12
- Install all monitoring components:
  - Grafana (visualization)
  - Prometheus (metrics)
  - Loki (logs)
  - InfluxDB (time-series)
  - Promtail (log shipper)
  - Unpoller (UniFi metrics)
  - Telegraf (metrics collector) - **fix restart issue**

**Migration Process:**
1. Install all components on new LXC
2. Export Grafana dashboards (JSON)
3. Export InfluxDB databases
4. Configure Prometheus scrape targets
5. Configure Loki log sources
6. Update Promtail to ship logs to new Loki
7. Update Telegraf to send metrics to new InfluxDB
8. Configure Unpoller for UniFi controller
9. Import Grafana dashboards
10. Test all dashboards and data sources
11. Update NPM proxy: grafana.gmdojo.tech → 10.16.1.52:3000
12. Run both stacks in parallel for 1 week
13. Remove all 7 Docker containers from VM 100

**Outcome:** Complete monitoring infrastructure on LXC, 7 containers removed

---

### Weeks 4-5: DNS Migration (Critical)

**Pi-hole Consolidation & Migration**

**Current State:**
- Production Pi-hole: VM 100 @ 10.16.1.4:82
- Development Pi-hole: VM 109 @ 10.16.1.12:80
- DHCP handing out: 10.16.1.4 as DNS

**Target State:**
- Single Pi-hole: LXC CT 203 @ 10.16.1.53

**Migration Process:**
1. **Preparation (Day 1)**
   - Create LXC CT 203 @ 10.16.1.53
   - Specs: 512 MB RAM, 5 GB disk, Debian 12
   - Install Pi-hole
   - Export configuration from production Pi-hole (VM 100):
     - `/etc/pihole/custom.list` (local DNS records)
     - Blocklists configuration
     - DHCP settings (if used)
     - Whitelist/blacklist

2. **Import & Test (Day 2)**
   - Import all configuration into new LXC
   - Test DNS resolution: `dig @10.16.1.53 google.com`
   - Test local DNS: `dig @10.16.1.53 pve.gmdojo.tech`
   - Verify blocklists working
   - Compare query results between old (10.16.1.4) and new (10.16.1.53)

3. **Parallel Operation (Days 3-5)**
   - Update DHCP to hand out **both** DNS servers: `10.16.1.4, 10.16.1.53`
   - Monitor both Pi-hole query logs
   - Ensure new Pi-hole handling queries correctly

4. **Cutover (Day 6)**
   - Update DHCP to hand out **only**: `10.16.1.53`
   - Update `/etc/resolv.conf` on all VMs/LXCs to use 10.16.1.53
   - Test from multiple devices
   - Monitor for DNS resolution issues

5. **Cleanup (Day 7+)**
   - Monitor for 1 week
   - If stable, remove Docker Pi-hole containers from both VMs
   - Update NPM proxy: pihole.gmdojo.tech → 10.16.1.53:80

**Rollback Plan:**
- If issues arise, update DHCP back to 10.16.1.4
- Old Pi-hole still running until cleanup phase

**Outcome:** Single Pi-hole LXC, 2 Docker containers removed, critical DNS stable

---

### Weeks 6-7: Media Services Migration

**Sonarr (TV Automation)**
- Create LXC CT 206 @ 10.16.1.56
- Specs: 1 GB RAM, 20 GB disk, Debian 12
- Install Sonarr
- Export configuration and database from VM 100
- Import into LXC
- Update download client settings (Sabnzbd, Transmission)
- Update media library paths (TrueNAS mounts)
- Create NPM proxy: sonarr.gmdojo.tech → 10.16.1.56:8989
- Test with existing shows
- Monitor for 1 week
- Remove Docker container

**Sabnzbd (Usenet Downloader)**
- Create LXC CT 207 @ 10.16.1.57
- Specs: 512 MB RAM, 10 GB disk, Debian 12
- Install Sabnzbd
- Export configuration from VM 100
- Import into LXC
- Update Usenet server settings
- Update download paths (TrueNAS mounts)
- Create NPM proxy: sabnzbd.gmdojo.tech → 10.16.1.57:8080
- Test downloads
- Monitor for 1 week
- Remove Docker container

**Transmission (Torrent Client)**
- Create LXC CT 208 @ 10.16.1.58
- Specs: 512 MB RAM, 10 GB disk, Debian 12
- Install Transmission
- Export configuration from VM 100
- Import into LXC
- Update download paths (TrueNAS mounts)
- Create NPM proxy: transmission.gmdojo.tech → 10.16.1.58:9091
- Test downloads
- Monitor for 1 week
- Remove Docker container

**Outcome:** Media automation stack on LXCs, 3 containers removed

---

### Week 7: Utilities Migration

**Speedtest Tracker**
- Create LXC CT 209 @ 10.16.1.59
- Specs: 512 MB RAM, 5 GB disk, Debian 12
- Install Speedtest Tracker + MariaDB
- Export MariaDB database from VM 100
- Import into LXC
- Create NPM proxy: speedtest.gmdojo.tech → 10.16.1.59:80
- Test speedtests
- Remove 2 Docker containers (app + db)

**Outcome:** Utility services migrated, 2 more containers removed

---

### Week 8: Cleanup & Decommission

**VM 100 Cleanup:**
After all migrations complete, VM 100 should only have:
- Cloudflared tunnel (keep)
- Twingate connector (keep or evaluate)

**Options:**
1. **Keep VM 100 minimal** - 1 GB RAM, just for these 2 containers
2. **Move to VM 109** - Consolidate Docker hosts
3. **Move to LXC** - If cloudflared/twingate can run in LXC

**VM 109 Cleanup:**
After removing all services in Week 1, VM 109 should be empty.
- Power off VM 109
- Monitor for 1 week
- If no issues, delete VM 109

**VM 112 Decommission:**
- Confirm VM 112 is not being used (Plex is on CT 108)
- Power off VM 112
- Monitor for 1 week
- If no issues, delete VM 112

**Remove Traefik:**
- After all NPM proxies tested and working
- Stop Traefik container on VM 100
- Remove old `*.local.getmassive.com.au` domain entirely
- Clean up Traefik Docker volumes

**Final Portainer Removal:**
- Remove Portainer CE from VM 100
- Remove Portainer EE from VM 109 (if still exists)

**Outcome:** 2-3 VMs decommissioned, 6+ GB RAM freed, cleaner infrastructure

---

## LXC Resource Allocation

| VMID | Service | IP | RAM | Disk | Status |
|------|---------|----|----|------|--------|
| 200 | nginx-proxy-manager | 10.16.1.50 | 1 GB | 8 GB | ✅ Running |
| 201 | uptime-kuma | 10.16.1.51 | 512 MB | 5 GB | 📋 Week 2 |
| 202 | monitoring-stack | 10.16.1.52 | 4 GB | 50 GB | 📋 Week 3-4 |
| 203 | pihole | 10.16.1.53 | 512 MB | 5 GB | 📋 Week 4-5 |
| 204 | homer | 10.16.1.54 | 256 MB | 2 GB | 📋 Week 2 |
| 205 | gotify | 10.16.1.55 | 256 MB | 2 GB | 📋 Week 2 |
| 206 | sonarr | 10.16.1.56 | 1 GB | 20 GB | 📋 Week 6 |
| 207 | sabnzbd | 10.16.1.57 | 512 MB | 10 GB | 📋 Week 6 |
| 208 | transmission | 10.16.1.58 | 512 MB | 10 GB | 📋 Week 6 |
| 209 | speedtest-tracker | 10.16.1.59 | 512 MB | 5 GB | 📋 Week 7 |

**Total New LXC Resources:**
- RAM: ~8 GB
- Disk: ~117 GB
- Containers: 10 new LXCs (9 existing + 10 new = 19 total LXCs)

---

## Resource Impact Analysis

### Before Migration:
- VM 100: 6 GB RAM, 24 Docker containers
- VM 109: 2 GB RAM, 6 Docker containers (will be removed)
- VM 112: 2 GB RAM (will be removed if unused)
- 9 existing LXCs: ~5 GB RAM
- **Total: ~15 GB RAM**

### After Migration:
- VM 100: 1 GB RAM (2 containers only) or decommissioned
- 19 LXCs: ~13 GB RAM
- **Total: ~13-14 GB RAM**

### Net Impact:
- **RAM savings: 1-2 GB** (after decommissioning VMs)
- **Better resource distribution:** Individual LXC control
- **Improved isolation:** Security and stability
- **Easier management:** Individual service snapshots, backups, restarts

---

## Critical Success Factors

### 1. DNS Migration (Pi-hole)
- **Most critical:** DNS failure affects everything
- **Plan:** Parallel operation, gradual cutover
- **Rollback:** Keep old Pi-hole until fully stable

### 2. Monitoring Stack
- **Important:** Visibility into infrastructure
- **Plan:** Export all dashboards, parallel operation
- **Verify:** All data sources working before cutover

### 3. NPM Proxy Testing
- **Before each migration:** Test NPM proxy to old backend
- **After migration:** Update NPM to point to new LXC
- **Verify:** Both internal and external access working

### 4. Storage Mounts
- **Media services need TrueNAS mounts**
- **Verify:** LXCs can access NFS/SMB shares
- **Test:** Read/write permissions before migration

---

## Rollback Strategy

Each migration should maintain the Docker container for 1 week after LXC is live:

1. **LXC created and tested** ✅
2. **NPM proxy updated to new LXC** ✅
3. **Monitor for issues** (1 week)
4. **If issues:** Revert NPM proxy to Docker container
5. **If stable:** Remove Docker container

**Never remove a Docker container until the LXC replacement is proven stable.**

---

## Questions Remaining

1. **VM 107 (deb-util-01):** What utilities are running? (Needs user investigation with correct credentials)
2. **VM 112 (deb-srv-plex):** Confirm it's unused (Plex is on CT 108)
3. **Twingate Connector:** Can it run in LXC instead of Docker?
4. **Cloudflared Tunnel:** Move to LXC with systemd or keep in Docker?
5. **VM 100 final state:** Keep minimal Docker host or decommission entirely?

---

## Next Immediate Actions

1. ✅ **Week 1 cleanup starts NOW:**
   - Remove 8 unused services from VMs 100 & 109
   - Power off VM 112 if confirmed unused

2. **Week 2 begins after cleanup:**
   - Create Uptime Kuma LXC (CT 201)
   - Begin first migration

3. **Validate NPM proxies:**
   - Test all 8 configured proxy hosts
   - Verify backends are responding now that we know where they are

---

**Status:** Ready to begin Week 1 cleanup
**Timeline:** 8 weeks to complete full migration
**Risk:** Low (gradual approach with rollback capability)
