# Cloudflare Tunnel Status

**Date:** 2025-11-17
**Status:** ✅ Running and Healthy

---

## Current Setup

**Container:** CT 114 (cloudflared) @ 10.16.1.3

**Tunnel Details:**
- **Tunnel Name:** uptime-gm-hq
- **Tunnel ID:** d4b4b44c-97d0-46f3-8890-2f3d6040231b
- **Connector ID:** 05ef98c8-842a-406b-a844-ed1cdc2085ed
- **Status:** HEALTHY ✅
- **Uptime:** 6+ hours
- **Origin IP:** 159.196.170.48 (public IP)
- **Platform:** linux_amd64

---

## How It Works

```
Internet Users
    ↓
https://unifi.gmdojo.tech (Cloudflare SSL)
    ↓
Cloudflare Edge
    ↓
Encrypted Tunnel (no ports open)
    ↓
CT 114 (cloudflared) @ 10.16.1.3
    ↓
http://10.16.1.50 (NPM)
    ↓
http://10.16.1.X (backend services)
```

**Security:**
- ✅ External traffic encrypted with Cloudflare SSL certificates
- ✅ No firewall ports open (80/443)
- ✅ Tunnel encrypted between Cloudflare and your network
- ⚠️ Internal traffic (NPM → services) unencrypted (on trusted LAN)

---

## SSL Certificates

### External Access (Working)

When users access `https://unifi.gmdojo.tech` from the internet:
- ✅ Valid Cloudflare SSL certificate (trusted by all browsers)
- ✅ Fully encrypted connection
- ✅ Green padlock in browser

### Internal Access (Current Behavior)

When accessing `http://unifi.gmdojo.tech` from LAN (10.16.1.x):
- ⚠️ Resolves to NPM @ 10.16.1.50 via Pi-hole local DNS
- ⚠️ No SSL certificate (NPM serves HTTP only)
- ⚠️ Browser shows "Not Secure"

**This is expected** - internal DNS bypasses Cloudflare tunnel entirely.

---

## Optional: End-to-End Encryption

To encrypt the entire path (Cloudflare → NPM → Services):

### Step 1: Create Cloudflare Origin Certificate

1. Go to Cloudflare Dashboard → **SSL/TLS** → **Origin Server**
2. Click **Create Certificate**
3. Leave defaults (15 year validity, RSA 2048)
4. Copy both:
   - Origin Certificate
   - Private Key

### Step 2: Add Certificate to NPM

1. Open NPM: http://10.16.1.50:81
2. Go to **SSL Certificates**
3. Click **Add SSL Certificate** → **Custom**
4. Name: "Cloudflare Origin Certificate"
5. Paste Certificate and Private Key
6. Save

### Step 3: Apply to Proxy Hosts

For each domain (unifi, plex, pihole, etc.):
1. Edit the Proxy Host
2. Click **SSL** tab
3. Select "Cloudflare Origin Certificate"
4. Check:
   - ✅ Force SSL
   - ✅ HTTP/2 Support
   - ✅ HSTS Enabled
5. Save

### Step 4: Update Cloudflare Tunnel Config

In Cloudflare Zero Trust → Networks → Tunnels → uptime-gm-hq → Configure:
- Update ingress rules from `http://10.16.1.50` to `https://10.16.1.50`

**Result:** Full end-to-end encryption from browser to backend services.

---

## Alternative: Self-Signed Certificates for Internal Access

If you want HTTPS for internal access (*.gmdojo.tech on LAN):

### Option 1: NPM Self-Signed Certificates

For each domain in NPM:
1. Edit Proxy Host → **SSL** tab
2. Select "Request a New SSL Certificate"
3. Choose "Generate Self-Signed"
4. Save

**Result:**
- Internal users see HTTPS (with browser warning)
- Must click "Accept Risk" on first visit
- Certificate not trusted, but traffic is encrypted

### Option 2: Internal Certificate Authority

Create a custom CA certificate and install on all devices:
1. Generate root CA certificate
2. Install CA cert on all computers/phones
3. Generate certificates signed by your CA
4. Upload to NPM

