# Homelab Monitoring Recommendation

**Goal**: Simple, lightweight monitoring with ~1 week metric retention

**Last Updated:** 2025-11-10

---

## Current State

You already have **two** monitoring solutions running:

### 1. Beszel (rova-beszel - 10.25.1.20)
- **Status**: ✅ Running on port 8090
- **Architecture**: Hub + Agent model
- **Agent Location**: Docker on rova-docka (10.25.1.12)
- **Weight**: Very lightweight (single Go binary)
- **Database**: SQLite
- **Not exposed via Traefik yet**

### 2. CheckMK (rova-checkmk - 10.25.1.22)
- **Status**: ✅ Running
- **URL**: https://cmk-mon.rova.getmassive.com.au/monitoring
- **Weight**: Heavier (full monitoring platform)
- **Features**: Enterprise-grade monitoring

---

## Recommendation: Use Beszel as Primary

**Winner: Beszel** ✅

### Why Beszel?

1. **Already Installed**: You have it running!
2. **Extremely Lightweight**:
   - ~10MB RAM for hub
   - ~5MB RAM per agent
   - Single Go binary
   - SQLite database (no separate DB needed)

3. **Perfect for Your Requirements**:
   - ✅ Simple and minimal
   - ✅ Configurable retention (set to 7 days)
   - ✅ Very lightweight
   - ✅ Fast and responsive
   - ✅ Beautiful modern UI

4. **Easy Deployment**:
   - Hub: Single binary
   - Agents: Docker container or binary
   - SSH-based monitoring (no agent needed for some systems)

5. **Key Metrics Covered**:
   - CPU usage
   - Memory usage
   - Disk usage
   - Network I/O
   - System load
   - Container stats (Docker)

### Why Not CheckMK?

CheckMK is excellent but **overkill** for your needs:
- Much heavier resource usage
- Complex configuration
- Enterprise features you don't need
- Longer setup time
- More maintenance overhead

You can keep it as a secondary/backup or remove it to free resources.

---

## Implementation Plan

### Phase 1: Expose Beszel via Traefik (15 minutes)

#### Step 1: Add Traefik Route

Add to `/dockerland/traefik/config.yml`:

```yaml
    beszel:
      entryPoints:
        - "https"
      rule: "Host(`beszel.rova.getmassive.com.au`)"
      middlewares:
        - default-headers
        - https-redirectscheme
      tls: {}
      service: beszel
```

And service:

```yaml
    beszel:
      loadBalancer:
        servers:
          - url: "http://10.25.1.20:8090/"
        passHostHeader: true
```

#### Step 2: Add OPNsense DNS Override

- Host: `beszel.rova`
- Domain: `getmassive.com.au`
- IP: `10.25.1.12`

#### Step 3: Add to SERVICES.md

```markdown
- Beszel: https://beszel.rova.getmassive.com.au
```

### Phase 2: Configure Retention (5 minutes)

SSH to rova-beszel and configure retention:

```bash
ssh 10.25.1.20

# Edit Beszel config (location may vary)
# Set retention to 7 days in config or via web UI
```

### Phase 3: Deploy Agents to All Hosts (30 minutes)

You already have one agent on rova-docka. Deploy to other critical hosts.

**Option 1: Docker Agent** (for hosts with Docker)
```yaml
version: '3.8'
services:
  beszel-agent:
    image: henrygd/beszel-agent
    container_name: beszel-agent
    restart: unless-stopped
    network_mode: host
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

**Option 2: SSH Monitoring** (for hosts without Docker)
Beszel can monitor via SSH - no agent needed!
- Add hosts in Beszel web UI
- Provide SSH credentials
- Beszel pulls metrics via SSH

**Option 3: Binary Agent** (lightweight)
```bash
# Download beszel agent binary
wget https://github.com/henrygd/beszel/releases/latest/download/beszel-agent-linux-amd64
chmod +x beszel-agent-linux-amd64
mv beszel-agent-linux-amd64 /usr/local/bin/beszel-agent

# Create systemd service
cat > /etc/systemd/system/beszel-agent.service << 'EOF'
[Unit]
Description=Beszel Agent
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/beszel-agent
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable beszel-agent
systemctl start beszel-agent
```

### Recommended Agent Deployment

Deploy agents to:
- [x] rova-docka (already has agent)
- [ ] pve-rover01 (Proxmox host) - **Critical**
- [ ] rova-checkmk (ironically, monitor the monitor)
- [ ] rover-plexd (Plex performance)
- [ ] rova-sabnzbd (download monitoring)
- [ ] opnsense01 (firewall) - via SSH monitoring

Others can use SSH-based monitoring from Beszel hub.

---

## Alternative Options (If You Don't Want Beszel)

### Option 2: Netdata ⭐⭐⭐⭐
**Best alternative if starting fresh**

**Pros**:
- Beautiful real-time dashboards
- Zero configuration
- Auto-detects everything
- Very lightweight (can limit retention)
- Single-line install
- Excellent for troubleshooting

**Cons**:
- Real-time focus (not great for historical)
- Default retention is longer (can configure)
- More resource usage than Beszel (but still light)

**Install**:
```bash
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

**Metrics Retention**: Configure to 7 days in `/etc/netdata/netdata.conf`:
```ini
[global]
    history = 604800  # 7 days in seconds
```

---

### Option 3: Prometheus + Grafana ⭐⭐⭐
**Industry standard, but heavier**

**Pros**:
- Powerful query language (PromQL)
- Flexible and extensible
- Grafana dashboards are gorgeous
- Large ecosystem

**Cons**:
- More complex setup
- Heavier resource usage
- Overkill for simple monitoring
- Two components to manage

