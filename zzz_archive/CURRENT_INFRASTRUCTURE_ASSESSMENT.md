# Current Infrastructure Assessment - November 2025

**Date:** 2025-11-16
**Assessment for:** LXC Migration Planning Post-Phase 1

---

## Summary

**Phase 1 Complete:** Nginx Proxy Manager infrastructure now operational
- NPM at 10.16.1.50 (CT 200) with `*.gmdojo.tech` SSL
- 8 proxy hosts configured (3 working: Proxmox, TrueNAS, NPM Admin)
- Foundation ready for service migration

**Inventory Complete:** Full Docker environment mapped
- **VM 100 (dockc @ 10.16.1.4):** 24 containers - Main application host
- **VM 109 (docka @ 10.16.1.12):** 6 containers - Security & VPN services
- **Total Services:** 30 Docker containers + 9 LXCs + 8 VMs = 47 services

---

## Current Running Services

### LXC Containers on pve-scratchy (10.16.1.22)

| VMID | Name | Status | Purpose | Migration Status |
|------|------|--------|---------|-----------------|
| 101 | watchyourlan | Running | Network monitoring | Keep as LXC |
| 104 | wikijs | Running | Documentation wiki | Keep as LXC |
| 106 | docker00 | Running | Docker host (3 containers) | **Migrate contents** |
| 108 | plexpunnisher | Running | Plex management | Keep as LXC |
| 113 | proxmox-datacenter-manager | Running | Proxmox management | Keep as LXC |
| 129 | crafty-s | Running | Minecraft server | Keep as LXC |
| 200 | nginx-proxy-manager | Running | **NEW** Reverse proxy | Keep as LXC ✅ |
| 900 | proxbackupsrv | Running | Backup server | Keep as LXC |
| 901 | tailscaler | Running | VPN/remote access | Keep as LXC |

**Total LXCs:** 9 (including new NPM)

### Docker Containers on VM 100 (dockc @ 10.16.1.4)

**Status:** Main application host with 24 containers

| Container | Image | Purpose | Port(s) | Migration Plan |
|-----------|-------|---------|---------|----------------|
| **twingate-opal-python** | twingate/connector:1 | Zero-trust network access | - | **Keep in Docker** or evaluate - Agree |
| **minecraft-server-dad-mc-1** | itzg/minecraft-server | Game server | 25565 | **Keep in Docker** (resource intensive) - delete no longer needed |
| **gotify** | gotify/server | Notification service | 8085 | **Migrate to LXC** (CT 205) - Agree |
| **watchtower** | containrrr/watchtower | Auto-update containers | - | **Remove** (manual updates better) - Agree |
| **uptime-kuma** | louislam/uptime-kuma:1 | Status monitoring | 3001 | **Migrate to LXC** (CT 201) ⭐ - Agree |
| **cloudflared-tunnel** | cloudflare/cloudflared | Public tunnel | - | **Keep in Docker** ⭐ - interested to investigate reasoning |
| **transmission** | linuxserver/transmission | Torrent client | 9091, 51413 | **Migrate to LXC** or keep - LXC |
| **traefik** | traefik:latest | Reverse proxy (OLD) | 80, 443 | **REMOVE** after NPM migration ⭐- Agree |
| **speedtest-tracker** | linuxserver/speedtest-tracker | Network speed monitoring | 8088, 8443 | **Migrate to LXC** - Agree |
| **speedtest2-db-1** | mariadb:10 | Database for speedtest | - | Migrate with speedtest - Agree |
| **sonarr** | linuxserver/sonarr | TV show automation | 8989 | **Migrate to LXC** or keep LXC |
| **sabnzbd** | linuxserver/sabnzbd | Usenet downloader | 8080 | **Migrate to LXC** or keep LXC |
| **pihole** | pihole/pihole | DNS + Ad blocking | 53, 82 | **Migrate to LXC** (CT 203) ⭐- Agree |
| **loki-stack-telegraf-1** | telegraf | Metrics collector | - | **Fix** (restarting) then migrate - Agree |
| **loki-stack-influxdb-1** | influxdb | Time-series database | 8086, 8089 | **Migrate to LXC** (monitoring stack) - Agree |
| **loki-stack-grafana-1** | grafana/grafana | Metrics visualization | 3002 | **Migrate to LXC** (CT 202) ⭐ - Agree |
| **loki-stack-prometheus-1** | prom/prometheus | Metrics collection | 9090 | **Migrate to LXC** (monitoring stack) - Agree |
| **loki-stack-promtail-1** | grafana/promtail | Log aggregation | 1514 | **Migrate to LXC** (monitoring stack) - Agree |
| **loki-stack-unpoller-1** | unpoller/unpoller | UniFi metrics | 9130, 37288 | **Migrate to LXC** (monitoring stack) - Agree |
| **loki-stack-loki-1** | grafana/loki | Log storage | 3100 | **Migrate to LXC** (monitoring stack) - Agree |
| **homer** | b4bz/homer | Dashboard | 81 | **Migrate to LXC** (CT 204) ⭐ - Agree |
| **homepage** | gethomepage/homepage | Alternative dashboard | 3000 | **Evaluate** - keep one dashboard - no longer needed |
| **code-server** | linuxserver/code-server | Web-based VS Code | 8445 | **Migrate to LXC** or remove - no longer needed |
| **portainer** | portainer/portainer-ce | Docker management | 8000, 9443 | **REMOVE** after migration ⭐ - Agree |