**Result:**
- Internal users see HTTPS with no warnings
- Certificates trusted by all your devices
- Best UX for homelab

---

## Current Configuration

### CT 114 Details

```bash
VMID: 114
Name: cloudflared
IP: 10.16.1.3/24
Gateway: 10.16.1.1
DNS: 10.16.1.1 (router)
Status: Running
```

### Services Accessible via Tunnel

Based on your local DNS entries pointing to NPM @ 10.16.1.50:

| Domain | Backend | Status |
|--------|---------|--------|
| firewall-node1.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| grafana.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| home.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| nas.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| npm.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| pihole.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| plex.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| pve.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| status.gmdojo.tech | 10.16.1.50 (NPM) | Configured |
| unifi.gmdojo.tech | 10.16.1.50 (NPM) | ⚠️ Shows "Not Secure" on LAN |

**Note:** All domains work with SSL when accessed externally via Cloudflare tunnel.

---

## VM 100 Docker Cloudflared (Removed)

**Previous Setup:**
- Docker container `cloudflared-tunnel` on VM 100 @ 10.16.1.4
- Was crash-looping due to DNS issues (Docker DNS resolver broken)
- **Status:** Stopped and removed ✅

**Reason for failure:**
- Docker container using internal DNS (127.0.0.11)
- After disabling Pi-hole on VM 100, Docker DNS failed
- Error: "lookup region1.v2.argotunnel.com on 127.0.0.11:53: server misbehaving"

**Resolution:**
- Confirmed CT 114 was already running the tunnel successfully
- Removed Docker container to avoid conflicts

---

## Monitoring

### Check Tunnel Health

**Cloudflare Dashboard:**
- https://one.dash.cloudflare.com
- Navigate to **Networks** → **Tunnels**
- Should show: **HEALTHY** status ✅

**From Proxmox Host:**
```bash
# Check container status
pct status 114

# Check cloudflared process
pct exec 114 -- ps aux | grep cloudflared

# View logs
pct exec 114 -- journalctl -u cloudflared -f
```

### Troubleshooting

If tunnel goes down:

1. **Check container is running:**
```bash
pct status 114
# If stopped: pct start 114
```

2. **Check DNS in container:**
```bash
pct exec 114 -- cat /etc/resolv.conf
# Should show: nameserver 10.16.1.1
```

3. **Restart cloudflared service:**
```bash
pct exec 114 -- systemctl restart cloudflared
```

4. **View logs:**
```bash
pct exec 114 -- journalctl -u cloudflared -n 50
```

---

## Migration from VM 100

**Completed:**
- ✅ Cloudflare Tunnel migrated from Docker (VM 100) to LXC (CT 114)
- ✅ Running for 6+ hours with HEALTHY status
- ✅ Docker container removed from VM 100

**Benefits:**
- Dedicated container for tunnel
- Easier to manage and monitor
- Better resource isolation
- Native LXC integration with Proxmox

---

## Next Steps (Optional)

### For Better Security:
1. **Add Cloudflare Origin Certificates** to NPM
2. **Update tunnel config** to use HTTPS backend
3. **Enable HSTS** on all proxy hosts

### For Better Internal Access:
1. **Create Internal CA** and install on devices
2. **Generate certificates** for *.gmdojo.tech
3. **Upload to NPM** for trusted internal HTTPS

### For VM 100 Cleanup:
1. ✅ Cloudflared Docker removed
2. ⏳ Can stop old Pi-hole Docker (after DHCP updated)
3. ⏳ Continue migrating other services (Homer, Uptime Kuma, etc.)

---

## Summary

Your Cloudflare Tunnel is **working perfectly**:
- ✅ External users get valid HTTPS certificates
- ✅ No firewall ports open (secure)
- ✅ Tunnel running for 6+ hours (stable)
- ✅ Services accessible from internet

The "Not Secure" warning you saw was for **internal LAN access only**, which bypasses the tunnel entirely. External users accessing via the internet see valid SSL certificates.

**Recommendation:** Keep current setup as-is (it's working), or optionally add Cloudflare Origin Certificates for end-to-end encryption.
