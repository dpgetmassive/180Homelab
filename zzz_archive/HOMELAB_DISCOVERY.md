# Homelab Infrastructure Discovery Report
**Date:** 2025-11-15
**Network:** 10.16.1.0/24

---

## Executive Summary

Current homelab consists of 3 Proxmox nodes in a cluster running:
- **15 VMs total** (7 running, 8 stopped/templates)
- **8 LXC containers** (all running)
- **40+ Docker containers** across multiple hosts

**Consolidation Goal:** Migrate all active workloads to a single primary host with scheduled replication to a standby node.

---

## Proxmox Cluster Nodes

### 1. pve-itchy (10.16.1.8)
- **Hardware:** 8 cores, 31.21 GiB RAM
- **Storage:**
  - itchy-lvm-2: 976 GB (13% used)
  - ISO storage: 60 GB (83% used)
- **CPU Load:** 1.63%
- **Memory Usage:** 9.08 GiB / 31.21 GiB

### 2. pve-scratchy (10.16.1.22)
- **Hardware:** 12 cores, 46.88 GiB RAM
- **Storage:**
  - scratch-pve (LVM): 976 GB (16% used)
  - zedpool (ZFS): 1.88 TB (30% used)
- **CPU Load:** 3.10%
- **Memory Usage:** 17.56 GiB / 46.88 GiB
- **Note:** Highest resource utilization - best candidate for primary host

### 3. bricky (10.16.1.30)
- **Hardware:** 12 cores, 14.99 GiB RAM
- **Storage:**
  - zedpool (ZFS): 1.81 TB (50% used)
- **CPU Load:** 0.25%
- **Memory Usage:** 1.76 GiB / 14.99 GiB
- **Note:** Lowest RAM - mostly stopped VMs/templates

---

## Shared Storage Resources

- **prox-backup-srv (PBS):** 2 TB (15% used) - Proxmox Backup Server
- **proxmoxbackups (NFS):** 8.84 TB (16% used) - Network backup storage

---

## Virtual Machines Inventory

### pve-itchy (10.16.1.8) - 2 VMs Running

#### VM 112: deb-srv-plex
- **Status:** Running
- **Resources:** 4 cores, 2 GB RAM, 64 GB disk
- **IP:** 10.16.1.18
- **Purpose:** Plex Media Server
- **Special:** GPU passthrough (Intel GVT-g)
- **Boot:** Autostart enabled

#### VM 115: truenas-scale-DR
- **Status:** Running
- **Resources:** 4 cores, 8 GB RAM, 32 GB boot disk
- **IP:** 10.16.1.20
- **Purpose:** TrueNAS Scale Disaster Recovery
- **Storage:** 3x 8TB HGST drives (passthrough)
- **Boot:** Autostart enabled

---

### pve-scratchy (10.16.1.22) - 5 VMs Running, 1 Stopped

#### VM 100: dockc
- **Status:** Running
- **Resources:** 4 cores, 6 GB RAM, 92 GB disk
- **IP:** 10.16.1.4 (primary), 10.16.1.50 (secondary)
- **Storage:** ZFS (zedpool)
- **Purpose:** Primary Docker host
- **Boot:** Autostart enabled

**Docker Containers (24):**
1. sonarr - TV show management
2. traefik - Reverse proxy
3. uptime-kuma - Uptime monitoring
4. cloudflared-tunnel - Cloudflare tunnel
5. transmission - BitTorrent client
6. telegraf - Metrics collection
7. unpoller - UniFi metrics
8. grafana - Monitoring dashboard
9. prometheus - Metrics database
10. influxdb - Time series database
11. promtail - Log aggregator
12. loki - Log aggregation system
13. sabnzbd - Usenet client
14. portainer - Docker management UI
15. homer - Dashboard
16. twingate-opal-python - Zero trust access
17. speedtest-tracker - Internet speed monitoring
18. mariadb - Database for speedtest
19. code-server - VS Code in browser
20. watchtower - Container auto-updater (restarting)
21. dockge - Docker compose manager (exited)
22. homepage - Homepage dashboard
23. pihole - DNS ad blocker
24. nginx-nginx - Web server (exited)

