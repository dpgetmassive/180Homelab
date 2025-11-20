# Network Infrastructure Consolidation Analysis

**Date:** 2025-11-16
**Objective:** Simplify Tailscale and Cloudflare tunnel infrastructure across two Proxmox hosts

---

## Current Infrastructure

### Tailscale Deployments

#### pve-scratchy (10.16.1.22) - HomeLab Primary
- **CT 901:** tailscaler
  - **Local IP:** 10.16.1.31
  - **Tailscale IP:** 100.83.115.87
  - **Status:** ✅ Running and active
  - **Role:** Exit node provider
  - **Hostname:** tailscaler.kooka-universe.ts.net
  - **Connected devices:** 16 total (1 active - your MacBook Pro)

#### rova (10.25.1.5) - Remote Site
- **CT 111:** rova-tailscale
  - **Local IP:** 10.25.1.18
  - **Tailscale IP:** 100.94.136.14
  - **Status:** ❌ Logged out / Not authenticated
  - **Role:** Unknown (appears inactive)
  - **Shown in scratchy's Tailscale:** Offline, tagged-devices

### Cloudflare Tunnel Deployments

#### rova (10.25.1.5) - Remote Site
- **CT 113:** rova-cloudflared
  - **Status:** ✅ Running since Nov 14
  - **Token-based tunnel** (running with auth token)
  - **Configuration:** Unknown services/routes
  - **Uptime:** ~2 days

#### pve-scratchy (10.16.1.22) - HomeLab Primary
- **Status:** ❌ No Cloudflare tunnel found
  - No cloudflared containers
  - No cloudflared processes

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                       Tailscale Network                         │
│                   kooka-universe.ts.net                         │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                           │
        ▼                                           ▼
┌───────────────────────┐                 ┌───────────────────────┐
│   pve-scratchy        │                 │      rova             │
│   10.16.1.22          │                 │   10.25.1.5           │
│                       │                 │                       │
│  CT 901: tailscaler   │                 │  CT 111: rova-ts      │
│  ✅ ACTIVE            │                 │  ❌ LOGGED OUT        │
│  100.83.115.87        │                 │  100.94.136.14        │
│  Exit node enabled    │                 │                       │
│                       │                 │  CT 113: cloudflared  │
│  ❌ No Cloudflare     │                 │  ✅ RUNNING           │
│                       │                 │  Token-based          │
└───────────────────────┘                 └───────────────────────┘
         │                                          │
         │                                          │
    ┌────┴────┐                              ┌──────┴──────┐
    │ 10.16.1 │                              │  10.25.1    │
    │ Network │                              │  Network    │
    │ (Main)  │                              │  (Remote)   │
    └─────────┘                              └─────────────┘
```

---

## Issues & Redundancy

### Tailscale Issues

1. **Dual Tailscale instances** - Two separate containers across sites
   - **scratchy CT 901:** Working, exit node configured
   - **rova CT 111:** Not authenticated, appears abandoned

2. **Exit node location:** Currently on scratchy (Sydney homelab)
   - Your monitoring script uses this for perrett.tech access
   - MacBook Pro currently using this exit node

3. **Authentication state:** rova-tailscale is logged out
   - Not providing any functionality
   - Consuming resources (minimal)
   - Listed in network but offline

### Cloudflare Issues

1. **Single tunnel at remote site** only
   - Rova has cloudflared running
   - Main homelab (scratchy) has none
   - **No visible HTTP traffic in logs** - tunnel appears unused

2. **Token-based authentication** (can't list/manage without cert)
   - Running but can't audit configuration without Cloudflare dashboard
   - Token: `eyJhIjoi...` (obscured for security)
   - Tunnel ID embedded in token: `79fbb004-716a-4249-9891-cd25770c1a3f`
   - Only listening on localhost:20241 (management/metrics port)

3. **Tunnel Status:**
   - ✅ Connected to Cloudflare edge (4 connections: syd05, syd07, bne01 x2)
   - ⚠️ Frequent reconnects/errors (network stability issues?)
   - ❌ No HTTP request logs visible (no actual traffic flowing)
   - **Likely unused/abandoned** - just maintaining connection

4. **No centralized management**
   - Each site configured independently
   - No unified access strategy
   - Configuration stored in Cloudflare cloud (token-based setup)

---

## Recommendations

### Option 1: Single Tailscale (Recommended)

**Keep:** scratchy CT 901 (tailscaler)
**Remove:** rova CT 111 (rova-tailscale)

**Rationale:**
- Scratchy is primary 24/7 homelab
- Exit node already configured and working
- Used by monitoring (heartbeat to perrett.tech)
- Active connection to your devices
- Rova Tailscale is offline anyway

**Benefits:**
- Single point of authentication
- Simplified management
- One less container at remote site
- Exit node centrally located
- Consistent network access

**Implementation:**
```bash
# 1. Verify nothing depends on rova-tailscale
# 2. Stop and remove CT 111 on rova
pct stop 111
pct destroy 111

