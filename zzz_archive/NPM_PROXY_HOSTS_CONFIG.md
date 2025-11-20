# NPM Proxy Host Configurations for gmdojo.tech

**Date:** 2025-11-16
**NPM Admin:** http://10.16.1.50:81
**Domain:** gmdojo.tech
**SSL Certificate:** `*.gmdojo.tech` (already configured)

---

## Proxy Host Configurations

### 1. Proxmox (pve.gmdojo.tech)

**Details Tab:**
- Domain Names: `pve.gmdojo.tech`
- Scheme: `https`
- Forward Hostname/IP: `10.16.1.22`
- Forward Port: `8006`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
proxy_ssl_verify off;
```

---

### 2. Uptime Kuma (uptime.gmdojo.tech)

**Details Tab:**
- Domain Names: `uptime.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.4`
- Forward Port: `3001`
- ✅ Block Common Exploits
- ✅ Websockets Support (REQUIRED)

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# No additional config needed
```

---

### 3. Grafana (grafana.gmdojo.tech)

**Details Tab:**
- Domain Names: `grafana.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.4`
- Forward Port: `3002`
- ✅ Block Common Exploits
- ✅ Websockets Support

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# No additional config needed
```

---

### 4. TrueNAS (nas.gmdojo.tech)

**Details Tab:**
- Domain Names: `nas.gmdojo.tech`
- Scheme: `https`
- Forward Hostname/IP: `10.16.1.6`
- Forward Port: `443`
- ✅ Cache Assets
- ✅ Block Common Exploits
- ✅ Websockets Support

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
proxy_ssl_verify off;
```

---

### 5. Pi-hole (pihole.gmdojo.tech)

**Details Tab:**
- Domain Names: `pihole.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.4`
- Forward Port: `82`
- ✅ Block Common Exploits

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
location / {
    proxy_pass http://10.16.1.4:82/admin/;
}
```

---

### 6. Homer Dashboard (home.gmdojo.tech)

**Details Tab:**
- Domain Names: `home.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.4`
- Forward Port: `81`
- ✅ Cache Assets
- ✅ Block Common Exploits

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# No additional config needed
```

---

### 7. NPM Admin (npm.gmdojo.tech)

**Details Tab:**
- Domain Names: `npm.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.50`
- Forward Port: `81`
- ✅ Block Common Exploits

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# No additional config needed
```

---

### 8. Public Status Page (status.gmdojo.tech)

**Details Tab:**
- Domain Names: `status.gmdojo.tech`
- Scheme: `http`
- Forward Hostname/IP: `10.16.1.4`
- Forward Port: `3001`
- ✅ Block Common Exploits
- ✅ Websockets Support (REQUIRED)

**SSL Tab:**
- SSL Certificate: `*.gmdojo.tech`
- ✅ Force SSL
- ✅ HTTP/2 Support
- ✅ HSTS Enabled

**Advanced Tab:**
```nginx
# No additional config needed
```

**Note:** This will be accessed publicly via Cloudflare Tunnel

---

## Testing Commands

After creating the proxy hosts, test with:

```bash
# Test Proxmox
curl -I https://pve.gmdojo.tech

# Test Uptime Kuma
curl -I https://uptime.gmdojo.tech

# Test Grafana
curl -I https://grafana.gmdojo.tech

# Test TrueNAS
curl -I https://nas.gmdojo.tech

# Test Pi-hole
curl -I https://pihole.gmdojo.tech

# Test Homer
curl -I https://home.gmdojo.tech

# Test NPM Admin
curl -I https://npm.gmdojo.tech

# Test Status (internal)
curl -I https://status.gmdojo.tech
```

---

## Automation

See `scripts/configure-npm-proxies.sh` for automated proxy host creation via NPM API.

---

## Next Steps After Proxy Hosts are Created

1. Test all internal URLs
2. Update Cloudflare Tunnel to point to `https://10.16.1.50` for `status.gmdojo.tech`
3. Test public access to status page
4. Update bookmarks/Homer dashboard with new URLs
5. Verify Traefik old URLs still work (parallel operation)