#### VM 102: Anisble-master
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 32 GB disk
- **IP:** 10.16.1.25
- **Storage:** ZFS (zedpool)
- **Purpose:** Ansible automation controller
- **Boot:** Autostart enabled, startup order 2

#### VM 103: zabbix
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 32 GB disk
- **IP:** Unknown (guest agent not responding)
- **Storage:** ZFS (zedpool)
- **Purpose:** Zabbix monitoring system
- **Boot:** Autostart enabled, startup order 5

#### VM 105: haosova-6.6
- **Status:** Stopped
- **Resources:** 2 cores, 4 GB RAM, 32 GB disk
- **Storage:** ZFS (zedpool)
- **Purpose:** Home Assistant OS (VLAN 666)
- **Boot:** UEFI, startup order 4

#### VM 107: deb-util-01
- **Status:** Running
- **Resources:** 2 cores, 4 GB RAM, 32 GB disk
- **IP:** 10.16.1.24
- **Storage:** ZFS (zedpool)
- **Purpose:** General utilities server
- **Boot:** UEFI, autostart enabled

#### VM 109: docka
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 100 GB disk
- **IP:** 10.16.1.12
- **Storage:** ZFS (zedpool)
- **Purpose:** Secondary Docker host
- **Boot:** Autostart enabled

**Docker Containers (6):**
1. vaultwarden - Password manager
2. pihole - DNS ad blocker
3. cups - Print server with AirPrint
4. openvpn-as - OpenVPN Access Server
5. nexterm - Terminal management
6. portainer - Docker management UI (Enterprise)

#### VM 110: truenas-scale
- **Status:** Running
- **Resources:** 4 cores, 8 GB RAM, 32 GB boot disk
- **IP:** 10.16.1.6
- **Purpose:** Primary TrueNAS Scale storage
- **Storage:** 3x 8TB HGST drives (passthrough)
- **Boot:** Autostart enabled, startup order 1 (boots first)
- **Network:** Also has Tailscale (100.74.119.102)

---

### bricky (10.16.1.30) - All Stopped/Templates

#### VM 114: deb-template
- **Status:** Stopped
- **Resources:** 2 GB RAM, 64 GB disk
- **Purpose:** Template

#### VM 116: winblows
- **Status:** Stopped
- **Resources:** 8 GB RAM, 64 GB disk
- **Purpose:** Windows VM

#### VM 117: k3s-single-1
- **Status:** Stopped
- **Resources:** 2 GB RAM, 64 GB disk
- **Purpose:** Kubernetes test node

#### VM 118: deb-test
- **Status:** Stopped
- **Resources:** 2 GB RAM, 64 GB disk
- **Purpose:** Testing

#### VM 119: test
- **Status:** Stopped
- **Resources:** 2 GB RAM, 3 GB disk
- **Purpose:** Testing

#### VM 120: tested
- **Status:** Stopped
- **Resources:** 2 GB RAM, 20 GB disk
- **Purpose:** Testing

#### VM 6000: debian12-cloudinit
- **Status:** Stopped
- **Resources:** 2 GB RAM, 20 GB disk
- **Purpose:** Cloud-init template

#### VM 9000: Template-Debian-Bookworm
- **Status:** Stopped
- **Resources:** 2 GB RAM, 3 GB disk
- **Purpose:** Debian template

---

## LXC Containers Inventory

### pve-itchy (10.16.1.8) - 2 Containers Running

#### CT 113: proxmox-datacenter-manager
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 10 GB disk
- **IP:** 10.16.1.28
- **Purpose:** Proxmox datacenter management
- **Features:** Privileged, nesting, USB passthrough
- **Boot:** Autostart enabled

#### CT 129: crafty-s
- **Status:** Running
- **Resources:** 4 cores, 8 GB RAM, 16 GB disk
- **IP:** 10.16.1.29
- **Purpose:** Crafty Controller (Minecraft server management)
- **Features:** Unprivileged, nesting
- **Boot:** Autostart enabled

