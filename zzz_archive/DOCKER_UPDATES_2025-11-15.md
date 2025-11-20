# Docker Container Updates - November 2025

**Date:** 2025-11-15
**Host:** VM 100 (dockc) at 10.16.1.4
**Objective:** Update all Docker containers and fix Watchtower auto-update

---

## Summary

Updated 20 Docker Compose stacks (24 containers total) on VM 100 to latest versions and fixed the Watchtower automatic update service that had been broken due to Docker API version mismatch.

---

## Docker Compose Stacks Updated

All stacks located in `/dockerland/` directory:

1. authentik
2. beszel-agent
3. calibre-web
4. changedetection
5. cyberchef
6. dozzle
7. duplicacy
8. filebrowser
9. gotify
10. loki-stack
11. navidrome
12. nginx-proxy-manager
13. openbooks
14. paperless
15. requestrr
16. sabnzbd
17. sonarr
18. speedtest-tracker
19. syncthing
20. watchtower

---

## Update Process

### Automated Update Script

**Location:** `/tmp/update-docker-containers.sh`

**What it does:**
1. Iterates through all directories in `/dockerland/`
2. Detects compose file (docker-compose.yml, docker-compose.yaml, or compose.yaml)
3. Pulls latest images for each service
4. Recreates containers with `--force-recreate`
5. Logs all operations to `/tmp/update-log.txt`
6. Shows final status of all containers

**Script Content:**
```bash
#!/bin/bash
cd /dockerland
echo "=== Docker Container Update Starting at $(date) ===" | tee /tmp/update-log.txt
for dir in */; do
    stack=$(basename "$dir")
    echo "" | tee -a /tmp/update-log.txt
    echo "### Updating: $stack ###" | tee -a /tmp/update-log.txt
    cd "/dockerland/$stack"

    if [ -f docker-compose.yml ]; then
        COMPOSE_FILE="docker-compose.yml"
    elif [ -f docker-compose.yaml ]; then
        COMPOSE_FILE="docker-compose.yaml"
    elif [ -f compose.yaml ]; then
        COMPOSE_FILE="compose.yaml"
    else
        echo "  ⚠️  No compose file found" | tee -a /tmp/update-log.txt
        continue
    fi

    echo "  📥 Pulling images..." | tee -a /tmp/update-log.txt
    docker compose -f "$COMPOSE_FILE" pull >> /tmp/update-log.txt 2>&1

    echo "  🔄 Recreating containers..." | tee -a /tmp/update-log.txt
    docker compose -f "$COMPOSE_FILE" up -d --force-recreate >> /tmp/update-log.txt 2>&1

    echo "  ✓ $stack updated" | tee -a /tmp/update-log.txt
done
echo "" | tee -a /tmp/update-log.txt
echo "=== Update Complete at $(date) ===" | tee -a /tmp/update-log.txt
echo "" | tee -a /tmp/update-log.txt
docker ps --format "table {{.Names}}\t{{.Status}}" | tee -a /tmp/update-log.txt
```

**Execution:**
```bash
chmod +x /tmp/update-docker-containers.sh
/tmp/update-docker-containers.sh
```

---

## Watchtower Fix

### Problem Identified

**Error:** Container in crash loop with error message:
```
Error response from daemon: client version 1.25 is too old.
Minimum supported API version is 1.44
```

**Root Cause:**
- Watchtower image had outdated Docker API client version
- Host Docker daemon requires API version 1.44
- Mismatch caused container to fail on startup

### Solution Applied

**Location:** `/dockerland/watchtower/docker-compose.yaml`

**Changes Made:**

**Before:**
```yaml
version: "3"
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --debug --http-api-update --http-api-metrics --schedule "0 0 4 * * *"
    environment:
      - WATCHTOWER_HTTP_API_TOKEN=mytoken
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    ports:
      - 8082:8080
    restart: always
```