# 3. Access rova services via:
#    - Direct LAN (10.25.1.x) when on-site
#    - Through scratchy Tailscale exit node when remote
```

### Option 2: Dual Tailscale with Subnet Routing

**Keep both but configure properly:**
- scratchy: Primary exit node + subnet router for 10.16.1.0/24
- rova: Re-authenticate + subnet router for 10.25.1.0/24

**Rationale:**
- Each site advertises its local network
- Access any device through Tailscale without individual clients
- Geographic redundancy

**Benefits:**
- Full network access via Tailscale
- No need to Tailscale-enable every device
- Failover if one site offline

**Downsides:**
- More complex
- Two containers to maintain
- Higher overhead
- Requires both sites online for full access

**Implementation:**
```bash
# 1. Re-authenticate rova-tailscale
pct exec 111 -- tailscale login

# 2. Enable subnet routing on scratchy
pct exec 901 -- tailscale up --advertise-routes=10.16.1.0/24 --accept-routes

# 3. Enable subnet routing on rova
pct exec 111 -- tailscale up --advertise-routes=10.25.1.0/24 --accept-routes

# 4. Approve subnet routes in Tailscale admin console
```

### Cloudflare Tunnel Consolidation

#### Option A: Single Tunnel on Scratchy (Recommended)

**Move tunnel from rova → scratchy**

**Rationale:**
- Scratchy is primary 24/7 host
- Better uptime guarantee
- Centralized management
- Main services are on scratchy anyway

**Services to expose:**
- Sonarr (10.16.1.4:8989)
- SABnzbd (10.16.1.4:8080)
- Proxmox web UI (10.16.1.22:8006)
- Nginx Proxy Manager (10.16.1.4:81)
- WikiJS, Grafana, or other web services

**Benefits:**
- Single tunnel to manage
- Better performance (primary host)
- All main services accessible
- One less container at rova

**Implementation:**
```bash
# 1. Create new tunnel on scratchy (via Cloudflare dashboard)
# 2. Create new LXC container on scratchy for cloudflared
# 3. Configure ingress rules for desired services
# 4. Test access
# 5. Stop rova cloudflared tunnel
# 6. Remove CT 113 from rova
```

#### Option B: Dual Tunnels with Clear Purpose

**Keep both but define roles:**
- **scratchy tunnel:** HomeLab services (Sonarr, Proxmox, etc.)
- **rova tunnel:** Rova-specific services (Pi-hole, local services)

**Only if you need:**
- Geographic redundancy
- Site-specific service isolation
- Different access control per site

#### Option C: No Cloudflare Tunnels (Tailscale Only)

**Remove all Cloudflare tunnels, use Tailscale exclusively**

**Rationale:**
- Tailscale provides encrypted access
- No need for public domain exposure
- Simpler architecture
- One less authentication system

**Benefits:**
- Maximum simplicity
- Better security (no public exposure)
- Zero-trust by default
- Single VPN solution

**Downsides:**
- Requires Tailscale client on all devices
- Can't share access without Tailscale account
- No public URLs for webhooks/integrations

---

## Recommended Consolidated Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tailscale Network (Primary)                  │
│                   kooka-universe.ts.net                         │
│                                                                 │
│   ┌──────────────────────────────────────────────────────┐    │
│   │  scratchy CT 901: tailscaler                         │    │
│   │  - Exit node for internet access                     │    │
│   │  - Subnet routing for 10.16.1.0/24 (optional)        │    │
│   │  - All devices connect here                          │    │
│   └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                    │
                    ▼                    ▼
         ┌──────────────────┐   ┌──────────────────┐
         │  pve-scratchy    │   │      rova        │
         │  10.16.1.22      │   │   10.25.1.5      │
         │                  │   │                  │
         │  CT 901: ts      │   │  ❌ Remove CT111 │
         │  (Tailscale)     │   │  ❌ Remove CT113 │
         │                  │   │  (or migrate to  │
         │  CT 902: cf      │   │   scratchy)      │
         │  (Cloudflare)    │   │                  │
         │  - Sonarr        │   │  Access via:     │
         │  - SABnzbd       │   │  - Tailscale     │
         │  - Proxmox UI    │   │  - Direct LAN    │
         │  - NPM           │   │                  │
         └──────────────────┘   └──────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│              Cloudflare Tunnel (Optional)                       │
│              app.perrett.tech / *.getmassive.au                 │
│                                                                 │
│   Only for services requiring:                                  │
│   - Public access without VPN                                   │
│   - Webhook integrations                                        │
│   - External API access                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Audit Current Usage

**Before making changes, determine:**

1. **What is rova-tailscale used for?**
   ```bash
   # Check what might be using it
   ssh root@10.25.1.5 "pct exec 111 -- netstat -tulpn"
   ssh root@10.25.1.5 "pct exec 111 -- systemctl status tailscaled"
   ```

2. **What services are exposed via rova cloudflared?**
   ```bash
   # Check tunnel configuration
   ssh root@10.25.1.5 "pct exec 113 -- cat /etc/cloudflared/config.yml"
   ssh root@10.25.1.5 "pct exec 113 -- systemctl status cloudflared"
   ```

3. **Who/what is accessing these services?**
   - Check Cloudflare dashboard for tunnel traffic
   - Check Tailscale admin for rova-tailscale usage history

### Phase 2: Remove rova-tailscale (if unused)

```bash
# 1. Verify it's logged out (already confirmed)
ssh root@10.25.1.5 "pct exec 111 -- tailscale status"

