# Docker to LXC Migration Plan - November 2025

**Date:** 2025-11-16
**Objective:** Migrate from Docker containers to LXC containers + switch to gmdojo.tech domain
**Current State:** 25 Docker containers on VM 100 (dockc), 8 existing LXC containers
**Target Domain:** `gmdojo.tech` (replacing `*.local.getmassive.com.au`)

---

## Executive Summary

### Current Architecture
- **Platform:** Docker containers on VM 100 (10.16.1.4)
- **Reverse Proxy:** Traefik
- **Domain:** `*.local.getmassive.com.au`
- **SSL:** Let's Encrypt via Cloudflare DNS challenge
- **Container Count:** 25 Docker containers
- **Storage Used:** 35 GB in /dockerland

### Target Architecture
- **Platform:** LXC containers on Proxmox
- **Reverse Proxy:** Traefik (keep as LXC) or migrate to Nginx Proxy Manager
- **Domain:** `*.gmdojo.tech` (simpler, shorter)
- **SSL:** Let's Encrypt via Cloudflare DNS challenge
- **Container Count:** ~20-25 LXC containers
- **Storage:** Native Proxmox storage (more efficient)

---

## Why Docker → LXC?

### Advantages of LXC

**Performance:**
- ✅ **Lower overhead** - System containers vs application containers
- ✅ **Better resource efficiency** - Native systemd, no Docker daemon
- ✅ **Direct hardware access** - Better I/O performance
- ✅ **Faster startup** - No container runtime overhead

**Management:**
- ✅ **Proxmox native** - Integrated backups, snapshots, replication
- ✅ **Better monitoring** - Native Proxmox metrics
- ✅ **Simpler networking** - Direct bridge access, no NAT layers
- ✅ **Easier troubleshooting** - Standard Linux tools

**Security:**
- ✅ **OS-level isolation** - Unprivileged containers
- ✅ **AppArmor/SELinux** - Built-in security profiles
- ✅ **Resource limits** - Proxmox cgroup controls

**Operational:**
- ✅ **Unified platform** - Everything in Proxmox
- ✅ **Better backups** - Proxmox Backup Server integration
- ✅ **Live migration** - Move between hosts without downtime
- ✅ **HA support** - High availability clustering

### Disadvantages to Consider

**Complexity:**
- ⚠️ **More containers** - One service per LXC (like VMs)
- ⚠️ **Manual configuration** - No docker-compose.yml convenience
- ⚠️ **Update management** - Need to handle OS updates per container

**Portability:**
- ⚠️ **Less portable** - Docker images work anywhere, LXC is Proxmox-specific
- ⚠️ **No Docker Hub** - Can't pull pre-built images easily

**Learning Curve:**
- ⚠️ **Different paradigm** - System containers vs application containers
- ⚠️ **More Linux knowledge** - Need to configure services manually

---

## Current Docker Container Inventory

### Category 1: Core Infrastructure (Keep as LXC Priority)

| Container | Image | Purpose | LXC Complexity |
|-----------|-------|---------|----------------|
| **traefik** | traefik:latest | Reverse proxy | Medium (critical) |
| **uptime-kuma** | louislam/uptime-kuma:1 | Monitoring | Low |
| **gotify** | gotify/server:latest | Notifications | Low |
| **pihole** | pihole/pihole:latest | DNS/Ad blocking | Low |
| **cloudflared-tunnel** | cloudflare/cloudflared | Public access | Low |

### Category 2: Monitoring & Metrics (Consolidate)

| Container | Image | Purpose | LXC Complexity |
|-----------|-------|---------|----------------|
| **grafana** | grafana/grafana:latest | Dashboards | Low |
| **prometheus** | prom/prometheus:latest | Metrics | Medium |
| **influxdb** | influxdb:latest | Time-series DB | Low |
| **telegraf** | telegraf | Metrics collector | Low |
| **promtail** | grafana/promtail:2.9.0 | Log collector | Low |

**Recommendation:** Consolidate into 1-2 LXCs (monitoring stack)

### Category 3: Media Services (Convert to LXC)

| Container | Image | Purpose | LXC Complexity |
|-----------|-------|---------|----------------|
| **sonarr** | linuxserver/sonarr | TV management | Low |
| **sabnzbd** | linuxserver/sabnzbd | Usenet downloader | Low |
| **transmission** | linuxserver/transmission | Torrent client | Low |

### Category 4: Application Services