---

### pve-scratchy (10.16.1.22) - 6 Containers Running

#### CT 101: watchyourlan
- **Status:** Running
- **Resources:** 1 core, 512 MB RAM, 2 GB disk
- **IP:** 10.16.1.104 (DHCP)
- **Purpose:** LAN device monitoring
- **Features:** Unprivileged, nesting
- **Boot:** Autostart enabled

#### CT 104: wikijs
- **Status:** Running
- **Resources:** 1 core, 512 MB RAM, 6 GB disk
- **IP:** 10.16.1.27
- **Purpose:** Wiki.js documentation platform
- **Features:** Unprivileged, nesting
- **Boot:** Autostart enabled

#### CT 106: docker00
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 8 GB disk
- **IP:** 10.16.1.40
- **Purpose:** Docker host for IoT/automation
- **Features:** Privileged, nesting, USB/serial passthrough
- **Boot:** Autostart enabled

**Docker Containers (3):**
1. cloudflared-tunnel - Cloudflare tunnel
2. uptime-kuma - Uptime monitoring
3. portainer - Docker management

#### CT 108: plexpunnisher
- **Status:** Running
- **Resources:** 4 cores, 4 GB RAM, 64 GB disk (ZFS)
- **IP:** 10.16.1.36
- **Purpose:** Plex management/automation
- **OS:** Ubuntu
- **Features:** Privileged, nesting, GPU passthrough, USB/serial passthrough
- **Boot:** Autostart enabled

#### CT 900: proxbackupsrv
- **Status:** Running
- **Resources:** 2 cores, 2 GB RAM, 20 GB disk (ZFS)
- **IP:** 10.16.1.41
- **Purpose:** Proxmox Backup Server
- **Features:** Privileged, nesting, USB/serial passthrough
- **Boot:** Autostart enabled

#### CT 901: tailscaler
- **Status:** Running
- **Resources:** 1 core, 512 MB RAM, 8 GB disk (ZFS)
- **IP:** 10.16.1.31 (LAN), 100.83.115.87 (Tailscale)
- **Purpose:** Tailscale exit node/subnet router
- **Features:** Privileged, nesting, TUN device passthrough
- **Boot:** Autostart enabled
- **Tag:** networking

---

## Network Configuration

### IP Address Allocation

| IP | Hostname | Type | Node | Purpose |
|---|---|---|---|---|
| 10.16.1.4 | dockc | VM | pve-scratchy | Primary Docker host |
| 10.16.1.6 | truenas-scale | VM | pve-scratchy | Primary TrueNAS |
| 10.16.1.8 | pve-itchy | Host | - | Proxmox node |
| 10.16.1.12 | docka | VM | pve-scratchy | Secondary Docker host |
| 10.16.1.18 | deb-srv-plex | VM | pve-itchy | Plex server |
| 10.16.1.20 | truenas-scale-DR | VM | pve-itchy | TrueNAS DR |
| 10.16.1.22 | pve-scratchy | Host | - | Proxmox node |
| 10.16.1.24 | deb-util-01 | VM | pve-scratchy | Utilities |
| 10.16.1.25 | Anisble-master | VM | pve-scratchy | Ansible controller |
| 10.16.1.27 | wikijs | CT | pve-scratchy | Wiki platform |
| 10.16.1.28 | proxmox-datacenter-manager | CT | pve-itchy | Datacenter mgmt |
| 10.16.1.29 | crafty-s | CT | pve-itchy | Minecraft servers |
| 10.16.1.30 | bricky | Host | - | Proxmox node |
| 10.16.1.31 | tailscaler | CT | pve-scratchy | VPN router |
| 10.16.1.36 | plexpunnisher | CT | pve-scratchy | Plex automation |
| 10.16.1.40 | docker00 | CT | pve-scratchy | Docker/IoT |
| 10.16.1.41 | proxbackupsrv | CT | pve-scratchy | Backup server |
| 10.16.1.50 | dockc (secondary) | VM | pve-scratchy | DNS server |
| 10.16.1.104 | watchyourlan | CT | pve-scratchy | LAN monitor |

