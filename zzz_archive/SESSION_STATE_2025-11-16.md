# Session State - November 16, 2025

**Date:** 2025-11-16
**Time:** Session interrupted for reboot
**Status:** Phase 1 planning complete, ready to begin implementation

---

## Current Project: Docker → LXC Migration + Domain Change

### Decisions Made

1. ✅ **Domain:** gmdojo.tech (registered, DNS with Cloudflare)
2. ✅ **Reverse Proxy:** Nginx Proxy Manager (GUI-based)
3. ✅ **Public Exposure:** Only Uptime Kuma via Cloudflare tunnel

### Key Infrastructure Details

**Cloudflare Account:**
- Account ID: `3993eb0547e077e081089690928540d7`
- DNS API Token: `aGSMUr8pQcAH4vuueTVCfyENElLKRUGVwMmNDIPn`
- Active Tunnel ID: `d4b4b44c-97d0-46f3-8890-2f3d6040231b` (CT 106 @ 10.16.1.40)

**Current Docker Environment:**
- Host: VM 100 (dockc) @ 10.16.1.4
- Containers: 25 Docker containers
- Reverse Proxy: Traefik (Docker)
- Domain: `*.local.getmassive.com.au`
- Storage: 35 GB used in /dockerland

**Target LXC Environment:**
- NPM LXC: CT 200 @ 10.16.1.50 (planned)
- Domain: `*.gmdojo.tech`
- LXC IP Range: 10.16.1.50-99

**Pi-hole:**
- Location: Docker container @ 10.16.1.4:82
- API Key: [User was providing this when interrupted]
- Will need to add DNS: `*.gmdojo.tech → 10.16.1.50`

---

## Documentation Created This Session

### 1. REMOTE_ACCESS_STRATEGY.md
- Solution for dynamic IP + no port forwarding
- Cloudflare Tunnel + Tailscale architecture
- Traefik SSL via DNS challenge (no inbound port 80 needed)
- Certificate expires: Feb 13, 2026

### 2. DOCKER_TO_LXC_MIGRATION_PLAN.md
- Complete analysis of 25 Docker containers
- LXC migration strategy (3 options)
- Resource comparison
- Risk assessment
- Timeline: 4-6 weeks gradual migration

### 3. PHASE1_NPM_MIGRATION.md
- Detailed Phase 1 implementation steps
- NPM LXC setup (CT 200 @ 10.16.1.50)
- DNS configuration (Pi-hole + Cloudflare)
- SSL certificate setup via NPM GUI
- Cloudflare tunnel update for `status.gmdojo.tech`
- Timeline: 2-4 hours

---

## Previous Completed Work (From Earlier Sessions)

### Network Consolidation
- Identified duplicate Tailscale/Cloudflare tunnels
- Disabled rova CT 111 (tailscale) - monitoring for 2 weeks
- Stopped rova CT 113 (cloudflared) - monitoring 24-48 hours
- Removed empty /dockerland/cloudflared directory
- Removed VM 110 backup lock

### Infrastructure Validation
- Validated Traefik setup on 10.16.1.4
- 17 services configured via Traefik
- SSL via Cloudflare DNS challenge working
- Grade: A- (production-ready)

### Documentation Created Previously
1. NETWORK_CONSOLIDATION_ANALYSIS.md
2. CLOUDFLARE_TUNNELS_FOUND.md
3. NETWORK_CLEANUP_2025-11-16.md
4. CLOUDFLARE_TUNNEL_AUDIT.md
5. TRAEFIK_VALIDATION.md

---

## Phase 1 Progress - IN PROGRESS

### Completed Steps:

**✅ Step 1: NPM LXC Container Created**
- Container ID: CT 200
- IP Address: 10.16.1.50
- Hostname: nginx-proxy-manager
- Storage: scratch-pve (8GB)
- Specs: 2 cores, 1024MB RAM
- Type: Privileged container (needed for Docker)
- Status: Running

**✅ Step 2: NPM Deployed**
- Method: Docker with host networking (to avoid port binding issues)
- Admin Interface: http://10.16.1.50:81
- Status: Running and accessible
- Default Credentials: admin@example.com / changeme

### Next Steps:

**Step 3: Initial NPM Configuration**
- [ ] Log into NPM admin interface
- [ ] Change admin email to: dp@getmassive.com.au
- [ ] Change admin password
- [ ] Add Cloudflare API token for SSL

**Step 4: Configure SSL Certificate**
- [ ] Request wildcard cert: `*.gmdojo.tech`
- [ ] Use Cloudflare DNS challenge
- [ ] API token: `aGSMUr8pQcAH4vuueTVCfyENElLKRUGVwMmNDIPn`

**Step 5: Add Pi-hole DNS Record**
- [ ] Add wildcard: `*.gmdojo.tech → 10.16.1.50`
- Pi-hole location: 10.16.1.4:82/admin

**Step 6: Add Proxy Hosts**
- [ ] Proxmox: `pve.gmdojo.tech` → 10.16.1.22:8006
- [ ] Uptime Kuma: `uptime.gmdojo.tech` → 10.16.1.4:3001
- [ ] Grafana: `grafana.gmdojo.tech` → 10.16.1.4:3002
- [ ] TrueNAS: `nas.gmdojo.tech` → 10.16.1.6
- [ ] Pi-hole: `pihole.gmdojo.tech` → 10.16.1.4:82