| Container | Image | Purpose | LXC Complexity |
|-----------|-------|---------|----------------|
| **minecraft-server** | itzg/minecraft-server | Game server | Medium |
| **speedtest-tracker** | linuxserver/speedtest-tracker | Network testing | Low |
| **speedtest2-db** | mariadb:10 | Database | Low |
| **nginx-nginx** | nginxdemos/nginx-hello | Test service | Low |

### Category 5: Management Tools

| Container | Image | Purpose | LXC Complexity |
|-----------|-------|---------|----------------|
| **watchtower** | containrrr/watchtower | Auto-updates | Low (or skip) |
| **twingate-opal-python** | twingate/connector:1 | VPN connector | Medium |

### Summary
- **Total:** 25 Docker containers
- **Convert to LXC:** ~18-20 containers (some can be consolidated)
- **Skip conversion:** Watchtower (not needed for LXC)

---

## Domain Migration: getmassive.com.au → gmdojo.tech

### Current URLs (Too Long)
```
https://proxmox.local.getmassive.com.au
https://uptime-kuma.local.getmassive.com.au
https://grafana.local.getmassive.com.au
```
**Character count:** 40+ characters!

### Proposed New URLs (Much Shorter)
```
https://pve.gmdojo.tech         (Proxmox)
https://uptime.gmdojo.tech      (Uptime Kuma)
https://grafana.gmdojo.tech     (Grafana)
https://plex.gmdojo.tech        (Plex)
https://sonarr.gmdojo.tech      (Sonarr)
```
**Character count:** 20-25 characters

### URL Naming Convention

**Infrastructure:**
- `pve.gmdojo.tech` - Proxmox VE (scratchy)
- `pve2.gmdojo.tech` - Proxmox VE (itchy, standby)
- `nas.gmdojo.tech` - TrueNAS
- `fw.gmdojo.tech` - OPNsense firewall
- `vpn.gmdojo.tech` - VPN gateway

**Monitoring:**
- `uptime.gmdojo.tech` - Uptime Kuma
- `grafana.gmdojo.tech` - Grafana
- `metrics.gmdojo.tech` - Prometheus

**Applications:**
- `plex.gmdojo.tech` - Plex Media Server
- `sonarr.gmdojo.tech` - Sonarr
- `sabnzbd.gmdojo.tech` - SABnzbd
- `transmission.gmdojo.tech` - Transmission
- `pihole.gmdojo.tech` - Pi-hole
- `homer.gmdojo.tech` - Homer dashboard

**Admin Tools:**
- `traefik.gmdojo.tech` - Traefik dashboard
- `portainer.gmdojo.tech` - Portainer
- `vault.gmdojo.tech` - Vaultwarden

**External/Public:**
- `status.gmdojo.tech` - Public status page (Cloudflare tunnel)
- `home.gmdojo.tech` - Public homepage (if needed)

---

## Migration Strategy Options

### Option 1: Big Bang Migration (Not Recommended)
- Stop all Docker containers
- Create all LXC containers at once
- Migrate data
- Reconfigure everything
- Start services

**Risk:** High (everything down at once)
**Time:** 8-16 hours of downtime
**Rollback:** Difficult

### Option 2: Gradual Service-by-Service Migration (Recommended)
- Keep Docker running
- Create LXC containers one at a time
- Migrate data per service
- Switch DNS/Traefik routing
- Verify and move to next service
- Decommission Docker VM when complete

**Risk:** Low (one service at a time)
**Time:** 2-4 weeks, minimal downtime per service
**Rollback:** Easy (just switch DNS back)

### Option 3: Parallel Infrastructure (Safest, Requires Resources)
- Build complete LXC infrastructure alongside Docker
- Migrate data in background
- Test thoroughly
- Switch DNS/routing all at once
- Keep Docker VM for 2 weeks as backup

**Risk:** Very low (full rollback possible)
**Time:** 1 week setup + 2 weeks validation
**Rollback:** Instant (just change DNS)

---

## Recommended Approach: Option 2 (Gradual Migration)

### Phase 1: Foundation (Week 1)

**1.1: Domain Setup**
```bash
# Transfer gmdojo.tech to Cloudflare
# Add to Cloudflare account: 3993eb0547e077e081089690928540d7
# Create DNS records pointing to 10.16.1.4 (initially)
```

**DNS Records:**
```
*.gmdojo.tech       A       10.16.1.4
*.local.gmdojo.tech A       10.16.1.4  (for internal only)
```

**1.2: Traefik Configuration Update**
- Keep existing Traefik Docker container
- Add new routes for `*.gmdojo.tech`
- Keep old routes for `*.local.getmassive.com.au`
- Both domains work during migration

