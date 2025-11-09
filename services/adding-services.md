# How to Add New Services to Homelab

This guide explains the complete process for adding a new web-accessible service to the homelab infrastructure.

**Last Updated:** 2025-11-10

## Overview: How DNS and Routing Works

### Architecture Summary

```
External Client Request:
Internet → Cloudflare DNS → Cloudflare Tunnel (10.25.1.19) → Traefik (10.25.1.12) → Backend Service

Internal Client Request (Split-Brain DNS):
Internal Client → OPNsense DNS (10.16.66.1) → Traefik (10.25.1.12) → Backend Service
```

### Key Components

1. **OPNsense Unbound DNS (10.16.66.1)** - Internal DNS server with host overrides
2. **Cloudflare DNS** - Public DNS for external access
3. **Cloudflare Tunnel (10.25.1.19)** - Secure tunnel from Cloudflare edge to homelab
4. **Traefik (10.25.1.12)** - Reverse proxy with automatic HTTPS
5. **Backend Services** - Your actual applications (Sonarr, Radarr, etc.)

### Split-Brain DNS Explanation

The homelab uses **split-brain DNS** to optimize internal traffic:

- **Internal clients** (devices on your network) bypass the Cloudflare Tunnel entirely
  - Query OPNsense DNS → Get 10.25.1.12 → Direct to Traefik
  - Faster, no round-trip to Cloudflare
  - Still uses HTTPS with Let's Encrypt certificates

- **External clients** (devices outside your network)
  - Query Cloudflare DNS → Get Cloudflare IPs
  - Traffic routes through Cloudflare Tunnel (10.25.1.19)
  - Cloudflare Tunnel forwards to Traefik (10.25.1.12)
  - Traefik routes to backend service

### DNS Configuration Locations

#### OPNsense (Internal DNS)
- **Location**: Services → Unbound DNS → Overrides → Host Overrides
- **Config File**: `/var/unbound/host_entries.conf` (auto-generated)
- **Purpose**: Provides internal DNS resolution to bypass Cloudflare Tunnel
- **Format**: Each subdomain explicitly defined

#### Cloudflare (External DNS)
- **Location**: Cloudflare Dashboard → DNS Settings
- **Purpose**: Routes external traffic through Cloudflare Tunnel
- **Format**: CNAME records pointing to Cloudflare Tunnel hostname

## Step-by-Step: Adding a New Service

### Prerequisites

- Service is running and accessible on an internal IP and port
- You have admin access to OPNsense firewall
- You have admin access to Cloudflare account
- You have SSH access to rova-docka (10.25.1.12)

### Example: Adding Radarr

We'll use Radarr as the example throughout this guide.
- Service: Radarr (movie management)
- Host: rova-radarr (10.25.1.24)
- Port: 7878
- Desired URL: https://radarr.rova.getmassive.com.au

---

## Step 1: Verify Service is Running

First, confirm your service is accessible on the network:

```bash
# SSH to the ansible host
ssh root@10.25.1.25

# Check the service is running
ssh <service-ip> 'ss -tlnp | grep LISTEN'
```

**Example:**
```bash
ssh 10.25.1.24 'ss -tlnp | grep LISTEN'
# Output should show:
# LISTEN 0  512  *:7878  *:*  users:(("Radarr",pid=89,fd=246))
```

Note the port number - you'll need it for Traefik configuration.

---

## Step 2: Add Traefik Configuration

Traefik needs both a **router** (defines the URL) and a **service** (defines the backend).

### 2.1: Backup Current Config

```bash
ssh root@10.25.1.25
ssh 10.25.1.12
cd /dockerland/traefik
cp config.yml config.yml.backup.$(date +%Y%m%d)
```

### 2.2: Download and Edit Config

On your local machine or via ansible host:
```bash
# Via ansible host
ssh root@10.25.1.25 "ssh 10.25.1.12 'cat /dockerland/traefik/config.yml'" > /tmp/traefik_config.yml
```

### 2.3: Add Router Entry

In the `#region routers` section, add your new service:

```yaml
    radarr:
      entryPoints:
        - "https"
      rule: "Host(`radarr.rova.getmassive.com.au`)"
      middlewares:
        - default-headers
        - https-redirectscheme
      tls: {}
      service: radarr
```

**Configuration Breakdown:**
- `radarr:` - Unique name for this router
- `entryPoints: ["https"]` - Accept HTTPS traffic only
- `rule:` - Match requests to this hostname
- `middlewares:` - Apply security headers and HTTP→HTTPS redirect
- `tls: {}` - Enable TLS (uses wildcard cert automatically)
- `service:` - Points to the service definition (created in next step)