### Key Services by IP

- **DNS Servers:** 10.16.1.50 (pihole on dockc), 10.16.1.4, 10.16.1.12 (pihole on docka)
- **Backup Services:** 10.16.1.41 (Proxmox Backup Server)
- **Storage:** 10.16.1.6 (TrueNAS), 10.16.1.20 (TrueNAS DR)
- **VPN/Remote Access:** 10.16.1.31 (Tailscale), 10.16.1.12 (OpenVPN)
- **Monitoring:** 10.16.1.4 (Grafana/Prometheus/Loki)

---

## Resource Summary by Node

### Total Allocated Resources (Running Only)

#### pve-itchy
- **VMs:** 2 running (8 cores, 10 GB RAM allocated)
- **Containers:** 2 running (6 cores, 10 GB RAM allocated)
- **Total:** 14 cores, 20 GB RAM allocated
- **Available:** 8 cores, 31 GB RAM
- **Overcommit Ratio:** 1.75x cores

#### pve-scratchy
- **VMs:** 5 running (16 cores, 22 GB RAM allocated)
- **Containers:** 6 running (11 cores, 9.5 GB RAM allocated)
- **Total:** 27 cores, 31.5 GB RAM allocated
- **Available:** 12 cores, 47 GB RAM
- **Overcommit Ratio:** 2.25x cores

#### bricky
- **VMs:** 0 running
- **Containers:** 0 running
- **Usage:** Templates and stopped test VMs only

---

## Storage Utilization

### Active Storage by Type

1. **ZFS Pools:**
   - zedpool @ pve-scratchy: 1.88 TB (30% used = 558 GB)
   - zedpool @ bricky: 1.81 TB (50% used = 897 GB)

2. **LVM:**
   - itchy-lvm-2 @ pve-itchy: 976 GB (13% used = 128 GB)
   - scratch-pve @ pve-scratchy: 976 GB (16% used = 159 GB)

3. **Backup Storage:**
   - prox-backup-srv: 2 TB (15% used)
   - proxmoxbackups (NFS): 8.84 TB (16% used)

4. **Passthrough Disks:**
   - 6x 8TB HGST drives (3 per TrueNAS instance)

---

## Key Dependencies & Startup Order

### Critical Path (pve-scratchy)
1. **VM 110 (truenas-scale)** - startup order 1 - boots first
2. **VM 102 (Anisble-master)** - startup order 2
3. **VM 105 (haosova)** - startup order 4 (currently stopped)
4. **VM 103 (zabbix)** - startup order 5

### Critical Services
- **DNS:** pihole containers on VMs 100 & 109 - must start before other services
- **Storage:** TrueNAS VMs provide network storage for some services
- **VPN:** Tailscale (CT 901) for remote access
- **Monitoring:** Grafana stack on VM 100 monitors all infrastructure
- **Backup:** PBS (CT 900) backs up all VMs/containers

---

## Special Hardware Requirements

### GPU Passthrough
- **VM 112 (plex):** Intel GVT-g virtual GPU
- **CT 108 (plexpunnisher):** DRI/render device passthrough

### USB/Serial Devices
- Multiple containers configured for USB/serial passthrough:
  - CT 106 (docker00)
  - CT 108 (plexpunnisher)
  - CT 113 (proxmox-datacenter-manager)
  - CT 900 (proxbackupsrv)

### Raw Disk Passthrough
- **VM 110 & 115:** 6 total 8TB HGST drives

---

## Migration Recommendations

### Primary Host Candidate: pve-scratchy
**Reasons:**
1. Most RAM (46.88 GB) - sufficient for all workloads
2. Most cores (12)
3. Already hosts majority of running VMs (5 of 7)
4. Has both ZFS and LVM storage
5. Currently handling highest load without issues

### Standby Host Candidate: pve-itchy
**Reasons:**
1. Adequate resources (8 cores, 31 GB RAM)
2. Has dedicated LVM storage
3. Currently underutilized
4. Can replicate from pve-scratchy

