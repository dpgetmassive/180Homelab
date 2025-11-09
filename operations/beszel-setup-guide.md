# Beszel Monitoring Setup Guide

**Status**: SSH keys configured on all 17 hosts ✅

**Last Updated:** 2025-11-10

---

## What Was Done

✅ **Beszel SSH key added to all hosts** - Beszel can now SSH to any host for monitoring
✅ **Traefik configured** - https://beszel.rova.getmassive.com.au
✅ **Documentation updated**

---

## Access Beszel

**URL**: https://beszel.rova.getmassive.com.au

(After you add the OPNsense DNS override for `beszel.rova`)

---

## Add Systems to Beszel (Web UI)

### Method: SSH-Based Monitoring (Recommended - No Agent Needed!)

Beszel can monitor all your systems via SSH - no need to install agents. This is perfect for your lightweight setup.

### Step-by-Step for Each Host:

1. **Log into Beszel**: https://beszel.rova.getmassive.com.au
2. **Click "Add System"** or "+" button
3. **Fill in details**:
   - **Name**: (use hostname from list below)
   - **Host**: (IP address from list below)
   - **Port**: `22`
   - **User**: `root`
   - **Connection Type**: **SSH**

4. **Authentication**:
   - Beszel will use its SSH key (already added to authorized_keys)
   - No password needed!

5. **Click Save/Add**

---

## Systems to Add (Priority Order)

### Critical Infrastructure (Add These First)

#### 1. Proxmox Host
```
Name: pve-rover01
Host: 10.25.1.5
Port: 22
User: root
Connection: SSH
Priority: CRITICAL (hypervisor)
```

#### 2. Docker Host
```
Name: rova-docka
Host: 10.25.1.12
Port: 22
User: root
Connection: SSH
Priority: CRITICAL (Traefik + containers)
Note: Already has Docker agent, but SSH works too
```

#### 3. Firewall
```
Name: opnsense01
Host: 10.16.1.1
Port: 22
User: root
Connection: SSH
Priority: CRITICAL (network gateway)
```

#### 4. DNS/Ad Blocking
```
Name: rova-pihole
Host: 10.25.1.15
Port: 22
User: root
Connection: SSH
Priority: HIGH (DNS service)
```

#### 5. Cloudflare Tunnel
```
Name: rova-cloudflared
Host: 10.25.1.19
Port: 22
User: root
Connection: SSH
Priority: HIGH (external access)
```

### Media Services

#### 6. Plex Media Server
```
Name: rover-plexd
Host: 10.25.1.11
Port: 22
User: root
Connection: SSH
```

#### 7. Sonarr (TV)
```
Name: rova-sonarr
Host: 10.25.1.16
Port: 22
User: root
Connection: SSH
```

#### 8. Radarr (Movies)
```
Name: rova-radarr
Host: 10.25.1.24
Port: 22
User: root
Connection: SSH
```

#### 9. SABnzbd (Downloads)
```
Name: rova-sabnzbd
Host: 10.25.1.14
Port: 22
User: root
Connection: SSH
```

#### 10. SABnzbd Old
```
Name: rover-sabnzbd-old
Host: 10.25.1.53
Port: 22
User: root
Connection: SSH
Note: Old instance, lower priority
```

#### 11. Transmission (Torrents)
```
Name: rova-transmission
Host: 10.25.1.13
Port: 22
User: root
Connection: SSH
```

#### 12. Filerr (File Management)
```
Name: rova-filerr
Host: 10.25.1.10
Port: 22
User: root
Connection: SSH
```

### Monitoring & Utilities

#### 13. CheckMK (Existing Monitoring)
```
Name: rova-checkmk
Host: 10.25.1.22
Port: 22
User: root
Connection: SSH
Note: Monitor the monitor!
```

#### 14. Beszel Hub (Self-Monitoring)
```
Name: rova-beszel
Host: 10.25.1.20
Port: 22
User: root
Connection: SSH
Note: Monitor itself for meta-monitoring
```

#### 15. Glance Dashboard
```
Name: rova-glance
Host: 10.25.1.23
Port: 22
User: root
Connection: SSH
```

#### 16. VS Code Server
```
Name: rova-vscode-srv
Host: 10.25.1.21
Port: 22
User: root
Connection: SSH
```

#### 17. Tailscale VPN
```
Name: rova-tailscale
Host: 10.25.1.18
Port: 22
User: root
Connection: SSH
```

---

## Quick Add Script (All Hosts)

