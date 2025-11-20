# Homelab Consolidation - Planning Prompt for Claude Desktop

## Project Context

I have a 3-node Proxmox homelab that needs to be consolidated down to:
1. **One primary host** running all workloads
2. **One standby host** that receives scheduled replication and powers down after sync

## Current Infrastructure Summary

### Proxmox Nodes
- **pve-scratchy** (10.16.1.22): 12 cores, 47 GB RAM, ZFS (1.88TB) + LVM (976GB)
- **pve-itchy** (10.16.1.8): 8 cores, 31 GB RAM, LVM (976GB)
- **bricky** (10.16.1.30): 12 cores, 15 GB RAM, ZFS (1.81TB) - mostly templates/stopped VMs

### Current Workloads
- 7 running VMs (8 stopped/templates)
- 8 running LXC containers
- 40+ Docker containers across 3 hosts (VMs 100, 109, and CT 106)

### Critical Services
- **DNS:** Multiple pihole instances (VMs 100, 109)
- **Storage:** 2x TrueNAS Scale with 6x 8TB passthrough drives
- **Monitoring:** Grafana/Prometheus/Loki stack on VM 100
- **VPN:** Tailscale (CT 901), OpenVPN (VM 109)
- **Backup:** Proxmox Backup Server (CT 900)
- **Media:** Plex (VM 112 with GPU passthrough), Sonarr, Transmission
- **Management:** Portainer instances, Ansible (VM 102)

### Special Hardware Requirements
- GPU passthrough (VM 112 - Intel GVT-g)
- USB/serial passthrough (multiple containers)
- Raw disk passthrough (6x 8TB HGST drives for TrueNAS)

### Network Configuration
- Network: 10.16.1.0/24
- Gateway: 10.16.1.1
- DNS: 10.16.1.50, 10.16.1.4
- Multiple services with static IPs documented in HOMELAB_DISCOVERY.md

## Preliminary Recommendation

**Primary:** pve-scratchy (has most resources and already hosts majority of workloads)
**Standby:** pve-itchy (adequate for failover)
**Decommission:** bricky (insufficient RAM for failover role)

## What I Need Help Planning

1. **Migration Strategy**
   - Detailed step-by-step migration plan
   - Order of operations to minimize downtime
   - How to handle services with special hardware (GPU, USB, passthrough disks)
   - Testing checkpoints along the way

2. **Replication Architecture**
   - Should we use Proxmox Backup Server replication?
   - ZFS send/receive replication?
   - Storage replication strategy for both primary and standby
   - How to handle TrueNAS with passthrough disks in a replication scenario

3. **Automation & Scheduling**
   - Automated replication schedule (daily? weekly?)
   - Standby host power management (shutdown after sync, wake before sync)
   - Wake-on-LAN setup for standby host
   - Health checks and alerting
   - Failover procedures

4. **Risk Mitigation**
   - Rollback procedures for each migration phase
   - Testing plan for critical services
   - Network reconfiguration strategy (many services have static IPs)
   - How to maintain service availability during migration

5. **Data Integrity**
   - Docker volume migration strategy
   - Database backup/restore procedures (MariaDB, InfluxDB, etc.)
   - Configuration backup strategy

6. **Edge Cases**
   - How to replicate VMs with passthrough hardware
   - GPU passthrough on standby node (should it be configured but inactive?)
   - Handling the two TrueNAS instances (primary + DR)
   - Network service dependencies (DNS, VPN during migration)

## Constraints & Preferences

- Everything is backed up offsite - we can "rip and tear"
- Prefer minimal downtime for critical services (DNS, VPN, storage)
- Media services can have extended downtime
- All credentials use same password: `Getmassiv3` (root and user `dp`)
- Want automated replication + shutdown to save power
- Need reliable failover capability

## Reference Documents

Full discovery report available at: `/Users/dp/developerland/homelab/HOMELAB_DISCOVERY.md`

This includes:
- Complete VM/CT/Docker inventory
- Resource utilization details
- Network mapping with all IPs
- Storage breakdown
- Startup dependencies
- Risk assessment

## Desired Outcome

A detailed, phased migration plan with:
- Step-by-step procedures for each phase
- Shell scripts/commands where applicable
- Testing/validation steps
- Rollback procedures
- Replication setup and automation scripts
- Final state architecture diagram/description

## Questions to Consider

1. Should we keep both TrueNAS instances or consolidate?
2. How to handle the Docker sprawl across 3 hosts?
3. Should standby host be powered on 24/7 or wake-on-schedule?
4. Replication frequency (RPO/RTO requirements)?
5. Do we need to maintain cluster or break it?
6. How to handle hardware-dependent services in standby scenario?

---

**Note:** I'm comfortable with Linux, Proxmox, Docker, and can execute commands. I'm looking for a well-thought-out strategy before we start executing changes.