### Decommission Candidate: bricky
**Reasons:**
1. Only 15 GB RAM (insufficient for failover)
2. No running production workloads
3. Only contains templates and stopped test VMs
4. ZFS pool can be moved or recreated

---

## Critical Services Analysis

### Must Keep Running
1. **DNS (pihole)** - Multiple instances for redundancy
2. **TrueNAS** - Network storage
3. **Proxmox Backup Server** - Critical for backups
4. **Tailscale** - Remote access
5. **Monitoring stack** - Grafana/Prometheus/Loki
6. **Portainer** - Docker management across hosts

### Can Have Brief Downtime
1. Media services (Plex, Sonarr, Transmission)
2. Wikijs
3. Minecraft servers
4. Test/development VMs
5. Ansible controller

### Optional/Test Systems
1. Home Assistant (currently stopped)
2. Zabbix (if replacing with Grafana)
3. All VMs on bricky

---

## Migration Strategy Phases

### Phase 1: Preparation
1. Document all Docker compose files and volumes
2. Ensure Proxmox Backup Server has recent backups
3. Test restore process
4. Document network dependencies
5. Create migration runbook

### Phase 2: Storage Consolidation
1. Migrate VMs from itchy to scratchy
2. Consolidate to ZFS pool on scratchy
3. Replicate critical data to external backup

### Phase 3: Service Migration
1. Move Docker containers to LXC on primary host
2. Consolidate multiple Docker hosts into organized LXC structure
3. Update DNS records and service discovery

### Phase 4: Replication Setup
1. Configure PBS replication from primary to standby
2. Set up automated snapshot schedule
3. Create startup/shutdown automation
4. Test failover procedures

### Phase 5: Decommission
1. Power down bricky after confirming templates moved
2. Repurpose hardware if needed
3. Update documentation

---

## Estimated Resource Requirements for Consolidated Host

### Minimum Specifications
- **CPU:** 12+ cores (accounting for 2.5x overcommit)
- **RAM:** 48 GB (current usage + 20% headroom)
- **Storage:**
  - 2 TB ZFS pool for VMs/containers
  - 1 TB LVM for flexible storage
  - Backup to PBS and NFS
- **Network:** 1-2 Gbps for storage traffic

### pve-scratchy Current Specs
- **CPU:** 12 cores ✓
- **RAM:** 46.88 GB ✓ (slightly under, but acceptable)
- **Storage:** ✓ Has both ZFS and LVM
- **Recommendation:** Add 16-32 GB RAM if possible for comfortable headroom

---

## Risk Assessment

### High Risk Items
1. **TrueNAS with passthrough disks** - Requires careful drive mapping during migration
2. **GPU passthrough** - May need reconfiguration on different host
3. **Network dependencies** - Many services rely on specific IPs
4. **USB/serial devices** - Physical hardware dependencies

### Medium Risk Items
1. **Docker volume migration** - Data integrity during moves
2. **Startup order dependencies** - Services expecting specific boot sequence
3. **ZFS pool migration** - Requires proper export/import

### Low Risk Items
1. **LXC containers** - Easy backup/restore
2. **Templates and test VMs** - Non-critical
3. **Standard VMs without special hardware** - Straightforward migration

---

## Next Steps

1. Verify backup status of all VMs/containers
2. Test restore of critical services
3. Create detailed migration runbook with rollback procedures
4. Schedule maintenance window
5. Begin with low-risk migrations (templates, test VMs)
6. Progressively migrate services by criticality
7. Set up replication and automated power management
8. Validate monitoring and alerting on new configuration

---

## Notes

- All systems are backed up to off-site storage
- Proxmox cluster can be broken without data loss
- Most services use Docker, making them portable
- Network is 10.16.1.0/24 with gateway at 10.16.1.1
- DNS managed by pihole instances
- Remote access via Tailscale and OpenVPN
- MTU is 9000 on some interfaces (jumbo frames enabled)
