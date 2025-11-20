# Network Infrastructure Cleanup - November 2025

**Date:** 2025-11-16
**Objective:** Remove unused Tailscale and Cloudflare tunnel containers from rova
**Status:** In Progress

---

## Containers Being Removed

### CT 111: rova-tailscale
- **Status:** ❌ Logged out/offline
- **Function:** None (not authenticated)
- **Resources:** 512 MB RAM, 2 GB disk, 1 core
- **Risk:** None (already non-functional)
- **Action:** Remove after 2 weeks observation

### CT 113: rova-cloudflared
- **Status:** ✅ Connected but unused
- **Function:** None (no routes configured)
- **Resources:** 512 MB RAM, 2 GB disk, 2 cores
- **IP:** 10.25.1.19
- **Risk:** None (no traffic, no routes)
- **Action:** ✅ STOPPED 2025-11-16, remove after 24-48 hours

**Tunnel ID:** `79fbb004-716a-4249-9891-cd25770c1a3f`
**Cloudflare Dashboard Confirmed:** No public hostnames, no routes

---

## Timeline

### 2025-11-16 (Today)

**Actions Completed:**
1. ✅ Disabled autostart on CT 111 (rova-tailscale)
2. ✅ Audited Cloudflare tunnel CT 113
3. ✅ Confirmed tunnel has no routes (Cloudflare dashboard)
4. ✅ Stopped CT 113 (rova-cloudflared)

**Monitoring Period Begins:**
- Watch for any service disruptions
- Check logs for any errors
- Confirm no external access issues

### 2025-11-17 or 2025-11-18 (24-48 hours later)

**If No Issues Detected:**

1. **Delete Cloudflare tunnel from dashboard:**
   - Go to: https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels
   - Find tunnel: `79fbb004-716a-4249-9891-cd25770c1a3f`
   - Click Delete
   - Confirm deletion

2. **Destroy container CT 113:**
   ```bash
   ssh root@10.25.1.5 "pct destroy 113"
   ```

3. **Document resources freed:**
   - RAM: 512 MB
   - Storage: 2 GB
   - CPU cores: 2

### 2025-11-30 (2 weeks later)

**Remove rova-tailscale CT 111:**

1. **Remove from Tailscale admin console:**
   - Go to: https://login.tailscale.com/admin/machines
   - Find device: "rova-tailscale" (100.94.136.14)
   - Click "..." → "Delete device"
   - Confirm deletion

2. **Destroy container CT 111:**
   ```bash
   ssh root@10.25.1.5 "pct destroy 111"
   ```

3. **Document total resources freed:**
   - RAM: 1 GB total (512 MB + 512 MB)
   - Storage: 4 GB total (2 GB + 2 GB)
   - CPU cores: 3 total (1 + 2)

---

## Verification Commands

### Check Container Status

```bash
# Check if containers are stopped
ssh root@10.25.1.5 "pct list | grep -E '111|113'"

# Check container configs
ssh root@10.25.1.5 "pct config 111"
ssh root@10.25.1.5 "pct config 113"
```

### Monitor for Issues

```bash
# Check rova system logs
ssh root@10.25.1.5 "journalctl -n 100 --no-pager"

# Check running containers
ssh root@10.25.1.5 "pct list | grep running"

# Check for connection errors
ssh root@10.25.1.5 "dmesg | tail -50"
```

### Verify External Access Still Works

```bash
# Check Tailscale on scratchy still working
ssh root@10.16.1.22 "pct exec 901 -- tailscale status | head -5"

# Test external connectivity
ping -c 3 8.8.8.8
curl -I https://www.google.com
```

---

## Rollback Procedures

### If Cloudflare Tunnel Needed

**Restore CT 113:**
```bash
# Start the stopped container
ssh root@10.25.1.5 "pct start 113"

# If destroyed, recreate:
ssh root@10.25.1.5 "pct create 113 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
    --hostname rova-cloudflared \
    --memory 512 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=10.25.1.19/24,gw=10.25.1.1 \
    --rootfs local-lvm:2"

# Reinstall cloudflared
ssh root@10.25.1.5 "pct start 113"
ssh root@10.25.1.5 "pct exec 113 -- bash -c 'curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb && dpkg -i /tmp/cloudflared.deb'"

# Re-authenticate with same token
TOKEN="eyJhIjoiMzk5M2ViMDU0N2UwNzdlMDgxMDg5NjkwOTI4NTQwZDciLCJ0IjoiNzlmYmIwMDQtNzE2YS00MjQ5LTk4OTEtY2QyNTc3MGMxYTNmIiwicyI6IlpHSmlaams1TjJNdE16TmxNUzAwWkRNMUxXSXlOVGt0WVRCak16Z3dPR1kwWldZMCJ9"
ssh root@10.25.1.5 "pct exec 113 -- cloudflared service install $TOKEN"
```

