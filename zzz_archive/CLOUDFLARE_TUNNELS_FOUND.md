# Cloudflare Tunnels Discovered - November 2025

**Date:** 2025-11-16
**Discovery:** Found 3 separate Cloudflare tunnel instances across infrastructure

---

## Summary

| Location | Container/VM | IP | Tunnel ID | Status | Purpose |
|----------|-------------|-----|-----------|--------|---------|
| **scratchy** | CT 106 (docker00) | 10.16.1.40 | d4b4b44c-97d0-46f3-8890-2f3d6040231b | ✅ Running | **ACTIVE** - Uptime Kuma |
| **scratchy** | VM 100 /dockerland/cloudflared | 10.16.1.4 | Unknown | ❌ Empty dir | Abandoned |
| **rova** | CT 113 (rova-cloudflared) | 10.25.1.19 | 79fbb004-716a-4249-9891-cd25770c1a3f | ✅ Running | ❌ No routes |

---

## Tunnel Details

### Tunnel 1: CT 106 (docker00) - ACTIVE ✅

**Location:** pve-scratchy CT 106
**Container:** docker00 (IoT services)
**IP:** 10.16.1.40
**Tunnel ID:** `d4b4b44c-97d0-46f3-8890-2f3d6040231b`

**Token:**
```
eyJhIjoiMzk5M2ViMDU0N2UwNzdlMDgxMDg5NjkwOTI4NTQwZDciLCJ0IjoiZDRiNGI0NGMtOTdkMC00NmYzLTg4OTAtMmYzZDYwNDAyMzFiIiwicyI6IlpqZzFNamMzWVRZdE56WXdNQzAwTkRVeExUZzNOV0V0TlRKaE9HSTVOamN3WVdKbSJ9
```

**Process:**
```bash
PID 633: cloudflared --no-autoupdate tunnel run
PID 759: cloudflared tunnel --no-autoupdate run --token <TOKEN>
```

**Purpose:** ✅ **Exposing Uptime Kuma**
- Hostname: `uptime.getmassive.au`
- Backend: Uptime Kuma Docker container on VM 100 (10.16.1.4)
- **THIS IS THE ACTIVE TUNNEL** serving your uptime.getmassive.au site

**Status:** ✅ Keep - actively used

---

### Tunnel 2: VM 100 /dockerland/cloudflared - ABANDONED ❌

**Location:** pve-scratchy VM 100 (dockc)
**Path:** `/dockerland/cloudflared/`
**IP:** 10.16.1.4
**Tunnel ID:** Unknown

**Status:** ❌ Empty directory (created Jan 27 2024, no files)
- No docker-compose file
- No configuration
- Never configured or cleaned up after migration

**Action:** Can be safely deleted
```bash
ssh dp@10.16.1.4 "rm -rf /dockerland/cloudflared"
```

---

### Tunnel 3: rova CT 113 - NO ROUTES ⚠️

**Location:** rova CT 113
**Container:** rova-cloudflared
**IP:** 10.25.1.19
**Tunnel ID:** `79fbb004-716a-4249-9891-cd25770c1a3f`

**Token:**
```
eyJhIjoiMzk5M2ViMDU0N2UwNzdlMDgxMDg5NjkwOTI4NTQwZDciLCJ0IjoiNzlmYmIwMDQtNzE2YS00MjQ5LTk4OTEtY2QyNTc3MGMxYTNmIiwicyI6IlpHSmlaams1TjJNdE16TmxNUzAwWkRNMUxXSXlOVGt0WVRCak16Z3dPR1kwWldZMCJ9
```

**Process:** `cloudflared --no-autoupdate tunnel run --token <TOKEN>`

**Status:** ⚠️ Connected to Cloudflare edge but NO ROUTES configured
- Cloudflare dashboard shows: "No public hostnames"
- No HTTP traffic in logs
- Just maintaining tunnel connection
- **Currently RESTARTED** after brief stop

**Confusion:** Screenshot showed "uptime.getmassive.au" but actual tunnel is on CT 106, not here

**Action:** ❓ Determine if needed
- Currently running (was stopped briefly)
- Appears unused
- Could be removed if confirmed unnecessary

---

## Cloudflare Account Details

**Account ID:** `3993eb0547e077e081089690928540d7`

**API Token:** `GWZyipYR-89mJU9BJNODed1EVfs5XoBboMlAKqoM`
- Status: Active
- Permissions: Token verification only (cannot list/manage tunnels)
- Need full API token to manage tunnels programmatically

**Dashboard:** https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels

---

## Services Exposed via Cloudflare

### uptime.getmassive.au

**Backend Service:**
- Uptime Kuma Docker container
- Running on: VM 100 (dockc) at 10.16.1.4
- Container name: `uptime-kuma`