**1.3: SSL Certificate Setup**
```yaml
# Update Traefik to request new wildcard cert
certificatesResolvers:
  cloudflare:
    acme:
      email: dp@getmassive.com.au
      storage: acme.json
      dnsChallenge:
        provider: cloudflare

# Add new domain to TLS config
tls:
  domains:
    - main: gmdojo.tech
      sans:
        - "*.gmdojo.tech"
    # Keep old domain during migration
    - main: local.getmassive.com.au
      sans:
        - "*.local.getmassive.com.au"
```

### Phase 2: Pilot Migration - Non-Critical Service (Week 1)

**Choose:** Uptime Kuma (low risk, self-contained)

**Steps:**
1. Create LXC container on Proxmox
2. Install Uptime Kuma natively or via Docker (your choice)
3. Export data from Docker Uptime Kuma
4. Import to LXC Uptime Kuma
5. Update Traefik to route `uptime.gmdojo.tech` → new LXC
6. Test thoroughly
7. Keep Docker version running as backup for 48 hours
8. Remove Docker version after validation

### Phase 3: Core Services Migration (Week 2)

**Order:**
1. **Monitoring stack** (Grafana, Prometheus, InfluxDB)
   - Create single "monitoring" LXC or separate LXCs
   - Migrate databases and configs
2. **Pi-hole** (DNS critical, careful migration)
   - Create LXC, install Pi-hole
   - Export settings from Docker
   - Switch DNS gradually (test first)
3. **Gotify** (notifications)
   - Simple migration, just database

### Phase 4: Media Services (Week 3)

**Order:**
1. **SABnzbd** (downloader, data-heavy)
   - Create LXC
   - Mount NFS/CIFS to download locations
   - Migrate config and queue
2. **Sonarr** (depends on SABnzbd)
   - Create LXC
   - Migrate database (critical!)
   - Test integration with SABnzbd
3. **Transmission** (torrent client)
   - Create LXC
   - Migrate settings and resume data

### Phase 5: Reverse Proxy Migration (Week 4)

**Decision Point:** Keep Traefik or switch to Nginx Proxy Manager?

**Option A: Keep Traefik in LXC**
- Create dedicated "traefik" LXC
- Migrate config.yml
- Update all backend IPs to point to new LXCs

**Option B: Switch to Nginx Proxy Manager**
- Easier GUI management
- Better for LXC architecture
- Less YAML editing

### Phase 6: Cleanup & Decommission

1. Verify all services migrated
2. Update bookmarks/documentation
3. Remove old DNS records for `*.local.getmassive.com.au`
4. Snapshot Docker VM (one final backup)
5. Shut down Docker VM
6. Wait 2 weeks
7. Delete Docker VM and free resources

---

## Technical Implementation Details

### LXC Container Template

**Base Template:** Debian 12 or Ubuntu 22.04

**Standard LXC Configuration:**
```bash
# Example: Create Uptime Kuma LXC
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
    --hostname uptime-kuma \
    --memory 1024 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=10.16.1.50/24,gw=10.16.1.1 \
    --rootfs local-lvm:8 \
    --unprivileged 1 \
    --features nesting=1 \
    --onboot 1 \
    --startup order=10

# Start and configure
pct start 200

# Enter container
pct enter 200

# Install service (example: Uptime Kuma from source)
apt update && apt upgrade -y
apt install -y curl git nodejs npm
git clone https://github.com/louislam/uptime-kuma.git /opt/uptime-kuma
cd /opt/uptime-kuma
npm ci --production
npm run setup

# Create systemd service
cat > /etc/systemd/system/uptime-kuma.service <<EOF
[Unit]
Description=Uptime Kuma
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/uptime-kuma
ExecStart=/usr/bin/node server/server.js
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl enable --now uptime-kuma
```

### LXC IP Addressing Plan

**New IP Range:** 10.16.1.50-99 (LXC services)

| CTID | Service | IP | Memory | Cores |
|------|---------|-----|---------|-------|
| 200 | traefik | 10.16.1.50 | 1 GB | 2 |
| 201 | uptime-kuma | 10.16.1.51 | 1 GB | 1 |
| 202 | grafana | 10.16.1.52 | 2 GB | 2 |
| 203 | prometheus | 10.16.1.53 | 2 GB | 2 |
| 204 | influxdb | 10.16.1.54 | 2 GB | 2 |
| 205 | pihole | 10.16.1.55 | 512 MB | 1 |
| 206 | gotify | 10.16.1.56 | 512 MB | 1 |
| 207 | sonarr | 10.16.1.57 | 1 GB | 2 |
| 208 | sabnzbd | 10.16.1.58 | 2 GB | 2 |
| 209 | transmission | 10.16.1.59 | 1 GB | 2 |
| 210 | minecraft | 10.16.1.60 | 4 GB | 4 |