# 2. Stop container
ssh root@10.25.1.5 "pct stop 111"

# 3. Wait 24-48 hours to ensure nothing breaks

# 4. Remove from Tailscale admin console
# - Go to Tailscale admin
# - Find "rova-tailscale" device
# - Remove from network

# 5. Destroy container
ssh root@10.25.1.5 "pct destroy 111"
```

### Phase 3: Cloudflare Decision

**Option A: Migrate to scratchy**

```bash
# 1. Get tunnel details from Cloudflare dashboard
# 2. Create new tunnel in dashboard
# 3. Create LXC container on scratchy
pct create 902 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
    --hostname cloudflared \
    --memory 512 \
    --net0 name=eth0,bridge=vmbr0,ip=10.16.1.32/24,gw=10.16.1.1 \
    --cores 1 \
    --rootfs local-lvm:8

# 4. Install cloudflared
pct start 902
pct exec 902 -- bash -c "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb"
pct exec 902 -- dpkg -i /tmp/cloudflared.deb

# 5. Configure with new tunnel token
pct exec 902 -- cloudflared service install <TOKEN>

# 6. Test access to services
# 7. Update DNS records if needed
# 8. Decommission rova tunnel
```

**Option B: Remove Cloudflare entirely**

```bash
# 1. Document all services currently exposed
# 2. Ensure Tailscale access works for all users
# 3. Stop cloudflared on rova
ssh root@10.25.1.5 "pct stop 113"