**Total:** 24 containers (6 priority migrations marked ⭐)

### Docker Containers on VM 109 (docka @ 10.16.1.12)

**Status:** Security & VPN services host with 6 containers

| Container | Image | Purpose | Port(s) | Migration Plan |
|-----------|-------|---------|---------|----------------|
| **vaultwarden** | vaultwarden/server | Password manager | 9445 | **Keep in Docker** or LXC (security sensitive) - no longer needed |
| **pihole** | pihole/pihole:development | DNS + Ad blocking (dev) | 53, 80 | **Consolidate** with other Pi-hole - - Agree |
| **cups** | chuckcharlie/cups-avahi-airprint | Network printing | - | **Keep in Docker** (driver dependencies). - no longer needed |
| **openvpn-as** | openvpn/openvpn-as | VPN server | 443, 943, 1194 | **Keep as VM/Docker** (security) - remove no longer needed |
| **nexterm-nexterm-1** | germannewsmaker/nexterm | Terminal access | 6989 | **Evaluate** purpose - no longer needed |
| **portainer** | portainer/portainer-ee | Docker management (Enterprise) | 8000, 9443 | **REMOVE** after migration |

**Total:** 6 containers

**Total Docker Containers Across All Hosts:** 30

### Virtual Machines on pve-scratchy

| VMID | Name | Status | RAM | Disk | IP | Purpose | Migration Plan |
|------|------|--------|-----|------|-----|---------|----------------|
| 100 | dockc | Running | 6 GB | 92 GB | 10.16.1.4 | **Main Docker host** (24 containers) | **Migrate all services** → LXCs, then decommission - Agree |
| 102 | Anisble-master | Running | 2 GB | 32 GB | - | Automation/orchestration | **Keep as VM** |
| 103 | zabbix | Running | 2 GB | 32 GB | - | Monitoring (alternative to Grafana) | **Evaluate** - May be redundant with Grafana stack - Agree |
| 105 | haosova-6.6 | Stopped | 4 GB | 32 GB | - | Home Assistant | **Evaluate** - Why stopped? Still needed? Keep it - it's the next project once the lab is stable |
| 107 | deb-util-01 | Running | 4 GB | 32 GB | - | Utility server | **Investigate** - What utilities? - we need to see what's running on that thing. |
| 109 | docka | Running | 2 GB | 100 GB | 10.16.1.12 | **Security Docker host** (6 containers) | **Selective migration** - VPN/Security stay - I think it will go |
| 110 | truenas-scale | Running | 8 GB | 32 GB | 10.16.1.6 | NAS (has own storage pools) | **Keep as VM** ✅ |
| 112 | deb-srv-plex | Running | 2 GB | 64 GB | - | Plex media server | **Investigate** - Is this being used? - I would like that moved to an LXC if we can - if move database into plexpunisher it would do the trick or just build new and update the db |

**Total VMs:** 8 (7 running, 1 stopped)
**VMs to Decommission:** VM 100 (after migration) - potentially VM 109 if VPN can move

---

## Key Findings

### 1. Docker Environment Fully Mapped ✅

**VM 100 (dockc @ 10.16.1.4)** - Main application host
- 24 Docker containers running
- Services: Monitoring stack (Grafana, Prometheus, Loki, InfluxDB), Media automation (Sonarr, Sabnzbd, Transmission), Infrastructure (Traefik, Pi-hole, Homer, Uptime Kuma), Utilities (Gotify, Speedtest, Code-server)
- Also hosts 10.16.1.50 VIP (keepalived for NPM HA?)
- **Migration Impact:** High - Most critical services here