### Data Migration Strategies

**Strategy 1: Volume Mounts**
```bash
# From Docker volume to LXC
docker cp uptime-kuma:/app/data /tmp/uptime-data
pct push 201 /tmp/uptime-data /opt/uptime-kuma/data -recursive
```

**Strategy 2: Bind Mounts (if using NFS/CIFS)**
```bash
# Add to LXC config
pct set 208 -mp0 /mnt/pve/nas-downloads,mp=/downloads

# No data migration needed, just remount
```

**Strategy 3: Database Export/Import**
```bash
# Example: Grafana SQLite database
docker exec grafana sqlite3 /var/lib/grafana/grafana.db .dump > grafana-backup.sql
pct exec 202 -- sqlite3 /var/lib/grafana/grafana.db < grafana-backup.sql
```

### Traefik Configuration for LXC Backends

**Old (Docker):**
```yaml
http:
  routers:
    uptime-kuma:
      rule: "Host(`uptime-kuma.local.getmassive.com.au`)"
      service: uptime-kuma
  services:
    uptime-kuma:
      loadBalancer:
        servers:
          - url: "http://uptime-kuma:3001"  # Docker container name
```

**New (LXC):**
```yaml
http:
  routers:
    uptime-kuma:
      rule: "Host(`uptime.gmdojo.tech`)"  # New domain
      service: uptime-kuma
  services:
    uptime-kuma:
      loadBalancer:
        servers:
          - url: "http://10.16.1.51:3001"  # LXC IP address
```

---

## Cloudflare DNS Configuration

### Current DNS (getmassive.com.au)
```
# Internal only (Pi-hole)
*.local.getmassive.com.au  A  10.16.1.4
```

### New DNS (gmdojo.tech)

**Option A: Internal Only (Pi-hole)**
```
*.gmdojo.tech  A  10.16.1.50  (new Traefik LXC)
```

**Option B: Split DNS (Internal + Public)**
```
# Cloudflare (public internet)
status.gmdojo.tech  CNAME  d4b4b44c-97d0-46f3-8890-2f3d6040231b.cfargotunnel.com
home.gmdojo.tech    CNAME  d4b4b44c-97d0-46f3-8890-2f3d6040231b.cfargotunnel.com

# Pi-hole (internal LAN)
*.gmdojo.tech  A  10.16.1.50
```

**Option C: All Internal (Most Secure)**
```
# Cloudflare (public) - Nothing public
# Pi-hole (internal LAN) - Everything internal via Tailscale
*.gmdojo.tech  A  10.16.1.50
```

---

## Resource Comparison

### Current (Docker on VM 100)
- **VM RAM:** 8 GB allocated
- **VM Cores:** 4 cores
- **VM Storage:** 100 GB (35 GB used)
- **Container Overhead:** Docker daemon + overlay network

### Projected (LXC Containers)
- **Total RAM:** 20 GB across 10-15 LXCs (more flexible allocation)
- **Total Cores:** 20-25 cores across LXCs (CPU limits as needed)
- **Total Storage:** 80-100 GB (more efficient, no Docker layers)
- **Container Overhead:** Minimal (native LXC)

**Resource Savings:**
- More granular resource control
- No Docker daemon overhead
- Better memory efficiency (no image layers)
- Easier to scale individual services

---

## Risk Assessment

### High Risk Items
1. **DNS/Pi-hole Migration** - Critical service, could break name resolution
2. **Traefik Migration** - Single point of failure, all services depend on it
3. **Database Migrations** - Data loss potential (Grafana, Sonarr, etc.)

### Mitigation Strategies
1. **DNS:** Migrate during low-usage time, keep backup DNS (1.1.1.1)
2. **Traefik:** Keep Docker version running, test LXC version in parallel
3. **Databases:** Full backups before migration, test restores

### Rollback Procedures

**Per-Service Rollback:**
```bash
# Switch Traefik routing back to Docker container
# Update config.yml
# Restart Traefik
docker restart traefik
```

**Full Rollback:**
```bash
# Start Docker VM
qm start 100

# Update DNS to point to 10.16.1.4
# Revert Traefik config
```

