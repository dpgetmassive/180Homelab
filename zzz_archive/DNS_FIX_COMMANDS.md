# DNS Fix for Containers

**Problem:** Multiple containers are configured to use 10.16.1.50 (NPM) as DNS, but NPM doesn't run a DNS server. This causes 5+ second timeouts for external DNS lookups.

**Correct DNS:** 10.16.1.1 (your router)

---

## Quick Fix via Proxmox Shell

**Run these commands in pve-scratchy Shell (System → Shell):**

```bash
# Fix CT 108 (plexpunnisher) - PRIORITY
pct set 108 --nameserver 10.16.1.1,1.1.1.1
pct set 108 --searchdomain gm.local

# Fix CT 101 (watchyourlani)
pct set 101 --nameserver 10.16.1.1,1.1.1.1
pct set 101 --searchdomain gm.local

# Fix CT 129 (crafty-s)
pct set 129 --nameserver 10.16.1.1,1.1.1.1
pct set 129 --searchdomain gm.local

# Fix CT 901 (tailscale)
pct set 901 --nameserver 10.16.1.1,1.1.1.1
pct set 901 --searchdomain gm.local

# Restart containers for changes to take effect
pct restart 108
pct restart 101
pct restart 129
pct restart 901
```

---

## Verify DNS is Working

After restarting, check if DNS works:

```bash
# Test from CT 108
pct exec 108 -- nslookup plex.tv

# Should return IP addresses, not "connection refused"
```

---

## What This Fixes

**Before:**
- Containers try to query 10.16.1.50:53 (NPM) for DNS
- NPM doesn't have DNS service running
- Connection refused after 5+ second timeout
- Plex UI sluggish due to constant DNS failures

**After:**
- Containers query 10.16.1.1 (router) for DNS
- DNS lookups succeed immediately
- Plex UI responsive
- External services (plex.tv, updates, etc.) work properly

---

## Affected Containers

| VMID | Name | Old DNS | New DNS | Status |
|------|------|---------|---------|--------|
| 108 | plexpunnisher | 10.16.1.50 | 10.16.1.1 | ⚠️ NEEDS FIX |
| 101 | watchyourlani | 10.16.1.50 | 10.16.1.1 | ⚠️ NEEDS FIX |
| 129 | crafty-s | 10.16.1.50 | 10.16.1.1 | ⚠️ NEEDS FIX |
| 901 | tailscale | 10.16.1.50 | 10.16.1.1 | ⚠️ NEEDS FIX |

**Already correct:**
- CT 104: Uses 10.16.1.1 ✅
- CT 113: Uses 10.16.1.1 ✅
- CT 200 (NPM): Uses 1.1.1.1 ✅
- CT 900: Uses 10.16.1.1 ✅