**VM 109 (docka @ 10.16.1.12)** - Security & VPN services
- 6 Docker containers running
- Services: Security (Vaultwarden, OpenVPN-AS), Infrastructure (Pi-hole dev, CUPS printing), Management (Nexterm, Portainer EE)
- **Migration Impact:** Medium - Some services should stay in Docker/VM

### 2. NPM Migration Status (Phase 1)

✅ **Working Proxy Hosts:**
- pve.gmdojo.tech → Proxmox (10.16.1.22:8006)
- nas.gmdojo.tech → TrueNAS (10.16.1.6:443)
- npm.gmdojo.tech → NPM Admin (10.16.1.50:81)

⚠️ **Configured but backends not responding:**
- uptime.gmdojo.tech → 10.16.1.4:3001 ✅ Found (running on dockc)
- grafana.gmdojo.tech → 10.16.1.4:3002 ✅ Found (running on dockc)
- pihole.gmdojo.tech → 10.16.1.4:82 ✅ Found (running on dockc)
- home.gmdojo.tech → 10.16.1.4:81 ✅ Found (Homer running on dockc)
- status.gmdojo.tech → 10.16.1.4:3001 (public) ✅ Found

**Root Cause:** All backends are actually running! NPM proxies should work now. Need to test.

### 3. Reverse Proxy Migration Path

- **Old:** Traefik on VM 100 (10.16.1.4:80, 443) - Currently serving `*.local.getmassive.com.au`
- **New:** NPM on CT 200 (10.16.1.50:80, 443) - Now serving `*.gmdojo.tech`
- **Status:** Parallel operation confirmed ✅
- **Next Step:** Test NPM proxies, then decommission Traefik

### 4. Monitoring Stack Discovery ✅

Complete "Loki Stack" found on VM 100:
- **Grafana:** Port 3002 (visualization)
- **Prometheus:** Port 9090 (metrics)
- **Loki:** Port 3100 (logs)
- **InfluxDB:** Port 8086 (time-series DB)
- **Promtail:** Port 1514 (log shipper)
- **Unpoller:** Port 9130 (UniFi metrics)
- **Telegraf:** Restarting (needs fix)

**Decision:** Migrate entire stack to single "monitoring" LXC or keep as separate containers

### 5. Duplicate Services Identified

**Pi-hole:** 2 instances found
- VM 100 @ 10.16.1.4:82 (production)
- VM 109 @ 10.16.1.12:80 (development version)
- **Action:** Consolidate to single LXC instance

**Portainer:** 2 instances found
- VM 100 (Community Edition)
- VM 109 (Enterprise Edition)
- **Action:** Remove both after migration complete

**Dashboards:** 2 instances found
- Homer @ 10.16.1.4:81 (lightweight)
- Homepage @ 10.16.1.4:3000 (feature-rich)
- **Action:** Keep one, evaluate which is better

---

## Migration Strategy Recommendations

Based on the complete inventory, here's the recommended migration approach:

### Phase 2: Foundation Services Migration (Weeks 1-2)

**Priority 1: Uptime Kuma** (Public-facing, highest priority)
- **Current:** Docker on VM 100 @ 10.16.1.4:3001
- **Target:** LXC CT 201 @ 10.16.1.51
- **Why:** Currently accessible via Cloudflare Tunnel for public status page
- **Steps:**
  1. Create LXC CT 201 with Uptime Kuma
  2. Export data from Docker container
  3. Import into LXC
  4. Update NPM proxy to point to 10.16.1.51:3001
  5. Test internal access
  6. Update Cloudflare Tunnel to new backend
  7. Test public access at status.gmdojo.tech
  8. Monitor for 1 week before removing Docker container

**Priority 2: Homer Dashboard**
- **Current:** Docker on VM 100 @ 10.16.1.4:81
- **Target:** LXC CT 204 @ 10.16.1.54
- **Why:** Central navigation hub, frequently accessed
- **Steps:**
  1. Create LXC CT 204 with Homer
  2. Copy configuration from Docker volume
  3. Update all URLs from `*.local.getmassive.com.au` to `*.gmdojo.tech`
  4. Update NPM proxy to point to 10.16.1.54:8080
  5. Test and validate all links
  6. Decision: Keep or migrate to Homepage instead?

**Priority 3: Gotify Notifications**
- **Current:** Docker on VM 100 @ 10.16.1.4:8085
- **Target:** LXC CT 205 @ 10.16.1.55
- **Why:** Notification system used by other services
- **Steps:**
  1. Create LXC CT 205 with Gotify
  2. Export/import SQLite database
  3. Update all services to use new Gotify URL
  4. Create NPM proxy host
  5. Test notifications from various services

### Phase 3: Monitoring Stack Migration (Weeks 3-4)