**Step 7: Update Cloudflare Tunnel**
- [ ] Change hostname: `uptime.getmassive.au` → `status.gmdojo.tech`
- [ ] Point to: `https://10.16.1.50` (NPM, not Uptime Kuma directly)

---

## Key Architecture Changes

### Old Architecture (Current)
```
Clients → Traefik (10.16.1.4:443) → Docker Containers
Domain: *.local.getmassive.com.au (40+ chars)
```

### New Architecture (Target)
```
Clients → NPM (10.16.1.50:443) → LXC Containers
Domain: *.gmdojo.tech (20-25 chars)
Public: status.gmdojo.tech → Cloudflare Tunnel → NPM → Uptime Kuma
```

### Parallel Operation During Migration
- Traefik continues serving old domain
- NPM serves new domain
- Both work simultaneously
- No downtime during migration
- Old domain deprecated after 30 days

---

## Important Notes

### Security
- Only `status.gmdojo.tech` exposed publicly
- All other services internal only (Tailscale/LAN)
- No wildcard DNS in Cloudflare (security risk)
- Wildcard DNS only in Pi-hole (internal)

### SSL Certificates
- Traefik: `*.local.getmassive.com.au` (expires Feb 13, 2026)
- NPM: `*.gmdojo.tech` (will be requested in Phase 1)
- Both use Cloudflare DNS challenge (no inbound port 80)

### Rollback Strategy
- Keep Traefik running throughout Phase 1
- Old URLs continue working
- Easy to rollback if issues
- Stop NPM container: `pct stop 200`

---

## Background Tasks Status

Several background tasks were running when session ended:
- VM 112 migration (pve-itchy → pve-scratchy)
- CT 129 backup test
- TrueNAS rsync (temp-dr-mount → Tank/proxmox-backup-server)
- Docker container updates on VM 100

May need to check status when resuming.

---

## Questions to Ask When Resuming

1. **Pi-hole API Key:** User was about to provide this for automated DNS updates
2. **Proceed with Phase 1?** Ready to create NPM LXC and begin setup
3. **Timing:** When to execute (evening/weekend for safety?)

---

## Useful Commands Reference

### Check Proxmox Containers
```bash
ssh root@10.16.1.22 "pct list"
```

### Check Docker Containers
```bash
ssh dp@10.16.1.4 "docker ps"
```

### Check Cloudflare Tunnel
```bash
ssh root@10.16.1.22 "pct exec 106 -- ps aux | grep cloudflared"
```

### Access NPM Admin (after setup)
```
http://10.16.1.50:81
```

### Check DNS Resolution
```bash
dig pve.gmdojo.tech @10.16.1.4
```

---

## Timeline Estimate

**Phase 1 (NPM Setup):** 2-4 hours
- DNS configuration: 15 min
- LXC creation: 10 min
- NPM installation: 30 min
- SSL setup: 30 min
- Proxy hosts: 1-2 hours
- Testing: 30 min

**Total Migration (All Phases):** 4-6 weeks
- Phase 1: Foundation (Week 1)
- Phase 2: Core services (Week 2)
- Phase 3: Media services (Week 3)
- Phase 4: Cleanup (Week 4-6)

---

## Risk Assessment

**Phase 1 Risk:** Low
- Traefik stays running (backup)
- No changes to existing services
- Easy rollback
- No downtime expected

**Overall Migration Risk:** Medium
- Gradual approach mitigates risk
- One service at a time
- Full rollback capability
- 2-4 weeks validation per phase

---

## Success Criteria for Phase 1

- [ ] NPM LXC created and running
- [ ] NPM admin accessible (port 81)
- [ ] Wildcard SSL certificate issued
- [ ] DNS resolution working (*.gmdojo.tech → 10.16.1.50)
- [ ] At least 3 services accessible via new domain
- [ ] Public status page working (status.gmdojo.tech)
- [ ] Old domain still working (Traefik)
- [ ] No errors in NPM logs

---

**Status:** Phase 1 - DNS and NPM infrastructure complete, ready for proxy host creation
**Next Action:** Run `./scripts/configure-npm-proxies.sh` to create all proxy hosts automatically
**Documentation:** Complete with both manual and automated approaches

---

## Phase 1 Automation Scripts Created

### DNS Configuration
- **File:** `scripts/add-pihole-dns.sh`
- **Purpose:** Add DNS records to Pi-hole programmatically
- **Method:** SSH to Docker host, modify custom.list file

### NPM Proxy Host Configuration
- **File:** `scripts/configure-npm-proxies.sh`
- **Purpose:** Create all proxy hosts via NPM API
- **Method:** JWT authentication + REST API calls
- **Usage:** `export NPM_PASSWORD='your_password' && ./scripts/configure-npm-proxies.sh`

### Manual Configuration Guide
- **File:** `NPM_PROXY_HOSTS_CONFIG.md`
- **Purpose:** Step-by-step manual configuration if automation fails

---

**Resume Command:** "Run the NPM automation script to create proxy hosts"