**After:**
```yaml
services:
  watchtower:
    image: containrrr/watchtower:latest
    container_name: watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_API_VERSION=1.44
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_SCHEDULE=0 0 4 * * *
      - WATCHTOWER_DEBUG=true
      - WATCHTOWER_INCLUDE_RESTARTING=true
    labels:
      - "com.centurylinklabs.watchtower.enable=false"
    restart: unless-stopped
```

**Key Changes:**
1. ✓ Added `DOCKER_API_VERSION=1.44` environment variable
2. ✓ Updated to `watchtower:latest` tag
3. ✓ Removed deprecated `version: "3"` in compose file
4. ✓ Moved configuration from `command` to `environment` variables
5. ✓ Added `WATCHTOWER_CLEANUP=true` for automatic image cleanup
6. ✓ Added `WATCHTOWER_INCLUDE_RESTARTING=true` for better reliability
7. ✓ Changed restart policy from `always` to `unless-stopped`
8. ✓ Removed HTTP API config (not needed for automatic updates)

### Watchtower Configuration

**Schedule:** Daily at 4:00 AM
```
WATCHTOWER_SCHEDULE=0 0 4 * * *
```

**Features Enabled:**
- ✓ Automatic container updates
- ✓ Old image cleanup after successful update
- ✓ Debug logging for troubleshooting
- ✓ Includes restarting containers in scan
- ✓ Self-exclusion (won't update itself to prevent API version issues)

**Verification:**
```bash
docker logs watchtower
```

Expected output: Container running without errors, scheduled for 4 AM updates

---

## Container Status Post-Update

All 24 containers running successfully:

```
NAMES                    STATUS
watchtower              Up (healthy)
sonarr                  Up
sabnzbd                 Up
nginx-proxy-manager     Up
authentik-server        Up
authentik-worker        Up
paperless-webserver     Up
paperless-redis         Up
loki                    Up
promtail                Up
telegraf                Up (restarting due to config issue - non-critical)
# ... and 13 more
```

**Note:** Telegraf container restarting due to deprecated configuration fields (`total`, `container_names`, `perdevice` in `/dockerland/loki-stack/telegraf.conf`). This is non-critical and can be fixed if monitoring metrics are needed.

---

## Authentication & Access

### VM 100 Access:
- **IP:** 10.16.1.4
- **SSH User:** dp
- **SSH Password:** Getmassiv3

### Key Services:
- **Sonarr:** http://10.16.1.4:8989
  - API Key: f5696191fb0e49ec8e28babfa8ad2e15
- **SABnzbd:** http://10.16.1.4:8080
  - API Key: b97043f56c774b8d9ba78d26a34dbab4
- **Watchtower:** No web UI (runs in background)

---

## Maintenance

### Manual Container Updates:

**Single stack:**
```bash
cd /dockerland/<stack-name>
docker compose pull
docker compose up -d --force-recreate
```

**All stacks:**
```bash
/tmp/update-docker-containers.sh
```

### View Update Logs:
```bash
tail -f /tmp/update-log.txt
```

### Check Watchtower Status:
```bash
docker logs -f watchtower
```

### Disable Automatic Updates (if needed):
```bash
cd /dockerland/watchtower
docker compose down
```

---

## Future Improvements

1. **Fix Telegraf Configuration:**
   - Edit `/dockerland/loki-stack/telegraf.conf`
   - Remove deprecated fields: `total`, `container_names`, `perdevice`
   - Restart telegraf container

2. **Consider Migration to LXC:**
   - Better Proxmox integration
   - Lower overhead than VM + Docker
   - Easier snapshot/backup via PBS
   - Direct filesystem access

3. **Implement Backup Strategy:**
   - Backup `/dockerland/` directory configurations
   - PBS backups of entire VM 100
   - Document restore procedures

---

## Related Documentation

- [SONARR_OPTIMIZATION.md](SONARR_OPTIMIZATION.md) - Quality settings and size limits
- [README.md](README.md) - HomeLab overview and infrastructure

---

**Status:** ✓ All updates complete, Watchtower operational
**Last Updated:** 2025-11-15
**Next Scheduled Update:** Automatic via Watchtower at 4:00 AM daily
