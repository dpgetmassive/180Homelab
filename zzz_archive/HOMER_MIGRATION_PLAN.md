# Homer Dashboard Migration Plan

**Status:** Ready to execute
**Difficulty:** ⭐ Easy (static site, no database)
**ETA:** 15 minutes

---

## Overview

**Homer** is a static dashboard application - the easiest type of migration!

**Source:** VM 100 Docker @ 10.16.1.4:81
**Target:** CT 204 (new LXC) @ 10.16.1.54:8080
**Data Size:** 1.9 MB (config + icons)

---

## Current Setup

### On VM 100

```yaml
# /dockerland/Homer/docker-compose.yml
services:
  homer:
    image: b4bz/homer
    container_name: homer
    volumes:
      - /dockerland/Homer/assets:/www/assets
    ports:
      - 81:8080
    environment:
      - UID=1000
      - GID=1000
    restart: unless-stopped
```

**Status:**
- ✅ Running and healthy
- ✅ Accessible at http://10.16.1.4:81
- ✅ Uptime: 2 hours
- ✅ Assets backed up (1.7 MB from previous session)

---

## Migration Strategy

Since Homer is a **static site** with no database:
1. Create new LXC container (CT 204)
2. Install nginx or use Homer's built-in web server
3. Copy `/dockerland/Homer/assets` folder
4. Deploy Homer (Docker or native nginx)
5. Update NPM proxy host
6. Test
7. Stop old Docker container

**Recommended approach:** Docker on LXC (same as source, easy migration)

---

## Step-by-Step Migration

### Step 1: Create LXC Container (5 min)

```bash
# On pve-scratchy
pct create 204 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname homer \
  --cores 1 \
  --memory 512 \
  --swap 512 \
  --net0 name=eth0,bridge=vmbr0,gw=10.16.1.1,ip=10.16.1.54/24,type=veth \
  --nameserver 10.16.1.16,1.1.1.1 \
  --searchdomain gm.local \
  --storage scratch-pve \
  --rootfs scratch-pve:8 \
  --unprivileged 1 \
  --features nesting=1 \
  --start 1
```

### Step 2: Install Docker in CT 204 (3 min)

```bash
# Wait for container to start
sleep 10

# Install Docker
pct exec 204 -- bash -c 'apt update && apt install -y curl'
pct exec 204 -- bash -c 'curl -fsSL https://get.docker.com | sh'
```

### Step 3: Copy Assets from VM 100 (2 min)

**Option A: Direct copy via HTTP**

```bash
# On VM 100 - start HTTP server
qm guest exec 100 -- bash -c 'cd /dockerland/Homer && python3 -m http.server 8887 &'

# On CT 204 - download and extract
pct exec 204 -- bash -c 'mkdir -p /opt/homer'
pct exec 204 -- bash -c 'cd /opt/homer && wget -r -np -nH --cut-dirs=2 http://10.16.1.4:8887/assets/'
```

**Option B: Tar and transfer**

```bash
# On VM 100 - create tar
qm guest exec 100 -- bash -c 'cd /dockerland/Homer && tar czf /tmp/homer-assets.tar.gz assets/'

# Copy to Proxmox host
sshpass -p 'Getmassiv3' ssh root@10.16.1.22 \
  "qm guest exec 100 -- cat /tmp/homer-assets.tar.gz" > /tmp/homer-assets.tar.gz

# Copy to CT 204
pct push 204 /tmp/homer-assets.tar.gz /tmp/homer-assets.tar.gz

# Extract on CT 204
pct exec 204 -- bash -c 'mkdir -p /opt/homer && cd /opt/homer && tar xzf /tmp/homer-assets.tar.gz'
```

### Step 4: Deploy Homer on CT 204 (2 min)