---

## Testing Checklist

**Per Service:**
- [ ] Service starts correctly
- [ ] Service accessible via new URL (gmdojo.tech)
- [ ] SSL certificate valid
- [ ] All features working (login, uploads, etc.)
- [ ] Data migrated successfully
- [ ] Performance acceptable
- [ ] Logs clean (no errors)
- [ ] Auto-start on boot enabled
- [ ] Backup configured in Proxmox

---

## Timeline & Milestones

### Week 1: Foundation
- [ ] Transfer gmdojo.tech to Cloudflare
- [ ] Update Traefik with dual domains
- [ ] Request new SSL certificates
- [ ] Test DNS resolution
- [ ] Migrate Uptime Kuma (pilot)

### Week 2: Core Services
- [ ] Migrate monitoring stack (Grafana, Prometheus, InfluxDB)
- [ ] Migrate Pi-hole
- [ ] Migrate Gotify
- [ ] Update bookmarks with new URLs

### Week 3: Media Services
- [ ] Migrate SABnzbd
- [ ] Migrate Sonarr
- [ ] Migrate Transmission
- [ ] Test download workflows

### Week 4: Finalization
- [ ] Migrate Traefik to LXC (or NPM)
- [ ] Update all service IPs in configs
- [ ] Remove old DNS records
- [ ] Snapshot Docker VM
- [ ] Shut down Docker VM

### Week 6: Cleanup
- [ ] Verify 2 weeks of stable operation
- [ ] Delete Docker VM
- [ ] Update documentation
- [ ] Commit changes to git

---

## Alternative: Keep Hybrid Approach

**Not recommended, but possible:**
- Keep Traefik + critical services in Docker
- Move resource-heavy services to LXC (Plex, media stack)
- Use new domain (gmdojo.tech) for both

**Pros:**
- Less work
- Docker convenience for small services
- LXC performance for heavy services

**Cons:**
- Complexity of managing both
- Defeats purpose of consolidation
- Harder to troubleshoot

---

## Questions to Answer Before Starting

1. **Do you own gmdojo.tech already?**
   - If not, register it first
   - Transfer to Cloudflare DNS

2. **Reverse proxy preference?**
   - Keep Traefik (YAML config, powerful)
   - Switch to Nginx Proxy Manager (GUI, easier)
   - Use Caddy (auto-SSL, simple)

3. **Service consolidation?**
   - Separate LXC per service (cleaner, more containers)
   - Consolidate related services (fewer containers, more complex)

4. **Public exposure strategy?**
   - Keep Cloudflare tunnel for status page only
   - Expose more services publicly
   - Keep everything internal via Tailscale

5. **Resource allocation?**
   - Create all LXCs on scratchy
   - Distribute across scratchy and itchy
   - Keep Docker VM running in parallel

6. **Backup strategy?**
   - Proxmox Backup Server (full LXC backups)
   - Application-level backups (databases, configs)
   - Both

---

## Recommendation Summary

**My recommendation:**

1. **Register/transfer gmdojo.tech** to Cloudflare
2. **Start with gradual migration** (Option 2)
3. **Keep Traefik** (you already know it well)
4. **Separate LXC per service** (cleaner architecture)
5. **Migrate in this order:**
   - Uptime Kuma (pilot)
   - Monitoring stack (Grafana, Prometheus, InfluxDB)
   - Media services (Sonarr, SABnzbd)
   - Pi-hole (careful!)
   - Traefik last (after all backends migrated)
6. **Keep both domains working** during migration
7. **Use new gmdojo.tech domain** as primary going forward
8. **Deprecate old domain** after 30 days of stable operation

**Benefits:**
- ✅ Shorter URLs (gmdojo.tech vs getmassive.com.au)
- ✅ Better performance (LXC vs Docker)
- ✅ Native Proxmox integration
- ✅ Lower resource overhead
- ✅ Easier management (Proxmox GUI)
- ✅ Better backups (PBS integration)

**Timeline:** 4-6 weeks with minimal downtime per service

---

**Next Steps:**
1. Confirm gmdojo.tech ownership/registration
2. Choose reverse proxy (keep Traefik or switch)
3. Choose migration approach (I recommend gradual)
4. Start with domain setup and Traefik dual-domain config
5. Pilot migration with Uptime Kuma

---

**Status:** Planning phase, awaiting user decisions
**Estimated Effort:** 40-60 hours over 4-6 weeks
**Risk Level:** Medium (manageable with gradual approach)
**Reversibility:** High (easy to rollback per service)