**Complete Loki Stack Migration**
- **Current:** 7 containers on VM 100 (Grafana, Prometheus, Loki, InfluxDB, Promtail, Unpoller, Telegraf)
- **Target:** LXC CT 202 @ 10.16.1.52 (all-in-one) OR separate LXCs

**Option A: Single LXC (Recommended)**
- Easier to manage
- Data stays co-located
- 4 GB RAM, 50 GB disk
- Run all components in one container

**Option B: Separate LXCs**
- Grafana: CT 202 @ 10.16.1.52
- Prometheus/Loki/InfluxDB: CT 206 @ 10.16.1.56
- Better resource isolation
- More complex

**Migration Steps:**
1. Create monitoring LXC(s) with required specs
2. Export all Grafana dashboards
3. Export Prometheus data (or start fresh)
4. Export InfluxDB databases
5. Reconfigure Promtail, Telegraf, Unpoller to point to new endpoints
6. Import data into new stack
7. Update NPM proxy for grafana.gmdojo.tech
8. Test all dashboards and data sources
9. Monitor parallel operation for 1 week
10. Fix Telegraf restart issue during migration

### Phase 4: Infrastructure Services (Weeks 5-6)

**Pi-hole Consolidation & Migration**
- **Current:** 2 instances (VM 100 prod, VM 109 dev)
- **Target:** Single LXC CT 203 @ 10.16.1.53
- **Critical:** DNS service, requires careful migration
- **Steps:**
  1. Create LXC CT 203 with Pi-hole
  2. Export custom.list and blocklists from production instance
  3. Import configuration
  4. Test DNS resolution before switching
  5. Update DHCP to hand out 10.16.1.53 as DNS
  6. Monitor for issues
  7. Decommission both Docker instances after 1 week stable
  8. Update NPM proxy for pihole.gmdojo.tech

**Speedtest Tracker + Database**
- **Current:** 2 containers on VM 100 (app + mariadb)
- **Target:** LXC CT 207 @ 10.16.1.57
- **Why:** Self-contained stack, easy migration
- **Steps:**
  1. Create LXC with both speedtest-tracker and MariaDB
  2. Export MariaDB data
  3. Import and test
  4. Create NPM proxy host

### Phase 5: Media/Download Services (Weeks 7-8)

**Decision Point:** Keep in Docker or migrate to LXC?

Services to evaluate:
- Sonarr (TV show automation)
- Sabnzbd (Usenet downloader)
- Transmission (Torrent client)

**Recommendation:** Keep in Docker on VM 100 initially
- These are working well
- Heavy I/O operations (suited for Docker volumes)
- Connected to Plex media server
- Can migrate later if needed

### Phase 6: Security Services (Week 9)

**Keep on VM 109:**
- **Vaultwarden:** Password manager (security-sensitive, stay in Docker)
- **OpenVPN-AS:** VPN server (network-sensitive, stay in Docker/VM)
- **CUPS:** Network printing (driver dependencies)

**These should NOT migrate to LXC** - security and network access requirements

### Phase 7: Cleanup & Decommission (Week 10+)

**Remove:**
1. Traefik container on VM 100 (after all NPM proxies working)
2. Both Portainer instances (no longer needed)
3. Watchtower (manual updates better)
4. Duplicate Pi-hole instances
5. One of the two dashboards (Homer or Homepage)

**Decommission VM 100:**
- After all critical services migrated
- Keep only: Cloudflared tunnel, Minecraft server, Twingate connector, Media stack (Sonarr/Sabnzbd/Transmission)
- Or migrate remaining to VM 109 and decommission entirely

**Potential Savings:**
- VM 100: 6 GB RAM, 92 GB disk
- Reduced to: ~20 LXC containers @ ~500MB each = 10 GB RAM total
- **Net savings:** Negative in RAM (trade-off for better resource distribution)
- **Benefit:** Better isolation, easier management, individual service control

---

## Migration Priority Summary