**Not recommended for your use case** - too heavy and complex.

---

### Option 4: Uptime Kuma ⭐⭐⭐⭐
**Best for uptime/availability monitoring**

**Note**: This is different from system metrics!

**Pros**:
- Simple uptime monitoring
- Beautiful UI
- Multi-protocol (HTTP, TCP, Ping, etc.)
- Status pages
- Very lightweight

**Cons**:
- Not for system metrics (CPU, RAM, disk)
- Focused on service availability only

**Use Case**: Complement Beszel with Uptime Kuma for availability checks.

---

### Option 5: Glances ⭐⭐
**Real-time terminal-based monitoring**

**Pros**:
- Lightweight Python tool
- Works in terminal (SSH-friendly)
- Can export to various backends
- Web UI available

**Cons**:
- Terminal-focused
- Not great for historical data
- Less polished UI

---

## Comparison Matrix

| Feature | Beszel | Netdata | Prometheus/Grafana | CheckMK | Uptime Kuma |
|---------|--------|---------|-------------------|---------|-------------|
| **Lightweight** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Easy Setup** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **UI Quality** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **System Metrics** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ |
| **Uptime Checks** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Retention Config** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | N/A |
| **Resource Usage** | ~15MB | ~50MB | ~200MB+ | ~500MB+ | ~20MB |
| **Already Installed** | ✅ Yes | ❌ No | ❌ No | ✅ Yes | ❌ No |

---

## Final Recommendation

### Primary: Beszel ✅

**Action Plan**:
1. Expose Beszel via Traefik (15 min)
2. Configure 7-day retention (5 min)
3. Deploy agents to critical hosts (30 min)
4. **Total time: < 1 hour**

### Optional Add-on: Uptime Kuma

If you want **uptime monitoring** in addition to metrics:
- Deploy Uptime Kuma in Docker on rova-docka
- Monitor service availability (HTTP checks)
- Get notifications when services go down
- Complement Beszel's system metrics

### What to Do with CheckMK?

**Two options**:

1. **Keep as backup** - It's already there, uses minimal resources when not actively used
2. **Remove to free resources**:
   ```bash
   pct stop 116
   pct destroy 116
   ```

---

## Beszel Configuration Example

### Set 7-Day Retention

In Beszel web UI (http://10.25.1.20:8090):
1. Settings → General
2. Set "Data Retention" to 7 days
3. Save

Or via config file (if exists at `/opt/beszel/config.yml`):
```yaml
retention:
  days: 7
```

### Add SSH-Based Monitoring (No Agent Needed)

For lightweight hosts, monitor via SSH:
1. In Beszel UI: Add System
2. Choose "SSH" method
3. Provide host IP and SSH credentials
4. Beszel pulls metrics via SSH

This is perfect for:
- LXC containers without Docker
- Hosts where you don't want to install anything
- Pi-hole, Glance, etc.

---

## Resource Usage Estimates

### Current State (with both CheckMK and Beszel):
- CheckMK: ~500-1000MB RAM
- Beszel Hub: ~10MB RAM
- Beszel Agents: ~5MB each

### Recommended State (Beszel only):
- Beszel Hub: ~10MB RAM
- Beszel Agents (5 hosts): ~25MB RAM
- **Total: ~35MB RAM** (vs 500-1000MB with CheckMK)
- **Savings: 465-965MB RAM freed**

---

## Quick Start Commands

### Access Beszel Now
```bash
# Directly (from internal network)
http://10.25.1.20:8090

# After adding Traefik route
https://beszel.rova.getmassive.com.au
```

### Deploy Agent via Ansible (Automated)

Create `deploy-beszel-agents.yml`:
```yaml
---
- name: Deploy Beszel Agents
  hosts: all:!ansible:!opnsense01
  become: yes
  tasks:
    - name: Download Beszel agent
      get_url:
        url: https://github.com/henrygd/beszel/releases/latest/download/beszel-agent-linux-amd64
        dest: /usr/local/bin/beszel-agent
        mode: '0755'

    - name: Create systemd service
      copy:
        dest: /etc/systemd/system/beszel-agent.service
        content: |
          [Unit]
          Description=Beszel Agent
          After=network.target

          [Service]
          Type=simple
          User=root
          ExecStart=/usr/local/bin/beszel-agent
          Restart=always
          Environment="PORT=45876"
          Environment="KEY={{ beszel_key }}"

          [Install]
          WantedBy=multi-user.target

    - name: Enable and start agent
      systemd:
        name: beszel-agent
        enabled: yes
        state: started
        daemon_reload: yes
```

Run:
```bash
ansible-playbook deploy-beszel-agents.yml
```

---

## Monitoring Dashboard Design

### Recommended Metrics to Watch:

**System Health**:
- CPU usage (alert > 80%)
- Memory usage (alert > 85%)
- Disk usage (alert > 90%)
- System load average

**Services**:
- Docker container status
- Service uptime
- Network throughput

**Storage**:
- Disk I/O
- Available space on /mnt/pve/terra

---

## Summary

**Recommendation**: Use **Beszel** as your primary monitoring solution.

**Why**:
- ✅ Already installed
- ✅ Extremely lightweight (~35MB total)
- ✅ Simple and beautiful UI
- ✅ Perfect for 7-day retention
- ✅ Easy to deploy agents
- ✅ Can monitor via SSH (no agent needed)

**Next Steps**:
1. Expose Beszel via Traefik
2. Configure 7-day retention
3. Deploy agents to critical hosts
4. Optionally remove CheckMK to free 500MB+ RAM

**Total Implementation Time**: < 1 hour

**Alternative**: If you want to try something new, **Netdata** is also excellent and similarly lightweight, but you'd need to install it from scratch.
