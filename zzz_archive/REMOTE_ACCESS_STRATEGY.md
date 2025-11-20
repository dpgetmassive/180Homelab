# Remote Access Strategy - Dynamic IP + No Port Forwarding

**Date:** 2025-11-16
**Challenge:** Dynamic public IP, no port forwarding available
**Solution:** Cloudflare Tunnel + Tailscale hybrid approach

---

## Problem Statement

**Current Situation:**
- ✅ Traefik reverse proxy configured for internal access
- ✅ Cloudflare tunnel running (CT 106) - only serving uptime.getmassive.com.au
- ✅ Tailscale VPN running (CT 901) - working well
- ❌ Dynamic public IP address
- ❌ Cannot port forward (ISP restriction or CGNAT)
- ❓ Need external access to services

---

## Solution Overview

**Hybrid Approach:**

```
┌──────────────────────────────────────────────────────────┐
│                    Internet Access                       │
└──────────────────────────────────────────────────────────┘
                    │                    │
                    │                    │
            ┌───────▼─────────┐  ┌──────▼────────┐
            │  Tailscale VPN  │  │   Cloudflare  │
            │  (Private)      │  │   Tunnel      │
            │                 │  │   (Public)    │
            └───────┬─────────┘  └───────┬───────┘
                    │                    │
                    │                    │
            ┌───────▼────────────────────▼──────┐
            │         Homelab Network           │
            │                                   │
            │  Tailscale CT 901                 │
            │  Cloudflare CT 106                │
            │  Traefik Reverse Proxy            │
            │  All Services                     │
            └───────────────────────────────────┘
```

---

## Access Methods Comparison

| Method | Use Case | Security | Speed | Sharing | Cost |
|--------|----------|----------|-------|---------|------|
| **Tailscale** | Admin tasks, primary access | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | Free |
| **Cloudflare Tunnel** | Public services, webhooks | ⭐⭐⭐⭐ | ⭐⭐⭐ | ✅ | Free |
| **Traefik (Internal)** | LAN access | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | Free |

---

## Recommended Architecture

### Tier 1: Private Admin Access (Tailscale)

**Access Method:** Tailscale VPN only

**Services:**
- ❌ Proxmox (proxmox.local.getmassive.com.au)
- ❌ TrueNAS (truenas.local.getmassive.com.au)
- ❌ Portainer (portainer.local.getmassive.com.au)
- ❌ Grafana admin (grafana.local.getmassive.com.au)
- ❌ OPNsense (opnsense-fw1/2.local.getmassive.com.au)
- ❌ Vaultwarden (vaultwarden.local.getmassive.com.au)
- ❌ Traefik dashboard

**Why Tailscale only:**
- Management interfaces
- Sensitive data
- No public exposure needed
- Zero-trust security

**Access:**
```
Your Device → Tailscale → scratchy (10.16.1.4) → Traefik → Service
```

### Tier 2: Public Services (Cloudflare Tunnel)

**Access Method:** Cloudflare Tunnel → Public URLs

**Services to Expose:**
- ✅ Uptime Kuma (status.getmassive.com.au) - already exposed
- ✅ Homer/Homepage (home.getmassive.com.au) - optional dashboard
- ✅ Plex (plex.getmassive.com.au) - media streaming
- ✅ Grafana public dashboards (grafana.getmassive.com.au) - read-only

**Configuration:**
```
Public URL → Cloudflare Edge → Tunnel (CT 106) → Traefik (10.16.1.4:443) → Service
```

### Tier 3: Webhooks/Integrations (Cloudflare Tunnel)

**Access Method:** Cloudflare Tunnel for callbacks

**Services:**
- ✅ Sonarr/Radarr webhooks
- ✅ Home Assistant webhooks
- ✅ API endpoints for external integrations

**Example:**
```
webhooks.getmassive.com.au → Cloudflare → Traefik → Specific service
```

---

## Implementation Plan

### Phase 1: Expand Cloudflare Tunnel (Immediate)

**Current State:**
- CT 106 tunnel serving `uptime.getmassive.com.au` → 10.16.1.4:3001

**Goal:**
- Route `*.getmassive.com.au` → Traefik → Services

**Steps:**

1. **Add Traefik as backend in Cloudflare dashboard:**
   ```
   Hostname: services.getmassive.com.au
   Service: https://10.16.1.4:443
   ```

2. **Add wildcard route (optional):**
   ```
   Hostname: *.getmassive.com.au
   Service: https://10.16.1.4:443
   ```

3. **Update Traefik config to accept external hostnames:**

   Edit `/dockerland/traefik/config.yml`, add routers for public domains:
   ```yaml
   uptime-public:
     entryPoints:
       - "https"
     rule: "Host(`status.getmassive.com.au`)"
     middlewares:
       - default-headers
     tls: {}
     service: uptime-kuma

   plex-public:
     entryPoints:
       - "https"
     rule: "Host(`plex.getmassive.com.au`)"
     middlewares:
       - default-headers
     tls: {}
     service: plex
   ```

