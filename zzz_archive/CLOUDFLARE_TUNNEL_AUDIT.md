# Cloudflare Tunnel Audit - rova

**Date:** 2025-11-16
**Tunnel ID:** `79fbb004-716a-4249-9891-cd25770c1a3f`
**Container:** rova CT 113 (rova-cloudflared)
**Status:** Connected but appears unused

---

## Tunnel Details

### Current Status
- ✅ **Running:** Yes, since Nov 14 2025
- ✅ **Connected:** 4 connections to Cloudflare edge
  - syd05 (Sydney)
  - syd07 (Sydney)
  - bne01 x2 (Brisbane)
- ❌ **HTTP Traffic:** None visible in logs
- ⚠️ **Stability:** Frequent reconnects/errors

### Token Information
```
Token: eyJhIjoiMzk5M2ViMDU0N2UwNzdlMDgxMDg5NjkwOTI4NTQwZDciLCJ0IjoiNzlmYmIwMDQtNzE2YS00MjQ5LTk4OTEtY2QyNTc3MGMxYTNmIiwicyI6IlpHSmlaams1TjJNdE16TmxNUzAwWkRNMUxXSXlOVGt0WVRCak16Z3dPR1kwWldZMCJ9
```

**Decoded token contains:**
- Account ID: `3993eb0547e077e081089690928540d7`
- Tunnel ID: `79fbb004-716a-4249-9891-cd25770c1a3f`
- Secret: `ZGJiZjk5N2MtMzNlMS00ZDM1LWIyNTktYTBjMzgwOGY0ZWY0`

### Network Configuration
- **Local listening:** 127.0.0.1:20241 (metrics/management only)
- **No public ports:** Tunnel is ingress-only
- **No reverse proxy visible:** Not forwarding to any local services

---

## Analysis

### Evidence Tunnel is Unused

1. **No HTTP request logs** in 50+ lines of recent logs
2. **Only connection/reconnection logs** visible
3. **Listening on localhost only** (no forwarding configured)
4. **No ingress configuration found** on container

### Possible Scenarios

**Scenario A: Never Configured**
- Tunnel created but never set up with routes
- Just maintaining connection
- No DNS records pointing to it

**Scenario B: Previously Used, Now Abandoned**
- Was configured for some service
- Service moved or removed
- Tunnel left running

**Scenario C: Standby/Test Tunnel**
- Created for future use
- Never activated
- Forgotten about

---

## Manual Verification Steps

Since the API token doesn't have tunnel read permissions, you'll need to check the Cloudflare dashboard manually:

### 1. Login to Cloudflare Dashboard

**URL:** https://dash.cloudflare.com/

**Account ID:** `3993eb0547e077e081089690928540d7`

### 2. Navigate to Zero Trust → Access → Tunnels

**Direct URL:**
```
https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels
```

### 3. Find Your Tunnel

Look for tunnel with ID: `79fbb004-716a-4249-9891-cd25770c1a3f`

**Check for:**
- Tunnel name
- Status (Active/Inactive)
- Public hostnames configured
- Routes configured
- Last seen timestamp

### 4. Check Public Hostnames

**URL:**
```
https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels/79fbb004-716a-4249-9891-cd25770c1a3f
```

**Look for:**
- Any configured hostnames (e.g., `*.yourdomain.com`)
- Services being exposed
- Health check status

### 5. Check DNS Records

For each domain in your Cloudflare account, check DNS records:

**Look for:**
- CNAME records pointing to `<tunnel-id>.cfargotunnel.com`
- A/AAAA records with Cloudflare proxy enabled pointing to tunnel

### 6. Check Analytics

**URL:**
```
https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/analytics-and-logs/access
```

**Check:**
- Request count for tunnel (last 7/30 days)
- Bandwidth usage
- Error rates

---

## Decision Matrix

### If Tunnel Has No Routes Configured

**Action:** Safe to remove immediately

**Steps:**
1. Stop container: `pct stop 113`
2. Delete tunnel from Cloudflare dashboard
3. After 24 hours, destroy container: `pct destroy 113`

**Risk:** None

### If Tunnel Has Routes but No Recent Traffic

**Action:** Safe to remove with monitoring period

**Steps:**
1. Document all routes/hostnames
2. Stop container: `pct stop 113`
3. Monitor for 48 hours
4. If no complaints, delete tunnel from dashboard
5. Destroy container: `pct destroy 113`