**Tunnel Routing:**
- **Tunnel:** CT 106 (docker00) tunnel `d4b4b44c-97d0-46f3-8890-2f3d6040231b`
- **Path:** `uptime.getmassive.au` → CT 106 (10.16.1.40) → VM 100 (10.16.1.4)

**Why this setup?**
- CT 106 is an LXC container for IoT services
- Has network access to VM 100 where Uptime Kuma runs
- Acts as reverse proxy via Cloudflare tunnel

---

## Architecture Diagram

```
                         Internet
                            │
                            │ HTTPS
                            ▼
                 ┌──────────────────────┐
                 │  Cloudflare Edge     │
                 │  uptime.getmassive.au│
                 └──────────────────────┘
                            │
                            │ Tunnel: d4b4b44c...
                            ▼
┌─────────────────────────────────────────────────────────┐
│               pve-scratchy (10.16.1.22)                 │
│                                                         │
│  ┌────────────────────────────────────────────┐       │
│  │  CT 106: docker00 (10.16.1.40)             │       │
│  │  ✅ Cloudflared tunnel ACTIVE              │       │
│  │  - Receives traffic from Cloudflare        │       │
│  │  - Forwards to Uptime Kuma                 │       │
│  └────────────────────────────────────────────┘       │
│                          │                             │
│                          │ Forward to VM 100           │
│                          ▼                             │
│  ┌────────────────────────────────────────────┐       │
│  │  VM 100: dockc (10.16.1.4)                 │       │
│  │  📊 Uptime Kuma Docker Container           │       │
│  │  - Monitoring dashboard                    │       │
│  │  - Receives forwarded traffic              │       │
│  └────────────────────────────────────────────┘       │
│                                                         │
│  ┌────────────────────────────────────────────┐       │
│  │  VM 100: /dockerland/cloudflared/          │       │
│  │  ❌ Empty directory - UNUSED               │       │
│  └────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                 rova (10.25.1.5)                        │
│                                                         │
│  ┌────────────────────────────────────────────┐       │
│  │  CT 113: rova-cloudflared (10.25.1.19)     │       │
│  │  ⚠️ Tunnel ID: 79fbb004...                 │       │
│  │  - Connected to Cloudflare                 │       │
│  │  - No routes configured                    │       │
│  │  - No traffic                              │       │
│  └────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

---

## Recommendations

### 1. Keep CT 106 Tunnel ✅

**Reason:** Actively serving uptime.getmassive.au

**No changes needed** - this is working correctly

### 2. Remove /dockerland/cloudflared Directory ✅

**Reason:** Empty, abandoned, unused

**Action:**
```bash
ssh dp@10.16.1.4 "rm -rf /dockerland/cloudflared"
```

**Risk:** None

### 3. Remove rova CT 113 Tunnel ⚠️

**Reason:** No routes, no traffic, unused

**Action:**
```bash
# Already stopped (briefly), now running again
# Stop it
ssh root@10.25.1.5 "pct stop 113"

# Monitor for 24-48 hours
# If nothing breaks:

# Delete tunnel from Cloudflare dashboard
# Then destroy container
ssh root@10.25.1.5 "pct destroy 113"
```

**Risk:** Low (no routes configured, no traffic observed)

---

## Simplified Architecture Goal

**Current:** 3 tunnel instances (1 active, 1 empty, 1 unused)
**Goal:** 1 tunnel instance (CT 106 serving Uptime Kuma)

**Benefits:**
- Clearer architecture
- Less confusion
- Easier to manage
- 512 MB RAM freed (rova CT 113)
- Cleaner codebase (empty dir removed)

---

## Other Workloads to Check

**Still need to check:**
- VM 109 (docka) - another Docker host at 10.16.1.4

Wait, that's the same IP as VM 100. Let me verify:
- VM 100 (dockc): 10.16.1.4 - confirmed
- VM 109 (docka): Need to check IP

---

## VM 110 Lock Issue - RESOLVED ✅

**Issue:** VM 110 had a backup lock from old vzdump job
**Lock file:** `/var/lock/qemu-server/lock-110.conf`
**Created:** Nov 15 19:48 (yesterday)

**Resolution:**
- No vzdump process running
- Removed lock file manually
- VM 110 now accessible

**Note:** VM 110 (TrueNAS primary) is correctly excluded from backups

---

## Questions

1. **What is VM 109 (docka) used for?**
   - Need to check if it also has cloudflared

2. **Should we migrate Uptime Kuma exposure to a dedicated tunnel container?**
   - Currently piggybacking on CT 106 (IoT services)
   - Could be cleaner to have dedicated tunnel CT

3. **Do you need the rova tunnel for anything?**
   - Currently no routes
   - Safe to remove?

---

**Status:** Discovery complete, 3 tunnels found, 1 actively used
**Next:** Check VM 109, decide on rova tunnel removal
