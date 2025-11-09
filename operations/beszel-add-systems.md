# Beszel - Add Systems Quick Reference

**All agents installed and running!** ✅

Just add them in the Beszel UI now.

---

## How to Add Each System

1. Go to: https://beszel.rova.getmassive.com.au
2. Click **"Add New System"**
3. Select **"Binary"** tab
4. Fill in details from list below
5. Click **"Add system"**

---

## Systems to Add (Port 45876 for all)

### Critical Infrastructure

```
Name: pve-rover01
Host/IP: 10.25.1.5
Port: 45876
```

```
Name: rova-pihole
Host/IP: 10.25.1.15
Port: 45876
```

```
Name: rova-cloudflared
Host/IP: 10.25.1.19
Port: 45876
```

### Media Services

```
Name: rover-plexd
Host/IP: 10.25.1.11
Port: 45876
```

```
Name: rova-sonarr
Host/IP: 10.25.1.16
Port: 45876
```

```
Name: rova-radarr
Host/IP: 10.25.1.24
Port: 45876
```

```
Name: rova-sabnzbd
Host/IP: 10.25.1.14
Port: 45876
```

```
Name: rover-sabnzbd-old
Host/IP: 10.25.1.53
Port: 45876
```

```
Name: rova-transmission
Host/IP: 10.25.1.13
Port: 45876
```

```
Name: rova-filerr
Host/IP: 10.25.1.10
Port: 45876
```

### Monitoring & Utilities

```
Name: rova-checkmk
Host/IP: 10.25.1.22
Port: 45876
```

```
Name: rova-beszel
Host/IP: 10.25.1.20
Port: 45876
```

```
Name: rova-glance
Host/IP: 10.25.1.23
Port: 45876
```

```
Name: rova-vscode-srv
Host/IP: 10.25.1.21
Port: 45876
```

```
Name: rova-tailscale
Host/IP: 10.25.1.18
Port: 45876
```

### Docker Host (Use Docker Tab)

**rova-docka** - Already has Docker agent running:

1. Click **"Add New System"**
2. Select **"Docker"** tab
3. Fill in:
   ```
   Name: rova-docka
   Host/IP: 10.25.1.12
   Port: 45876
   ```
4. Public Key: (auto-filled)

---

## Not Added

- **ansible** (10.25.1.25) - Ansible control node, skip
- **opnsense01** (10.16.1.1) - FreeBSD, agent install failed

---

## Quick Copy/Paste Format

For each system, copy this and change the values:
```
Name: <hostname>
Host/IP: <ip-address>
Port: 45876
```

---

## After Adding All Systems

1. **Configure Retention**:
   - Settings → Data Retention → 7 days

2. **Set Up Alerts** (recommended):
   - CPU > 80%
   - Memory > 85%
   - Disk > 90%

3. **Verify** all systems show green/online

---

## Total Systems

- **15 Binary agents** installed and running
- **1 Docker agent** (rova-docka)
- **16 total** systems to add in Beszel UI

Time to add all: ~10-15 minutes

---

Done! 🎉
