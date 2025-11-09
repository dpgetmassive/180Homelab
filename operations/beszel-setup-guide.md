# Beszel Monitoring Setup Guide

**Status**: Binary agents installed on all 16 hosts ✅

**Last Updated:** 2025-11-10

---

## What Was Done

✅ **Binary agents installed** on 15 hosts via Ansible (port 45876)
✅ **Docker agent running** on rova-docka (already existed)
✅ **Traefik configured** - https://beszel.rova.getmassive.com.au
✅ **All agents active** and listening
✅ **Documentation updated**

---

## Access Beszel

**URL**: https://beszel.rova.getmassive.com.au

(After you add the OPNsense DNS override for `beszel.rova` → `10.25.1.12`)

---

## Agent Architecture

Beszel uses an **agent-based** monitoring system:

- **Hub**: rova-beszel (10.25.1.20:8090) - Web UI and data collection
- **Agents**: Installed on each monitored system (port 45876)
- **Connection**: Hub pulls metrics from agents via authenticated connection
- **Public Key**: ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKbl/kDZ6u7AXNkS188DSTcJt0kvC7U1Dl37OXpgpo+n

---

## Add Systems to Beszel (Web UI)

### Step-by-Step for Each Host:

1. **Log into Beszel**: https://beszel.rova.getmassive.com.au
2. **Click "Add New System"**
3. **Select "Binary" tab** (or "Docker" for rova-docka)
4. **Fill in details**:
   - **Name**: (hostname from list below)
   - **Host/IP**: (IP address from list below)
   - **Port**: `45876`
   - **Public Key**: (auto-filled, matches the key above)
5. **Click "Add system"**

---

## Systems with Agents Installed (16 total)

### Critical Infrastructure

#### 1. Proxmox Host
```
Name: pve-rover01
Host/IP: 10.25.1.5
Port: 45876
Tab: Binary
Priority: CRITICAL (hypervisor)
Agent: ✅ Installed
```

#### 2. Docker Host
```
Name: rova-docka
Host/IP: 10.25.1.12
Port: 45876
Tab: Docker (use Docker agent, not Binary)
Priority: CRITICAL (Traefik + containers)
Agent: ✅ Docker agent running
```

#### 3. DNS/Ad Blocking
```
Name: rova-pihole
Host/IP: 10.25.1.15
Port: 45876
Tab: Binary
Priority: HIGH (DNS service)
Agent: ✅ Installed
```

#### 4. Cloudflare Tunnel
```
Name: rova-cloudflared
Host/IP: 10.25.1.19
Port: 45876
Tab: Binary
Priority: HIGH (external access)
Agent: ✅ Installed
```

### Media Services

#### 5. Plex Media Server
```
Name: rover-plexd
Host/IP: 10.25.1.11
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 6. Sonarr (TV)
```
Name: rova-sonarr
Host/IP: 10.25.1.16
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 7. Radarr (Movies)
```
Name: rova-radarr
Host/IP: 10.25.1.24
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 8. SABnzbd (Primary)
```
Name: rova-sabnzbd
Host/IP: 10.25.1.14
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 9. SABnzbd (Old)
```
Name: rover-sabnzbd-old
Host/IP: 10.25.1.53
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 10. Transmission (Torrents)
```
Name: rova-transmission
Host/IP: 10.25.1.13
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 11. Filerr (File Management)
```
Name: rova-filerr
Host/IP: 10.25.1.10
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

### Monitoring & Utilities

#### 12. CheckMK (Monitoring)
```
Name: rova-checkmk
Host/IP: 10.25.1.22
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 13. Beszel Hub (Self-Monitoring)
```
Name: rova-beszel
Host/IP: 10.25.1.20
Port: 45876
Tab: Binary
Note: Monitor the monitor!
Agent: ✅ Installed
```

#### 14. Glance Dashboard
```
Name: rova-glance
Host/IP: 10.25.1.23
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 15. VS Code Server
```
Name: rova-vscode-srv
Host/IP: 10.25.1.21
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

#### 16. Tailscale VPN
```
Name: rova-tailscale
Host/IP: 10.25.1.18
Port: 45876
Tab: Binary
Agent: ✅ Installed
```

---

## Systems NOT Monitored

- **ansible** (10.25.1.25) - Ansible control node, skip monitoring
- **opnsense01** (10.16.1.1) - FreeBSD, agent install failed (systemd incompatible)

---

## Agent Management

### Check Agent Status on Any Host

```bash
ssh <hostname> systemctl status beszel-agent
```

### Restart Agent