# 4. Wait 24-48 hours
# 5. Delete tunnel from Cloudflare dashboard
# 6. Remove DNS records
# 7. Destroy container
ssh root@10.25.1.5 "pct destroy 113"
```

### Phase 4: Document New Architecture

1. Update network documentation
2. Update access procedures
3. Update monitoring (if needed)
4. Update backup scripts (remove destroyed CTs)

---

## Cost-Benefit Analysis

### Current State (Redundant)
- **Resources:** 3 containers (2x Tailscale, 1x Cloudflare)
- **Memory:** ~1.5 GB total
- **Management:** Multiple authentication points
- **Complexity:** High (duplicate services)
- **Single points of failure:** Both Tailscale and Cloudflare

### Recommended State (Consolidated)
- **Resources:** 1-2 containers (1x Tailscale, 0-1x Cloudflare)
- **Memory:** ~512 MB - 1 GB
- **Management:** Single Tailscale, optional single Cloudflare
- **Complexity:** Low (clear purpose for each)
- **Reliability:** Higher (fewer moving parts)

### Resource Savings
- **Memory:** 512 MB - 1 GB saved
- **Storage:** ~2-4 GB saved (container templates)
- **CPU:** Minimal but measurable
- **Management time:** 50% reduction

---

## Risk Assessment

### Low Risk
- ✅ Removing rova-tailscale (already offline)
- ✅ Stopping cloudflared temporarily (can restart)

### Medium Risk
- ⚠️ Migrating Cloudflare tunnel (downtime during migration)
- ⚠️ Removing Cloudflare tunnel (if anyone uses public URLs)

### High Risk
- ❌ None identified (all changes are reversible)

### Rollback Plan

**If something breaks:**

1. **Tailscale:**
   ```bash
   # Re-authenticate rova-tailscale
   pct start 111
   pct exec 111 -- tailscale login
   # Follow auth link in output
   ```

2. **Cloudflare:**
   ```bash
   # Restart tunnel on rova
   pct start 113
   pct exec 113 -- systemctl restart cloudflared
   ```

3. **Complete rollback:**
   - All containers can be restored from PBS backups
   - Tailscale devices can be re-added to network
   - Cloudflare tunnels can be recreated

---

## Questions to Answer Before Proceeding

1. **What services need external (non-VPN) access?**
   - Webhooks (Sonarr, Radarr, etc.)?
   - Public sharing?
   - Mobile apps without Tailscale?

2. **Who accesses your homelab?**
   - Just you via Tailscale?
   - Family members without Tailscale?
   - External services/integrations?

3. **What is rova's role?**
   - Permanent remote site?
   - Temporary deployment?
   - What services run there that need remote access?

4. **Current Cloudflare tunnel usage?**
   - What domains point to it?
   - What services are exposed?
   - Who/what accesses them?

---

## Next Steps

1. **Answer questions above** to determine best path
2. **Audit current Cloudflare tunnel** configuration
3. **Choose consolidation option** based on needs
4. **Execute Phase 1** (audit) to gather data
5. **Proceed with removal** if safe

---

**Status:** Analysis complete, awaiting decision
**Recommended:** Option 1 (Single Tailscale) + Option C (Remove Cloudflare - appears unused)
**Risk Level:** Low
**Estimated Time:** 30 minutes for complete consolidation

---

## Audit Findings Summary

### rova-tailscale (CT 111)
- ❌ **Status:** Logged out and offline
- ❌ **Autostart:** Was enabled (now disabled)
- ❌ **Function:** None (not authenticated)
- ✅ **Safe to remove:** Yes

### rova-cloudflared (CT 113)
- ✅ **Status:** Running and connected to Cloudflare edge
- ⚠️ **Traffic:** None visible in logs (no HTTP requests)
- 🔍 **Purpose:** Unknown - **need to check Cloudflare dashboard**
- ❓ **Safe to remove:** Likely yes, but verify dashboard first

**Tunnel ID:** `79fbb004-716a-4249-9891-cd25770c1a3f`

### scratchy-tailscaler (CT 901)
- ✅ **Status:** Active and functioning
- ✅ **Exit node:** Enabled and in use
- ✅ **Devices:** 16 registered, 1 active (your MacBook)
- ✅ **Keep:** Required for current workflow

---

## Immediate Recommendations

**Quick wins (low risk):**

1. ✅ **DONE:** Disabled autostart on rova-tailscale CT 111
2. **Check Cloudflare dashboard** for tunnel `79fbb004-716a-4249-9891-cd25770c1a3f`:
   - What routes/hostnames are configured?
   - Any DNS records pointing to tunnel?
   - Any recent traffic in Cloudflare Analytics?

3. **If Cloudflare tunnel is unused:**
   ```bash
   # Stop tunnel (can be restarted if needed)
   ssh root@10.25.1.5 "pct stop 113"

   # Monitor for 24-48 hours
   # If nothing breaks:

   # Delete tunnel from Cloudflare dashboard
   # Then destroy container
   ssh root@10.25.1.5 "pct destroy 113"
   ```

4. **After 2 weeks, remove rova-tailscale:**
   ```bash
   # Remove from Tailscale admin console first
   # Then destroy container
   ssh root@10.25.1.5 "pct destroy 111"
   ```

**Result:** 2 fewer containers, ~1 GB RAM saved, simpler network architecture