```bash
# Create docker-compose.yml
pct exec 204 -- bash -c 'cat > /opt/homer/docker-compose.yml << EOF
version: "3"
services:
  homer:
    image: b4bz/homer:latest
    container_name: homer
    volumes:
      - /opt/homer/assets:/www/assets
    ports:
      - 8080:8080
    environment:
      - UID=1000
      - GID=1000
    restart: unless-stopped
EOF'

# Start Homer
pct exec 204 -- bash -c 'cd /opt/homer && docker-compose up -d'
```

### Step 5: Test New Homer (1 min)

```bash
# Check container is running
pct exec 204 -- docker ps | grep homer

# Test from your browser
open http://10.16.1.54:8080
```

**Verify:**
- Dashboard loads
- All icons display
- All links work
- Configuration preserved

### Step 6: Update NPM Proxy Host (2 min)

In NPM (http://10.16.1.50:81):

1. Go to **Proxy Hosts**
2. Find `home.gmdojo.tech` entry
3. Click **Edit**
4. **Details** tab:
   - Change "Forward Hostname/IP" from `10.16.1.4` to `10.16.1.54`
   - Change "Forward Port" from `81` to `8080`
5. Click **Save**

**Test:**
- Internal: http://home.gmdojo.tech (LAN access)
- External: https://home.gmdojo.tech (via Cloudflare tunnel)

### Step 7: Stop Old Homer on VM 100

```bash
# Stop Docker container
qm guest exec 100 -- docker stop homer

# Optional: Remove container
qm guest exec 100 -- docker rm homer
```

---

## Rollback Procedure

If new Homer doesn't work:

1. **Restart old Homer:**
```bash
qm guest exec 100 -- docker start homer
```

2. **Revert NPM proxy host:**
   - Change back to `10.16.1.4:81`

3. **Stop CT 204:**
```bash
pct stop 204
```

**Recovery time:** < 2 minutes

---

## Alternative: Native Nginx (No Docker)

If you prefer native deployment without Docker:

### Install nginx + Homer

```bash
# Install nginx
pct exec 204 -- apt install -y nginx wget unzip

# Download Homer
pct exec 204 -- bash -c 'cd /tmp && wget https://github.com/bastienwirtz/homer/releases/latest/download/homer.zip'
pct exec 204 -- bash -c 'mkdir -p /var/www/homer && cd /var/www/homer && unzip /tmp/homer.zip'

# Copy assets
# (transfer assets from VM 100 to /var/www/homer/assets/)

# Configure nginx
pct exec 204 -- bash -c 'cat > /etc/nginx/sites-available/homer << EOF
server {
    listen 8080;
    server_name _;
    root /var/www/homer;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF'

# Enable site
pct exec 204 -- ln -s /etc/nginx/sites-available/homer /etc/nginx/sites-enabled/
pct exec 204 -- rm /etc/nginx/sites-enabled/default
pct exec 204 -- systemctl restart nginx
```

---

## Configuration Files

### Homer config.yml location

```
Docker: /opt/homer/assets/config.yml
Native: /var/www/homer/assets/config.yml
```

**No changes needed** - config.yml is static and doesn't contain hardcoded IPs (all relative paths).

### Assets structure

```
assets/
├── config.yml          # Main configuration
├── icons/              # Service icons
│   ├── plex.png
│   ├── pihole.png
│   ├── unifi.png
│   └── ...
├── tools/              # Additional tools/scripts
└── fonts/              # Custom fonts (if any)
```

---

## Network Configuration

### NPM Proxy Host

| Setting | Value |
|---------|-------|
| **Domain** | home.gmdojo.tech |
| **Scheme** | http |
| **Forward Hostname** | 10.16.1.54 (new) |
| **Forward Port** | 8080 (new) |
| **Cache Assets** | Yes |
| **Block Exploits** | Yes |
| **Websockets** | No (not needed) |

### SSL

Since Homer is accessed via NPM:
- External: Cloudflare provides SSL automatically
- Internal: No SSL needed (or add Cloudflare Origin Cert to NPM)

---

## Testing Checklist

After migration, verify:

- [ ] Dashboard loads at http://10.16.1.54:8080
- [ ] All service icons display correctly
- [ ] All service links work (click each one)
- [ ] Search functionality works
- [ ] Theme/styling preserved
- [ ] NPM proxy works (http://home.gmdojo.tech)
- [ ] External access works (https://home.gmdojo.tech via tunnel)
- [ ] No console errors in browser (F12 dev tools)

---

## Post-Migration Tasks

### Immediate

1. **Test for 24 hours** - ensure stability
2. **Update documentation** - record new IP in your homelab docs
3. **Backup CT 204** - create Proxmox backup

### After 1 Week

1. **Stop old Homer** on VM 100 (if not already done)
2. **Remove Docker container** and image
3. **Clean up** `/dockerland/Homer` on VM 100

---

## Benefits of Migration

- ✅ **Dedicated container** - easier to manage
- ✅ **Resource isolation** - doesn't compete with other VM 100 services
- ✅ **Easy backups** - Proxmox LXC snapshots
- ✅ **Better monitoring** - dedicated container metrics
- ✅ **Easier updates** - `docker-compose pull && docker-compose up -d`

---

## Estimated Resource Usage

**CT 204 Requirements:**
- CPU: 1 core (more than enough)
- RAM: 512 MB (Homer is lightweight)
- Disk: 8 GB (only using ~200 MB)
- Network: Minimal (static files)

**Actual usage (expected):**
- CPU: < 1% idle, < 5% during access
- RAM: ~50 MB (Docker) or ~20 MB (nginx)
- Disk: ~10 MB (Homer) + 1.9 MB (assets)

---

## Automation Script (Optional)

Complete migration in one command:

```bash
#!/bin/bash
# homer-migration.sh

echo "Creating CT 204..."
pct create 204 local:vztmpl/debian-12-standard_12.7-1_amd64.tar.zst \
  --hostname homer --cores 1 --memory 512 --swap 512 \
  --net0 name=eth0,bridge=vmbr0,gw=10.16.1.1,ip=10.16.1.54/24,type=veth \
  --nameserver 10.16.1.16,1.1.1.1 --searchdomain gm.local \
  --storage scratch-pve --rootfs scratch-pve:8 \
  --unprivileged 1 --features nesting=1 --start 1

sleep 10

echo "Installing Docker..."
pct exec 204 -- bash -c 'apt update && apt install -y curl'
pct exec 204 -- bash -c 'curl -fsSL https://get.docker.com | sh'

echo "Copying assets..."
qm guest exec 100 -- bash -c 'cd /dockerland/Homer && tar czf /tmp/homer-assets.tar.gz assets/'
qm guest exec 100 -- cat /tmp/homer-assets.tar.gz | pct exec 204 -- bash -c 'cat > /tmp/homer-assets.tar.gz'
pct exec 204 -- bash -c 'mkdir -p /opt/homer && cd /opt/homer && tar xzf /tmp/homer-assets.tar.gz'

echo "Creating docker-compose.yml..."
pct exec 204 -- bash -c 'cat > /opt/homer/docker-compose.yml << "EOF"
version: "3"
services:
  homer:
    image: b4bz/homer:latest
    container_name: homer
    volumes:
      - /opt/homer/assets:/www/assets
    ports:
      - 8080:8080
    environment:
      - UID=1000
      - GID=1000
    restart: unless-stopped
EOF'

echo "Starting Homer..."
pct exec 204 -- bash -c 'cd /opt/homer && docker-compose up -d'

echo "Migration complete! Test at: http://10.16.1.54:8080"
echo "Update NPM proxy host to point to 10.16.1.54:8080"
```

---

## Summary

Homer migration is **straightforward**:
- No database to migrate
- Static config files
- Small data size (1.9 MB)
- No complex dependencies
- Quick rollback available

**Total downtime:** < 5 minutes (just NPM proxy update)

**Confidence level:** 🟢 High (simplest migration type)

Ready to execute when you are!
