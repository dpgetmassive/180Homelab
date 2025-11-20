# Phase 1: Nginx Proxy Manager + gmdojo.tech Setup

**Date:** 2025-11-16
**Objective:** Replace Traefik with Nginx Proxy Manager + migrate to gmdojo.tech domain
**Decision:** GUI-based management (NPM), only expose Uptime Kuma publicly

---

## Phase 1 Overview

### What We're Building

**Old Architecture:**
```
Internet → Cloudflare Tunnel → Traefik (Docker) → Docker Containers
                                  ↓
                          *.local.getmassive.com.au
```

**New Architecture:**
```
Internet → Cloudflare Tunnel → Nginx Proxy Manager (LXC) → LXC Containers
                                  ↓
                             *.gmdojo.tech (internal only)
                             status.gmdojo.tech (public via tunnel)
```

---

## Step 1: Cloudflare DNS Setup

### 1.1: Verify Domain in Cloudflare

**Check domain status:**
- Domain: `gmdojo.tech`
- Nameservers should point to Cloudflare
- Account: `3993eb0547e077e081089690928540d7`

**Dashboard URL:**
```
https://dash.cloudflare.com/<account-id>/gmdojo.tech/dns/records
```

### 1.2: Create Internal DNS Records (Pi-hole)

**Add to Pi-hole (10.16.1.4:82/admin):**

```
# Internal wildcard - all services resolve internally
*.gmdojo.tech          A    10.16.1.50    (NPM LXC IP)

# Specific overrides if needed
pve.gmdojo.tech        A    10.16.1.22    (Proxmox scratchy)
nas.gmdojo.tech        A    10.16.1.6     (TrueNAS)
fw.gmdojo.tech         A    10.16.1.249   (OPNsense)
```

**Result:** All `*.gmdojo.tech` requests from LAN go to NPM at 10.16.1.50

### 1.3: Create Public DNS Records (Cloudflare)

**Only for Uptime Kuma public access:**

```
# Public status page via Cloudflare Tunnel
status.gmdojo.tech     CNAME    d4b4b44c-97d0-46f3-8890-2f3d6040231b.cfargotunnel.com
```

**DO NOT create:**
- ❌ Wildcard `*.gmdojo.tech` in Cloudflare (security risk)
- ❌ A records pointing to your public IP (no port forwarding)

**Result:** Only `status.gmdojo.tech` is publicly accessible via tunnel

---

## Step 2: Create Nginx Proxy Manager LXC

### 2.1: Create LXC Container

**Container Specs:**
- CTID: 200
- Hostname: nginx-proxy-manager
- IP: 10.16.1.50
- RAM: 1 GB
- Cores: 2
- Storage: 8 GB

**Create command:**
```bash
ssh root@10.16.1.22 "pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
    --hostname nginx-proxy-manager \
    --memory 1024 \
    --cores 2 \
    --net0 name=eth0,bridge=vmbr0,ip=10.16.1.50/24,gw=10.16.1.1 \
    --rootfs local-lvm:8 \
    --unprivileged 1 \
    --features nesting=1 \
    --onboot 1 \
    --startup order=10 \
    --nameserver 10.16.1.4 \
    --searchdomain gmdojo.tech"
```

### 2.2: Start Container

```bash
ssh root@10.16.1.22 "pct start 200"
```

### 2.3: Install Nginx Proxy Manager

**Method 1: Docker inside LXC (Recommended)**
```bash
# Enter container
ssh root@10.16.1.22 "pct enter 200"

# Update system
apt update && apt upgrade -y

# Install Docker
apt install -y curl
curl -fsSL https://get.docker.com | sh

# Create NPM directory
mkdir -p /opt/nginx-proxy-manager

# Create docker-compose.yml
cat > /opt/nginx-proxy-manager/docker-compose.yml <<'EOF'
version: '3.8'
services:
  app:
    image: 'jc21/nginx-proxy-manager:latest'
    restart: unless-stopped
    ports:
      - '80:80'
      - '443:443'
      - '81:81'  # Admin interface
    environment:
      DB_SQLITE_FILE: "/data/database.sqlite"
    volumes:
      - ./data:/data
      - ./letsencrypt:/etc/letsencrypt
EOF

# Start NPM
cd /opt/nginx-proxy-manager
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

**Method 2: Native Installation**
```bash
# Enter container
ssh root@10.16.1.22 "pct enter 200"