```bash
ssh <hostname> systemctl restart beszel-agent
```

### View Agent Logs

```bash
ssh <hostname> journalctl -u beszel-agent -f
```

### Verify Agent Listening

```bash
ssh <hostname> ss -tlnp | grep 45876
```

---

## Configure Beszel Settings

### Set Data Retention

After adding systems:

1. Go to **Settings** in Beszel UI
2. Find **Data Retention** setting
3. Set to **7 days** (or your preferred duration)
4. Click **Save**

### Recommended Alerts

Set up alerts for:

**Critical Systems:**
- **pve-rover01**: CPU > 85%, Memory > 90%
- **rova-docka**: Disk > 85%, Memory > 85%
- **rova-pihole**: Service down alert

**Media Services:**
- **rover-plexd**: CPU > 90% (transcoding)
- **rova-sabnzbd**: Disk > 90% (download space)

---

## What Metrics You'll See

For each system, Beszel displays:

- **CPU Usage** - Overall and per-core percentage
- **Memory Usage** - Used vs available RAM
- **Disk Usage** - All mounted filesystems
- **Network I/O** - Bandwidth in/out
- **System Load** - Load average (1/5/15 min)
- **Uptime** - System uptime
- **Temperatures** - CPU/system temps (if available)

For **rova-docka** (Docker agent):
- **Container Stats** - CPU/memory per container
- **Container Status** - Running/stopped/health

---

## Troubleshooting

### Agent Not Connecting

**Check agent is running:**
```bash
ssh <hostname> systemctl status beszel-agent
```

**Check agent is listening:**
```bash
ssh <hostname> ss -tlnp | grep 45876
```

**Check agent logs:**
```bash
ssh <hostname> journalctl -u beszel-agent -n 50
```

### Wrong Public Key Error

If Beszel UI shows public key mismatch:

1. Get the correct key from Beszel hub:
   ```bash
   ssh 10.25.1.20 cat /opt/beszel/beszel_data/id_ed25519.pub
   ```

2. Reinstall agent with correct key (if needed)

### Port Already in Use

If port 45876 is taken, you can change it:

1. Edit systemd service:
   ```bash
   ssh <hostname> systemctl edit beszel-agent
   ```

2. Add:
   ```
   [Service]
   Environment="PORT=<new-port>"
   ```

3. Restart agent and update in Beszel UI

---

## Agent Installation Details

### What the Install Script Did

1. Created dedicated `beszel` user
2. Downloaded binary to `/usr/local/bin/beszel-agent`
3. Created systemd service at `/etc/systemd/system/beszel-agent.service`
4. Configured agent with public key authentication
5. Started and enabled service

### Agent Version

Check version:
```bash
ssh <hostname> /usr/local/bin/beszel-agent --version
```

Current version: **0.15.4**

### Agent Updates

Agents can auto-update if enabled during installation. To manually update:

```bash
ssh <hostname>
curl -sL https://raw.githubusercontent.com/henrygd/beszel/main/supplemental/scripts/install-agent.sh -o /tmp/update-agent.sh
chmod +x /tmp/update-agent.sh
/tmp/update-agent.sh
```

---

## Resource Usage

### Agent Overhead (Per Host)

- **Memory**: ~5-10 MB per agent
- **CPU**: < 1% (only during metric collection)
- **Disk**: ~20 MB (binary + logs)
- **Network**: Minimal (only when hub polls)

### Total Infrastructure

- **Beszel Hub**: ~10-15 MB RAM
- **16 Agents**: ~80-160 MB RAM total
- **Total**: ~100-175 MB RAM for entire monitoring system

Compare to CheckMK: ~500-1000 MB RAM (savings: 75-90%)

---

## Related Documentation

- [Monitoring Recommendation](monitoring-recommendation.md) - Why Beszel was chosen
- [Quick Add Systems Guide](beszel-add-systems.md) - Simplified copy/paste format
- [Beszel Hosts CSV](beszel-hosts.csv) - All hosts in CSV format
- [Official Beszel Docs](https://beszel.dev/guide/agent-installation)

---

## Time Estimate

- **Adding all 16 systems**: ~10-15 minutes
- **Configuring alerts**: ~5 minutes
- **Setting retention**: ~1 minute
- **Total**: ~15-20 minutes

---

## Summary

✅ **16 systems ready** to add in Beszel UI
✅ **All agents installed** and running on port 45876
✅ **Lightweight** - only ~100-175 MB RAM total
✅ **Secure** - public key authentication
✅ **Automatic** - systemd services, auto-restart

Just add them in the UI and you're monitoring! 🎉