4. **Test access:**
   ```bash
   curl -I https://status.getmassive.com.au
   ```

### Phase 2: DNS Configuration

**Update Cloudflare DNS:**

1. **Create public DNS records:**
   ```
   status.getmassive.com.au → CNAME → <tunnel-id>.cfargotunnel.com
   plex.getmassive.com.au   → CNAME → <tunnel-id>.cfargotunnel.com
   home.getmassive.com.au   → CNAME → <tunnel-id>.cfargotunnel.com
   ```

2. **Keep internal DNS (Pi-hole) for local access:**
   ```
   *.local.getmassive.com.au → A → 10.16.1.4
   ```

**Result:**
- `status.getmassive.com.au` - accessible from internet
- `status.local.getmassive.com.au` - accessible from LAN (faster)

### Phase 3: Security Hardening

**Add Cloudflare Access (optional, paid feature):**
```
Protect sensitive public services with email authentication
Or use free IP restrictions
```

**Add authentication middleware to public services:**
```yaml
# In Traefik config
middlewares:
  public-auth:
    basicAuth:
      users:
        - "user:hashedpassword"
```

**Apply to routers:**
```yaml
homer-public:
  middlewares:
    - public-auth  # Require login
    - default-headers
```

---

## Detailed Configuration Examples

### Example 1: Expose Homepage Publicly

**1. Cloudflare Dashboard:**
```
Public Hostname: home.getmassive.com.au
Type: HTTPS
URL: https://10.16.1.4:443
```

**2. Traefik config.yml:**
```yaml
http:
  routers:
    homepage-public:
      entryPoints:
        - "https"
      rule: "Host(`home.getmassive.com.au`)"
      middlewares:
        - default-headers
        - https-redirectscheme
      tls: {}
      service: homepage
```

**3. DNS (Cloudflare):**
```
home.getmassive.com.au → CNAME → d4b4b44c-97d0-46f3-8890-2f3d6040231b.cfargotunnel.com
```

**Result:**
- Access from anywhere: `https://home.getmassive.com.au`
- No port forwarding needed
- SSL handled by Cloudflare

### Example 2: Plex via Cloudflare

**1. Cloudflare Dashboard:**
```
Public Hostname: plex.getmassive.com.au
Type: HTTPS
URL: https://10.16.1.4:443
```

**2. Traefik config.yml:**
```yaml
http:
  routers:
    plex-public:
      entryPoints:
        - "https"
      rule: "Host(`plex.getmassive.com.au`)"
      middlewares:
        - default-headers
      tls: {}
      service: plex
```

**3. Plex Settings:**
- Custom server access URLs: `https://plex.getmassive.com.au`

### Example 3: Webhooks for Sonarr/Radarr

**1. Cloudflare Dashboard:**
```
Public Hostname: webhooks.getmassive.com.au
Type: HTTPS
URL: https://10.16.1.4:443
```

**2. Traefik config.yml:**
```yaml
http:
  routers:
    sonarr-webhook:
      entryPoints:
        - "https"
      rule: "Host(`webhooks.getmassive.com.au`) && PathPrefix(`/sonarr`)"
      middlewares:
        - default-headers
      tls: {}
      service: sonarr-backend

  services:
    sonarr-backend:
      loadBalancer:
        servers:
          - url: "http://10.16.1.4:8989"
```

**3. External Service:**
- Webhook URL: `https://webhooks.getmassive.com.au/sonarr/webhook`

---

## Alternative Solutions (Not Recommended)

### Dynamic DNS Services

**Examples:** DuckDNS, No-IP, Dynu

**Pros:**
- Provides static hostname for dynamic IP
- Free options available

**Cons:**
- ❌ Still requires port forwarding
- ❌ You don't have port forwarding access
- ❌ Not needed with Cloudflare/Tailscale

### VPS Reverse Proxy

**Setup:** VPS with WireGuard → Homelab

**Pros:**
- Full control
- Static IP
- Any protocol

**Cons:**
- ❌ Monthly cost ($5-10/month)
- ❌ Maintenance overhead
- ❌ Cloudflare Tunnel is free and easier

### Ngrok / Localtunnel

**Pros:**
- Quick setup
- Good for testing

**Cons:**
- ❌ Random URLs (free tier)
- ❌ Not suitable for production
- ❌ Limited bandwidth
- ❌ Cloudflare Tunnel is better

---

## Cost Analysis

| Solution | Setup Cost | Monthly Cost | Total Year 1 |
|----------|------------|--------------|--------------|
| **Cloudflare Tunnel** | $0 | $0 | $0 |
| **Tailscale** | $0 | $0 | $0 |
| **Dynamic DNS + VPN** | $0 | $5-10 | $60-120 |
| **VPS Reverse Proxy** | $0 | $5-10 | $60-120 |

**Recommended:** Cloudflare Tunnel + Tailscale = **$0/year**

---

## Security Considerations

### Cloudflare Tunnel Benefits