### 2.4: Add Service Entry

In the `#region services` section, add the backend definition:

```yaml
    radarr:
      loadBalancer:
        servers:
          - url: "http://10.25.1.24:7878/"
        passHostHeader: true
```

**Configuration Breakdown:**
- `radarr:` - Matches the service name in router
- `loadBalancer.servers:` - Backend server(s) to forward to
- `url:` - Internal URL (protocol://ip:port/)
- `passHostHeader: true` - Pass the original Host header to backend

### 2.5: Upload and Apply Config

```bash
# Upload to ansible host
scp /tmp/traefik_config.yml root@10.25.1.25:/tmp/config.yml

# Copy to rova-docka
ssh root@10.25.1.25 "scp /tmp/config.yml 10.25.1.12:/dockerland/traefik/config.yml"

# Restart Traefik to apply changes
ssh root@10.25.1.25 "ssh 10.25.1.12 'cd /dockerland/traefik && docker-compose restart'"
```

### 2.6: Verify Traefik Config

Check Traefik logs for errors:
```bash
ssh root@10.25.1.25 "ssh 10.25.1.12 'docker logs traefik --tail 50'"
```

You should see Traefik load the new configuration without errors.

---

## Step 3: Add Internal DNS Override (OPNsense)

For internal clients to access the service without going through Cloudflare Tunnel:

### 3.1: Access OPNsense Web Interface

1. Navigate to: `https://10.16.1.1`
2. Login with admin credentials
3. Go to: **Services → Unbound DNS → Overrides**

### 3.2: Add Host Override

Click "+" to add a new Host Override:

| Field | Value | Example |
|-------|-------|---------|
| **Host** | `<subdomain>.rova` | `radarr.rova` |
| **Domain** | `getmassive.com.au` | `getmassive.com.au` |
| **Type** | `A (IPv4 address)` | `A (IPv4 address)` |
| **IP** | `10.25.1.12` | `10.25.1.12` |
| **Description** | Brief description | `Radarr via Traefik` |

**Important Notes:**
- Always use `10.25.1.12` as the IP (Traefik host)
- Do NOT use the backend service IP
- The host field format is: `subdomain.rova` (not full domain)

### 3.3: Apply Changes

1. Click **Save**
2. Click **Apply** to restart Unbound DNS
3. Wait ~10 seconds for DNS cache to clear

### 3.4: Test Internal DNS Resolution

From any internal machine:
```bash
dig radarr.rova.getmassive.com.au +short
# Should return: 10.25.1.12

nslookup radarr.rova.getmassive.com.au
# Should show server 10.16.66.1 returning 10.25.1.12
```

---

## Step 4: Add External DNS (Cloudflare)

For external clients to access the service:

### 4.1: Access Cloudflare Dashboard

1. Log into: https://dash.cloudflare.com
2. Select domain: `getmassive.com.au`
3. Go to: **DNS → Records**

### 4.2: Check for Wildcard Record

Look for an existing wildcard record:
- Type: `CNAME`
- Name: `*.rova` or `*.rova.getmassive.com.au`
- Target: `<tunnel-id>.cfargotunnel.com`

### 4.3: Add DNS Record

**If wildcard exists:**
- You're done! The wildcard covers all `*.rova.getmassive.com.au` subdomains
- Skip to Step 5

**If NO wildcard exists:**
- Click **Add Record**
- Fill in:
  - **Type**: `CNAME`
  - **Name**: `radarr.rova` (or full: `radarr.rova.getmassive.com.au`)
  - **Target**: `<your-tunnel-id>.cfargotunnel.com`
  - **Proxy status**: Proxied (orange cloud)
  - **TTL**: Auto
- Click **Save**

### 4.4: Find Your Cloudflare Tunnel Hostname

To find your tunnel hostname, check existing DNS records in Cloudflare to see what other services point to, or check the cloudflared service configuration.

### 4.5: Test External DNS Resolution

From external network (or using public DNS):
```bash
nslookup radarr.rova.getmassive.com.au 8.8.8.8
# Should return Cloudflare IPs (104.21.x.x or 172.67.x.x)
```

---

## Step 5: Update Documentation

Update the homelab documentation repository:

### 5.1: Update SERVICES.md

```bash
ssh root@10.25.1.25
cd /root/homelab-docs
nano SERVICES.md
```

Add your new service URL to the **Public Services** section:
```markdown
- Radarr: https://radarr.rova.getmassive.com.au
```

### 5.2: Commit Changes

```bash
cd /root/homelab-docs
git add SERVICES.md
git commit -m "Add Radarr service"
git push origin main
```

---

## Step 6: Test End-to-End

### 6.1: Test Internal Access

From an internal machine:
```bash
curl -k https://radarr.rova.getmassive.com.au
# Should return HTML or redirect to service
```

Or open in browser: `https://radarr.rova.getmassive.com.au`

### 6.2: Test External Access (Optional)

From external network or using mobile data:
- Open: `https://radarr.rova.getmassive.com.au`
- Should route through Cloudflare Tunnel

### 6.3: Check Traefik Dashboard

Access: `https://traefik-dashboard.rova.getmassive.com.au`
- Verify new router and service appear
- Check for any errors or warnings

---

## Common Issues and Troubleshooting

### Issue: Service not accessible internally

**Check DNS:**
```bash
dig radarr.rova.getmassive.com.au +short
```
- Should return: `10.25.1.12`
- If not, check OPNsense Host Override

**Check Traefik routing:**
```bash
ssh root@10.25.1.25 "ssh 10.25.1.12 'docker logs traefik --tail 100'"
```

**Check backend service:**
```bash
ssh root@10.25.1.25 "ssh 10.25.1.24 'ss -tlnp | grep 7878'"
```

### Issue: Service not accessible externally

**Check Cloudflare DNS:**
- Verify CNAME record exists and is proxied (orange cloud)

**Check Cloudflare Tunnel:**
```bash
ssh root@10.25.1.25 "ssh 10.25.1.19 'systemctl status cloudflared'"
```

### Issue: SSL certificate errors

Traefik should automatically obtain a wildcard cert for `*.rova.getmassive.com.au`.

Check Traefik logs for certificate issues.

### Issue: Service returns 404 or 502

**404 Not Found:**
- Traefik can't find a matching router
- Check hostname in browser matches `rule:` in config.yml

**502 Bad Gateway:**
- Backend service is down or unreachable
- Check service IP and port in Traefik service definition
- Verify backend service is running

---

## Configuration Files Reference

### Traefik Config Location
```
Host: rova-docka (10.25.1.12)
Path: /dockerland/traefik/config.yml
```

### OPNsense DNS Overrides
```
Host: opnsense01 (10.16.1.1)
Location: Services → Unbound DNS → Overrides → Host Overrides
Config: /var/unbound/host_entries.conf (auto-generated)
```

### Cloudflare Tunnel Config
```
Host: rova-cloudflared (10.25.1.19)
Service: cloudflared
```

### Documentation Repository
```
Host: ansible (10.25.1.25)
Path: /root/homelab-docs/
Repo: https://github.com/dpgetmassive/180Homelab
```

---

## Quick Reference Commands

### Restart Traefik
```bash
ssh root@10.25.1.25 "ssh 10.25.1.12 'cd /dockerland/traefik && docker-compose restart'"
```

### View Traefik Logs
```bash
ssh root@10.25.1.25 "ssh 10.25.1.12 'docker logs traefik -f'"
```

### Test DNS Resolution
```bash
dig <service>.rova.getmassive.com.au +short
```

### Restart OPNsense DNS
Via web interface: Services → Unbound DNS → Restart

### Check Service Port
```bash
ssh root@10.25.1.25 "ssh <service-ip> 'ss -tlnp | grep LISTEN'"
```

---

## Service Naming Conventions

For consistency, follow these naming patterns:

| Service Type | Subdomain Pattern | Example |
|--------------|------------------|---------|
| Arr Services | Service name | `sonar`, `radarr`, `lidarr` |
| Download Clients | Client name | `sabnzb`, `transmission` |
| Media Servers | Server name | `plex`, `jellyfin` |
| Management Tools | Tool name | `portainer`, `proxmox1` |
| Monitoring | Service-mon | `cmk-mon`, `grafana-mon` |

---

## Related Documentation

- [Docker Infrastructure](docker.md) - Docker and Traefik details
- [Network Documentation](../NETWORK.md) - Network architecture
- [SERVICES.md](../SERVICES.md) - All available services
- [INVENTORY.md](../INVENTORY.md) - Host inventory

---

## Summary Checklist

When adding a new service, complete these steps:

- [ ] Verify service is running and accessible (Step 1)
- [ ] Add Traefik router configuration (Step 2.3)
- [ ] Add Traefik service configuration (Step 2.4)
- [ ] Upload config and restart Traefik (Step 2.5)
- [ ] Add OPNsense DNS Host Override (Step 3)
- [ ] Add or verify Cloudflare DNS record (Step 4)
- [ ] Update SERVICES.md documentation (Step 5)
- [ ] Commit and push to Git (Step 5.2)
- [ ] Test internal access (Step 6.1)
- [ ] Test external access (Step 6.2)

**Estimated time to add new service:** 10-15 minutes