### If Tailscale on Rova Needed

**Re-authenticate CT 111:**
```bash
# Start container
ssh root@10.25.1.5 "pct start 111"

# Re-authenticate
ssh root@10.25.1.5 "pct exec 111 -- tailscale login"
# Follow the authentication URL provided
```

---

## Final Architecture

### After Cleanup

**pve-scratchy (10.16.1.22) - Primary Site:**
- ✅ CT 901: tailscaler (KEEP)
  - Exit node enabled
  - Monitoring uses this
  - All devices connect here

**rova (10.25.1.5) - Remote Site:**
- ❌ CT 111: rova-tailscale (REMOVED)
- ❌ CT 113: rova-cloudflared (REMOVED)

**Access Methods:**
1. **Internal services:** Direct LAN (10.25.1.x) when on-site
2. **Remote access:** Via Tailscale exit node on scratchy
3. **No public exposure:** All services private (more secure)

---

## Benefits Achieved

### Resource Savings
- **Memory:** 1 GB freed on rova
- **Storage:** 4 GB freed on rova
- **CPU:** 3 cores freed on rova
- **Network:** Less network overhead

### Simplified Management
- ✅ Single Tailscale instance (scratchy)
- ✅ No Cloudflare tunnel complexity
- ✅ Fewer containers to maintain
- ✅ Clearer architecture
- ✅ Reduced attack surface

### Improved Security
- ❌ No public tunnel endpoints
- ✅ All access via Tailscale (zero-trust)
- ✅ No publicly exposed services
- ✅ Simplified authentication (single VPN)

---

## Related Documentation

- [NETWORK_CONSOLIDATION_ANALYSIS.md](NETWORK_CONSOLIDATION_ANALYSIS.md) - Full analysis
- [CLOUDFLARE_TUNNEL_AUDIT.md](CLOUDFLARE_TUNNEL_AUDIT.md) - Tunnel investigation
- [README.md](README.md) - HomeLab overview

---

## Notes & Observations

### Why These Were Unused

**rova-tailscale (CT 111):**
- Likely set up during initial rova deployment
- Never properly configured/authenticated
- Forgotten about
- Scratchy Tailscale became primary

**rova-cloudflared (CT 113):**
- Possibly created for testing
- Never configured with actual routes
- Left running "just in case"
- No actual use case materialized

### Lessons Learned

1. **Regular audits are valuable** - Found 1 GB RAM doing nothing
2. **Token-based tunnels are opaque** - Hard to audit without dashboard
3. **Document as you deploy** - Would have caught these sooner
4. **Question redundancy** - Two Tailscale instances made no sense
5. **Remove test infrastructure** - Don't leave experiments running

---

## Checklist

### Immediate (Completed)
- [x] Audit network infrastructure
- [x] Identify unused containers
- [x] Verify Cloudflare tunnel has no routes
- [x] Disable autostart on CT 111
- [x] Stop CT 113
- [x] Document removal plan

### 24-48 Hours (Pending)
- [ ] Verify no service disruptions
- [ ] Check for any unexpected errors
- [ ] Delete Cloudflare tunnel from dashboard
- [ ] Destroy CT 113
- [ ] Update backup exclusions if needed

### 2 Weeks (Pending)
- [ ] Remove rova-tailscale from Tailscale admin
- [ ] Destroy CT 111
- [ ] Update documentation
- [ ] Commit changes to git

### Follow-up
- [ ] Monthly review: Are services still working?
- [ ] Consider: Do we need rova at all long-term?
- [ ] Document: Final resource utilization on rova

---

**Status:** ✅ CT 113 stopped, monitoring period in progress
**Next Action:** Delete tunnel after 24-48 hours of stable operation
**Expected Completion:** 2025-11-30
**Resource Savings:** 1 GB RAM, 4 GB storage, 3 CPU cores