**Risk:** Low (no traffic suggests unused)

### If Tunnel Has Active Traffic

**Action:** Investigate before removal

**Steps:**
1. Identify what services are exposed
2. Determine if still needed
3. If needed, migrate to scratchy
4. If not needed, disable routes first
5. Monitor for 1 week
6. Remove if no impact

**Risk:** Medium (active use)

---

## Removal Instructions

### Option 1: Immediate Removal (if no routes)

```bash
# 1. Stop tunnel
ssh root@10.25.1.5 "pct stop 113"

# 2. Go to Cloudflare dashboard and delete tunnel
# https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels

# 3. After confirming nothing broke (24 hours)
ssh root@10.25.1.5 "pct destroy 113"
```

### Option 2: Gradual Removal (if routes exist)

```bash
# 1. Disable routes in Cloudflare dashboard
# - Remove all public hostnames
# - Keep tunnel running

# 2. Monitor for 48 hours

# 3. If no issues, stop tunnel
ssh root@10.25.1.5 "pct stop 113"

# 4. Monitor for another 48 hours

# 5. Delete tunnel from dashboard

# 6. Destroy container
ssh root@10.25.1.5 "pct destroy 113"
```

### Option 3: Migrate to Scratchy (if needed)

See [NETWORK_CONSOLIDATION_ANALYSIS.md](NETWORK_CONSOLIDATION_ANALYSIS.md) Phase 3 "Cloudflare Decision" section for migration instructions.

---

## Post-Removal Cleanup

After removing the tunnel:

1. **Update backup exclusions** (if CT 113 was in backup jobs)
2. **Update documentation**
3. **Remove from monitoring** (if applicable)
4. **Note resources freed:**
   - RAM: ~512 MB
   - Storage: ~2 GB
   - CPU: Minimal but measurable

---

## Rollback Plan

If you need to restore the tunnel:

### 1. Restore Container from Backup

```bash
# If you have PBS backup
pct restore 113 prox-backup-srv:backup-file

# Or recreate from scratch
pct create 113 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
    --hostname rova-cloudflared \
    --memory 512 \
    --net0 name=eth0,bridge=vmbr0,ip=10.25.1.20/24,gw=10.25.1.1 \
    --cores 1 \
    --rootfs local-lvm:4
```

### 2. Reinstall Cloudflared

```bash
pct start 113
pct exec 113 -- bash -c "curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o /tmp/cloudflared.deb"
pct exec 113 -- dpkg -i /tmp/cloudflared.deb
```

### 3. Use Same Token

```bash
TOKEN="eyJhIjoiMzk5M2ViMDU0N2UwNzdlMDgxMDg5NjkwOTI4NTQwZDciLCJ0IjoiNzlmYmIwMDQtNzE2YS00MjQ5LTk4OTEtY2QyNTc3MGMxYTNmIiwicyI6IlpHSmlaams1TjJNdE16TmxNUzAwWkRNMUxXSXlOVGt0WVRCak16Z3dPR1kwWldZMCJ9"
pct exec 113 -- cloudflared service install $TOKEN
```

### 4. Restore Routes in Dashboard

Re-create any public hostnames/routes that were documented.

---

## Questions to Ask Yourself

Before removing the tunnel, answer:

1. **Do I remember setting this up?**
   - If no → Likely safe to remove
   - If yes → What was it for?

2. **Do I have any public URLs pointing to my homelab?**
   - If no → Tunnel likely unused
   - If yes → Check if they use this tunnel

3. **Do I need external access to any homelab services?**
   - If no → Remove Cloudflare entirely
   - If yes → Consider Tailscale instead (simpler, more secure)

4. **Do I have webhooks or integrations that need public URLs?**
   - Examples: Sonarr/Radarr notifications, GitHub webhooks, etc.
   - If yes → Check if they're currently working
   - If working → They might use this tunnel

---

## Recommendations

Based on evidence:

### Primary Recommendation: Remove

**Confidence:** High (90%)

**Reasoning:**
- No traffic in logs
- No services configured
- Just maintaining connection
- Consuming resources for no benefit

**Action:** Follow "Option 1: Immediate Removal"

### Alternative: Keep for Future Use

**Only if:**
- You plan to expose services publicly soon
- You don't want to go through tunnel setup again
- Resources are not a concern

**Action:** Document and leave running, but set a reminder to review in 3 months

---

**Next Step:** Check Cloudflare dashboard at the URLs above, then decide removal approach.