You can copy/paste these into Beszel's bulk add feature (if available):

```csv
pve-rover01,10.25.1.5,22,root,ssh
rova-docka,10.25.1.12,22,root,ssh
opnsense01,10.16.1.1,22,root,ssh
rova-pihole,10.25.1.15,22,root,ssh
rova-cloudflared,10.25.1.19,22,root,ssh
rover-plexd,10.25.1.11,22,root,ssh
rova-sonarr,10.25.1.16,22,root,ssh
rova-radarr,10.25.1.24,22,root,ssh
rova-sabnzbd,10.25.1.14,22,root,ssh
rover-sabnzbd-old,10.25.1.53,22,root,ssh
rova-transmission,10.25.1.13,22,root,ssh
rova-filerr,10.25.1.10,22,root,ssh
rova-checkmk,10.25.1.22,22,root,ssh
rova-beszel,10.25.1.20,22,root,ssh
rova-glance,10.25.1.23,22,root,ssh
rova-vscode-srv,10.25.1.21,22,root,ssh
rova-tailscale,10.25.1.18,22,root,ssh
```

---

## Configure Data Retention

After adding systems:

1. Go to **Settings** in Beszel UI
2. Find **Data Retention** setting
3. Set to **7 days** (or your preferred duration)
4. Click **Save**

---

## What Metrics You'll See

For each system via SSH monitoring, Beszel will show:

- **CPU Usage** - Overall and per-core
- **Memory Usage** - Used vs available RAM
- **Disk Usage** - All mounted filesystems
- **Network I/O** - Bandwidth in/out
- **System Load** - Load average
- **Uptime** - System uptime
- **Process Count** - Running processes

For rova-docka (Docker host), you'll also see:
- **Container Stats** - If Docker agent is running
- **Container Status** - Running/stopped containers

---

## Advantages of SSH-Based Monitoring

✅ **No agent installation needed** - One less thing to manage
✅ **Lighter weight** - No agent process running
✅ **Easier maintenance** - No agents to update
✅ **Still gets all metrics** - Full system monitoring
✅ **Secure** - Uses SSH key authentication

The only downside: Slightly higher CPU on Beszel hub during polls (negligible).

---

## Alternative: Docker Agent (Optional)

If you want even more detailed metrics on rova-docka, the Docker agent is already running!

To see Docker-specific metrics in Beszel:
1. Add system as Docker agent type instead of SSH
2. Use connection string from Docker agent logs

But honestly, SSH monitoring is probably sufficient for your needs.

---

## Monitoring Dashboard Tips

### Useful Views:

1. **Overview Dashboard** - See all systems at a glance
2. **Alerts** - Set thresholds:
   - CPU > 80%
   - Memory > 85%
   - Disk > 90%
3. **Graphs** - Historical data for trending

### Recommended Alerts:

- **Proxmox (pve-rover01)**: CPU > 85%, Memory > 90%
- **Docker Host (rova-docka)**: Disk > 85% (Traefik logs can fill up)
- **Plex (rover-plexd)**: CPU > 90% (transcoding spikes)
- **SABnzbd (rova-sabnzbd)**: Disk > 90% (download space)

---

## Troubleshooting

### System Won't Connect

**Check SSH from Beszel host**:
```bash
ssh root@10.25.1.25
ssh 10.25.1.20
ssh -i /opt/beszel/beszel_data/id_ed25519 root@<host-ip>
```

Should connect without password.

### Metrics Not Updating

- Check system is online: `ping <host-ip>`
- Verify SSH access works
- Check Beszel hub logs: `ssh 10.25.1.20 'journalctl -u beszel -f'`

### Missing Metrics

SSH monitoring provides standard metrics. For advanced metrics:
- Install Beszel agent binary
- Or use CheckMK for deeper monitoring

---

## Next Steps

1. ✅ Add OPNsense DNS override for `beszel.rova` → `10.25.1.12`
2. ✅ Access Beszel UI: https://beszel.rova.getmassive.com.au
3. ✅ Add all 17 systems using SSH monitoring (use list above)
4. ✅ Configure 7-day retention
5. ✅ Set up alerts for critical systems
6. ✅ (Optional) Remove CheckMK to free 500MB+ RAM

---

## Time Estimate

- Adding all 17 systems: ~10-15 minutes
- Configuring alerts: ~5 minutes
- **Total**: ~20 minutes

Enjoy your lightweight monitoring! 🎉

---

## Documentation Location

This guide: `/root/homelab-docs/operations/beszel-setup-guide.md`