| Priority | Service | Current Location | Target LXC | Impact | Complexity | Timeline |
|----------|---------|------------------|-----------|--------|------------|----------|
| ⭐⭐⭐ | Uptime Kuma | VM 100:3001 | CT 201 | High (public) | Low | Week 1 |
| ⭐⭐⭐ | Homer Dashboard | VM 100:81 | CT 204 | High (frequent use) | Low | Week 1 |
| ⭐⭐⭐ | Gotify | VM 100:8085 | CT 205 | Medium (notifications) | Low | Week 2 |
| ⭐⭐ | Monitoring Stack | VM 100 (7 containers) | CT 202 | High (observability) | High | Weeks 3-4 |
| ⭐⭐ | Pi-hole | VM 100:82 + VM 109:80 | CT 203 | Critical (DNS) | Medium | Weeks 5-6 |
| ⭐ | Speedtest Tracker | VM 100:8088 | CT 207 | Low | Low | Week 6 |
| ⭐ | Code-server | VM 100:8445 | CT 208 | Low | Low | Week 7 |
| - | Media Stack | VM 100 | Stay Docker | Low | - | - |
| - | Security Services | VM 109 | Stay Docker/VM | Critical | - | - |
| ⛔ | Traefik | VM 100:80,443 | **REMOVE** | - | Low | After Phase 2 |
| ⛔ | Portainer x2 | VM 100 + VM 109 | **REMOVE** | - | Low | After Phase 7 |

---

## LXC IP Allocation Plan (10.16.1.50-99)

| VMID | Service | IP | RAM | Disk | Status |
|------|---------|----|-----|------|--------|
| 200 | nginx-proxy-manager | 10.16.1.50 | 1 GB | 8 GB | ✅ Running (Phase 1) |
| 201 | uptime-kuma | 10.16.1.51 | 512 MB | 5 GB | 📋 Phase 2 |
| 202 | monitoring-stack | 10.16.1.52 | 4 GB | 50 GB | 📋 Phase 3 |
| 203 | pihole | 10.16.1.53 | 512 MB | 5 GB | 📋 Phase 4 |
| 204 | homer | 10.16.1.54 | 256 MB | 2 GB | 📋 Phase 2 |
| 205 | gotify | 10.16.1.55 | 256 MB | 2 GB | 📋 Phase 2 |
| 206 | prometheus (if separate) | 10.16.1.56 | 2 GB | 20 GB | ⚙️ Optional |
| 207 | speedtest-tracker | 10.16.1.57 | 512 MB | 5 GB | 📋 Phase 4 |
| 208 | code-server | 10.16.1.58 | 1 GB | 10 GB | 📋 Phase 5 |
| 209-220 | | | | | Reserved for future services |

**Total Estimated Resources (New LXCs):**
- RAM: ~7-9 GB (depending on monitoring approach)
- Disk: ~85-107 GB
- Containers: 8-9 new LXCs

---

## Questions to Research

### Answered ✅:
1. ~~What's on VM 100 (dockc)?~~ - 24 containers identified
2. ~~What's on VM 109 (docka)?~~ - 6 containers identified
3. ~~Where is Grafana/monitoring stack?~~ - Complete Loki stack on VM 100

### Still Need Answers:
4. **VM 112 (deb-srv-plex):** Is Plex actually running here? Or is it on another host?
5. **VM 103 (zabbix):** Is this still in use? Redundant with Grafana?
6. **VM 105 (Home Assistant):** Why stopped? Migration candidate or decommission?
7. **VM 107 (deb-util-01):** What utilities are running here?
8. **Keepalived/VIP:** Is 10.16.1.50 configured as HA VIP on VM 100? Or just secondary IP?

---

## Next Immediate Actions

1. ✅ **Complete infrastructure inventory** - DONE
2. **Test NPM proxy hosts** - All backends found, should work now
3. **Fix Telegraf** restart issue on VM 100
4. **Begin Phase 2 planning** - Create detailed playbooks for Uptime Kuma migration
5. **Update Homer/Homepage URLs** from old domain to new domain (can do before migration)
6. **Document Phase 1 success** - Update SESSION_STATE with current status

---

## Resource Impact Analysis

**Current State:**
- VM 100: 6 GB RAM, 24 Docker containers
- VM 109: 2 GB RAM, 6 Docker containers
- 9 existing LXCs: ~5 GB RAM total
- **Total: 13 GB RAM + VM overhead**

**After Migration:**
- VM 100: 2-3 GB RAM (Minecraft, Cloudflared, Twingate, Media stack only)
- VM 109: 2 GB RAM (unchanged - security services)
- 17-18 LXCs: ~12-14 GB RAM
- **Total: 16-19 GB RAM (3-6 GB increase)**

**Trade-offs:**
- ➕ Better isolation and security
- ➕ Individual service control (start/stop/restart)
- ➕ Easier backups and snapshots
- ➕ Better resource visibility
- ➖ Slightly higher RAM usage (LXC overhead)
- ➖ More containers to manage
- ➕ Can decommission VM 100 eventually (or reduce to minimal size)

---

**Status:** ✅ **Assessment Complete - Full inventory documented**
**Next Step:** Test NPM proxy hosts and begin Phase 2 planning