# Run NPM installation script
apt update && apt upgrade -y
apt install -y curl

# Install NPM (official script)
curl -fsSL https://raw.githubusercontent.com/jc21/nginx-proxy-manager/master/scripts/install.sh | bash
```

### 2.4: Access NPM Admin Interface

**URL:** `http://10.16.1.50:81`

**Default Credentials:**
```
Email:    admin@example.com
Password: changeme
```

**First Login:**
1. Change email to: `dp@getmassive.com.au`
2. Change password to something secure
3. Update profile

---

## Step 3: Configure NPM SSL Certificates

### 3.1: Add Cloudflare API Token

**In NPM Admin (http://10.16.1.50:81):**

1. Go to **SSL Certificates** → **Add SSL Certificate**
2. Select **Let's Encrypt**
3. Domain Names: `*.gmdojo.tech`, `gmdojo.tech`
4. Use DNS Challenge: **Yes**
5. DNS Provider: **Cloudflare**
6. Credentials File Content:
```
dns_cloudflare_api_token = aGSMUr8pQcAH4vuueTVCfyENElLKRUGVwMmNDIPn
```
7. Email: `dp@getmassive.com.au`
8. Click **Save**

**NPM will:**
- Request wildcard certificate for `*.gmdojo.tech`
- Use Cloudflare DNS API to validate
- No inbound port 80 needed!

### 3.2: Verify Certificate

**Should see:**
- Certificate: `*.gmdojo.tech`
- Expires: 90 days from now
- Status: Valid
- Auto-renew: Enabled

---

## Step 4: Create Proxy Hosts in NPM

### 4.1: Proxmox (pve.gmdojo.tech)

**In NPM Admin:**
1. **Proxy Hosts** → **Add Proxy Host**
2. **Details tab:**
   - Domain Names: `pve.gmdojo.tech`
   - Scheme: `https`
   - Forward Hostname/IP: `10.16.1.22`
   - Forward Port: `8006`
   - ✅ Cache Assets
   - ✅ Block Common Exploits
   - ✅ Websockets Support
3. **SSL tab:**
   - SSL Certificate: Select `*.gmdojo.tech` (from Step 3)
   - ✅ Force SSL
   - ✅ HTTP/2 Support
   - ✅ HSTS Enabled
4. **Advanced tab:**
```nginx
# Proxmox requires this to bypass SSL verification
proxy_ssl_verify off;
```
5. Click **Save**

### 4.2: Test Proxmox Access

**From LAN:**
```bash
curl -I https://pve.gmdojo.tech
# Should return 200 OK

# Open in browser
open https://pve.gmdojo.tech
```

### 4.3: Add More Services (Examples)

**Uptime Kuma (uptime.gmdojo.tech):**
- Forward to: `http://10.16.1.4:3001` (Docker container for now)
- SSL: `*.gmdojo.tech`
- Websockets: ✅ Enabled

**Grafana (grafana.gmdojo.tech):**
- Forward to: `http://10.16.1.4:3002`
- SSL: `*.gmdojo.tech`

**TrueNAS (nas.gmdojo.tech):**
- Forward to: `https://10.16.1.6`
- SSL: `*.gmdojo.tech`
- Advanced:
```nginx
proxy_ssl_verify off;
```

**Pi-hole (pihole.gmdojo.tech):**
- Forward to: `http://10.16.1.4:82/admin`
- SSL: `*.gmdojo.tech`

**Homer (home.gmdojo.tech):**
- Forward to: `http://10.16.1.4:81`
- SSL: `*.gmdojo.tech`

---

## Step 5: Update Cloudflare Tunnel for Public Access

### 5.1: Update Tunnel Configuration (CT 106)

**Current tunnel serves:**
- `uptime.getmassive.au` → VM 100 Uptime Kuma

**Update to serve:**
- `status.gmdojo.tech` → NPM → Uptime Kuma

**Option A: Via Cloudflare Dashboard**
1. Go to: https://one.dash.cloudflare.com/3993eb0547e077e081089690928540d7/networks/tunnels
2. Find tunnel: `d4b4b44c-97d0-46f3-8890-2f3d6040231b`
3. Edit public hostname:
   - Old: `uptime.getmassive.au`
   - New: `status.gmdojo.tech`
   - Service: `https://10.16.1.50` (NPM, not Uptime Kuma directly)
4. Save

**Option B: Via config file on CT 106**
```bash
# SSH to docker00 CT
ssh root@10.16.1.22 "pct enter 106"

# Edit tunnel config (if using config file)
nano /etc/cloudflared/config.yml

# Update ingress rules
ingress:
  - hostname: status.gmdojo.tech
    service: https://10.16.1.50
    originRequest:
      noTLSVerify: true

# Restart tunnel
systemctl restart cloudflared
```

### 5.2: Update Cloudflare DNS

**In Cloudflare DNS:**
1. Remove old CNAME: `uptime.getmassive.au`
2. Add new CNAME: `status.gmdojo.tech` → `d4b4b44c-97d0-46f3-8890-2f3d6040231b.cfargotunnel.com`

### 5.3: Create NPM Proxy Host for Public Status

**In NPM:**
1. **Proxy Hosts** → **Add Proxy Host**
2. Domain: `status.gmdojo.tech`
3. Forward to: `http://10.16.1.4:3001` (Uptime Kuma)
4. SSL: Use `*.gmdojo.tech` certificate
5. Websockets: ✅ Enabled
6. Save

### 5.4: Test Public Access

**From external network (phone/LTE):**
```bash
curl -I https://status.gmdojo.tech
# Should return 200 OK
```

**Architecture flow:**
```
Internet
  ↓
Cloudflare Edge (status.gmdojo.tech)
  ↓
Cloudflare Tunnel (CT 106 @ 10.16.1.40)
  ↓
Nginx Proxy Manager (CT 200 @ 10.16.1.50)
  ↓
Uptime Kuma (Docker @ 10.16.1.4:3001)
```

---

## Step 6: Parallel Operation (Keep Traefik Running)

### 6.1: Keep Both Running

**Traefik (Docker):**
- Still serving: `*.local.getmassive.com.au`
- Port: 443
- All existing services working

**NPM (LXC):**
- Now serving: `*.gmdojo.tech`
- Port: 443 (on 10.16.1.50)
- Only new services added here

**No conflict because:**
- Different IP addresses (10.16.1.4 vs 10.16.1.50)
- Different domains (getmassive.com.au vs gmdojo.tech)
- Pi-hole resolves based on domain

### 6.2: Update Bookmarks Gradually

**Start using new URLs:**
- `https://pve.gmdojo.tech` → Proxmox
- `https://uptime.gmdojo.tech` → Uptime Kuma
- `https://grafana.gmdojo.tech` → Grafana

**Old URLs still work:**
- `https://proxmox.local.getmassive.com.au`
- `https://uptime-kuma.local.getmassive.com.au`
- `https://grafana.local.getmassive.com.au`

---

## Step 7: Testing & Validation

### 7.1: Internal Access Tests

**From LAN workstation:**
```bash
# Test NPM is accessible
curl -I http://10.16.1.50:81
# Should return: NPM admin login page

# Test SSL certificate
curl -I https://pve.gmdojo.tech
# Should return: 200 OK with valid SSL

# Test DNS resolution
dig pve.gmdojo.tech @10.16.1.4
# Should return: 10.16.1.50

# Test services
curl -I https://uptime.gmdojo.tech
curl -I https://grafana.gmdojo.tech
curl -I https://nas.gmdojo.tech
```

### 7.2: Public Access Tests

**From external network (disable VPN):**
```bash
# Test public status page
curl -I https://status.gmdojo.tech
# Should return: 200 OK

# Test internal services are NOT public
curl -I https://grafana.gmdojo.tech
# Should fail (no public DNS record)
```

### 7.3: SSL Certificate Validation

**Check certificate details:**
```bash
openssl s_client -connect pve.gmdojo.tech:443 -servername pve.gmdojo.tech < /dev/null | openssl x509 -noout -subject -dates

# Should show:
# subject=CN = *.gmdojo.tech
# notBefore=<date>
# notAfter=<90 days from now>
```

---

## Step 8: Monitoring & Troubleshooting

### 8.1: NPM Logs

**View NPM logs:**
```bash
ssh root@10.16.1.22 "pct enter 200"

# If using Docker
cd /opt/nginx-proxy-manager
docker compose logs -f

# If native install
journalctl -u nginx-proxy-manager -f
```

### 8.2: Check NPM Status

**NPM Admin Dashboard:**
- URL: `http://10.16.1.50:81`
- Check proxy host status (green = working)
- Check SSL certificate status (valid)
- View access logs per host

### 8.3: Common Issues

**Issue: SSL certificate fails**
```
Error: DNS validation failed
```
**Fix:** Check Cloudflare API token has DNS edit permissions

**Issue: Proxy host shows 502 Bad Gateway**
```
Error: Backend not reachable
```
**Fix:** Verify backend IP/port is correct and service is running

**Issue: Can't access NPM admin**
```
Error: Connection refused on port 81
```
**Fix:** Check NPM container is running, firewall allows port 81

---

## Step 9: Documentation Updates

### 9.1: Update Service URLs

**Create bookmark list:**
```
# Infrastructure
https://pve.gmdojo.tech          - Proxmox (scratchy)
https://nas.gmdojo.tech          - TrueNAS
https://fw.gmdojo.tech           - OPNsense

# Monitoring
https://uptime.gmdojo.tech       - Uptime Kuma
https://grafana.gmdojo.tech      - Grafana
https://status.gmdojo.tech       - Public status (external)

# Applications
https://plex.gmdojo.tech         - Plex
https://sonarr.gmdojo.tech       - Sonarr
https://pihole.gmdojo.tech       - Pi-hole

# Admin
https://npm.gmdojo.tech          - NPM Admin (port 81)
https://portainer.gmdojo.tech    - Portainer
```

### 9.2: Update README

**Add to homelab README.md:**
- New domain: gmdojo.tech
- NPM location: CT 200 @ 10.16.1.50
- Admin access: http://10.16.1.50:81
- Cloudflare API token location

---

## Phase 1 Completion Checklist

**Infrastructure:**
- [ ] gmdojo.tech domain verified in Cloudflare
- [ ] NPM LXC created (CT 200 @ 10.16.1.50)
- [ ] NPM installed and running
- [ ] NPM admin accessible (port 81)

**DNS Configuration:**
- [ ] Pi-hole wildcard: `*.gmdojo.tech → 10.16.1.50`
- [ ] Cloudflare CNAME: `status.gmdojo.tech → tunnel`
- [ ] DNS resolution working (internal)

**SSL Certificates:**
- [ ] Wildcard cert for `*.gmdojo.tech` issued
- [ ] Certificate valid and trusted
- [ ] Auto-renewal configured

**Proxy Hosts:**
- [ ] Proxmox: `pve.gmdojo.tech` working
- [ ] Uptime Kuma: `uptime.gmdojo.tech` working
- [ ] Grafana: `grafana.gmdojo.tech` working
- [ ] TrueNAS: `nas.gmdojo.tech` working

**Public Access:**
- [ ] Cloudflare tunnel updated
- [ ] Public status page: `status.gmdojo.tech` working
- [ ] Other services NOT publicly accessible

**Testing:**
- [ ] Internal access verified (all services)
- [ ] External access verified (status only)
- [ ] SSL certificates valid
- [ ] Old URLs still working (Traefik)

**Documentation:**
- [ ] Bookmark list created
- [ ] README updated
- [ ] Cloudflare tokens documented

---

## Next Steps (Phase 2)

After Phase 1 is complete and stable (1 week):

1. **Migrate Uptime Kuma** to LXC (pilot service)
2. **Update NPM proxy host** to point to new LXC
3. **Test thoroughly**
4. **Move to next service**

---

## Rollback Plan

**If NPM has issues:**
1. Keep using Traefik (still running)
2. Old URLs: `*.local.getmassive.com.au` still work
3. Remove Pi-hole DNS for `*.gmdojo.tech`
4. Stop NPM container: `pct stop 200`
5. Investigate and fix

**No downtime to existing services!**

---

## Estimated Timeline

**Phase 1 Total:** 2-4 hours

- Step 1 (DNS): 15 minutes
- Step 2 (Create LXC): 10 minutes
- Step 3 (SSL): 30 minutes
- Step 4 (Proxy Hosts): 1-2 hours
- Step 5 (Cloudflare Tunnel): 30 minutes
- Step 6-9 (Testing/Docs): 30 minutes

---

**Status:** Ready to begin Phase 1
**Risk Level:** Low (Traefik stays running as backup)
**Reversibility:** High (easy rollback)