1. **No open ports** - Outbound connection only
2. **DDoS protection** - Cloudflare absorbs attacks
3. **WAF available** - Web Application Firewall (paid)
4. **Rate limiting** - Built-in
5. **Geo-blocking** - Restrict by country
6. **TLS termination** - SSL handled by Cloudflare

### Tailscale Benefits

1. **Zero-trust** - End-to-end encrypted
2. **No public exposure** - Private network
3. **Device authentication** - Each device authorized
4. **Access logs** - See who accessed what
5. **ACLs** - Fine-grained access control

### Best Practices

1. **Never expose admin interfaces publicly**
   - Proxmox, TrueNAS, etc. → Tailscale only

2. **Use strong authentication on public services**
   - BasicAuth or OAuth on public Traefik routes

3. **Enable Cloudflare Access (optional paid feature)**
   - Email-based authentication
   - Identity provider integration

4. **Monitor access logs**
   - Traefik access logs
   - Cloudflare analytics

5. **Keep services updated**
   - Regular Docker updates
   - Security patches

---

## Quick Start Guide

### For Admin Access (Tailscale)

1. **Install Tailscale on your device:**
   ```bash
   # Mac/Linux
   brew install tailscale

   # Windows
   Download from tailscale.com
   ```

2. **Connect to your network:**
   ```bash
   tailscale up
   ```

3. **Access services via LAN IPs or .local domains:**
   ```
   https://proxmox.local.getmassive.com.au
   https://truenas.local.getmassive.com.au
   ```

### For Public Access (Cloudflare Tunnel)

1. **Already configured!**
   - Tunnel running on CT 106
   - Currently serving uptime.getmassive.com.au

2. **To add more services:**
   - Add hostname in Cloudflare dashboard
   - Point to `https://10.16.1.4:443`
   - Add router in Traefik config.yml
   - Create DNS CNAME record

3. **Access from anywhere:**
   ```
   https://status.getmassive.com.au
   (add more as needed)
   ```

---

## Monitoring & Maintenance

### Check Cloudflare Tunnel Status

```bash
# On CT 106 (docker00)
ssh root@10.16.1.22 "pct exec 106 -- ps aux | grep cloudflared"
```

### Check Traefik Status

```bash
# On VM 100
ssh dp@10.16.1.4 "docker ps | grep traefik"
```

### View Access Logs

**Cloudflare:**
- Dashboard → Analytics → Traffic

**Traefik:**
```bash
ssh dp@10.16.1.4 "docker logs traefik | tail -50"
```

### Test External Access

```bash
# From external network (phone/LTE)
curl -I https://status.getmassive.com.au
```

---

## Troubleshooting

### Public URL not accessible

1. **Check Cloudflare tunnel:**
   ```bash
   ssh root@10.16.1.22 "pct exec 106 -- ps aux | grep cloudflared"
   ```

2. **Check DNS:**
   ```bash
   dig status.getmassive.com.au
   # Should show CNAME to .cfargotunnel.com
   ```

3. **Check Traefik router:**
   ```bash
   # Verify router exists in config.yml
   ssh dp@10.16.1.4 "grep -A 10 'status.getmassive' /dockerland/traefik/config.yml"
   ```

4. **Check backend service:**
   ```bash
   # Service must be accessible from Traefik
   ssh dp@10.16.1.4 "curl -I http://10.16.1.4:3001"
   ```

### Tailscale not connecting

1. **Check container status:**
   ```bash
   ssh root@10.16.1.22 "pct status 901"
   ```

2. **Check Tailscale status:**
   ```bash
   ssh root@10.16.1.22 "pct exec 901 -- tailscale status"
   ```

3. **Check exit node:**
   ```bash
   # On your device
   tailscale status | grep "offers exit node"
   ```

---

## Recommendations

### Immediate Actions

1. ✅ **Keep using Tailscale** - Works great, already configured
2. ✅ **Expand Cloudflare tunnel** - Add services you want public
3. ✅ **Keep Traefik for internal** - Local access (fast, secure)

### Future Enhancements

1. **Add Cloudflare Access** (optional paid feature)
   - Email authentication for public services
   - Identity provider integration

2. **Enable Traefik access logs**
   - Monitor who's accessing what
   - Troubleshooting

3. **Setup Grafana dashboard**
   - Visualize access patterns
   - Monitor performance

---

## Summary

**Problem:** Dynamic IP + No port forwarding

**Solution:** ✅ **You already have everything you need!**

- **Tailscale (CT 901)** - Private admin access ✅
- **Cloudflare Tunnel (CT 106)** - Public service access ✅
- **Traefik (VM 100)** - Internal routing ✅

**Next step:** Just expand Cloudflare tunnel config to expose additional services you want public.

**Cost:** $0/month
**Complexity:** Low (already working)
**Security:** High (no open ports, encrypted)

---

**Status:** Solution identified, infrastructure ready
**Action Required:** Configure Cloudflare dashboard to add more public hostnames
**Estimated Time:** 15-30 minutes to add a new public service
