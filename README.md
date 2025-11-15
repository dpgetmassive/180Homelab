# HomeLab Legacy - Proxmox Consolidation Project

**Status:** Phase 7 Complete ✅
**Date:** November 2025
**Goal:** Consolidate 3-node Proxmox cluster to 1 primary + 1 standby with automated backups

---

## Project Overview

This repository documents the complete consolidation of a 3-node Proxmox homelab cluster into an efficient 2-node setup with automated backup strategies and power management.

### Original Infrastructure

- **3 Proxmox nodes:** pve-itchy, pve-scratchy, bricky
- **15 VMs** across nodes
- **8 LXC containers**
- **40+ Docker containers**
- **Power consumption:** ~600W continuous
- **Monthly cost:** ~$135/month

### Final Architecture

- **1 Primary:** pve-scratchy (12 cores, 47 GB RAM) - runs 24/7
- **1 Standby:** pve-itchy (8 cores, 31 GB RAM) - wakes daily for backups
- **All workloads:** Consolidated to primary
- **Power consumption:** ~250W (95% reduction on standby)
- **Monthly cost:** ~$62/month (~$73/month savings)

---

## Documentation Files

### Phase Completion Reports

1. **[HOMELAB_DISCOVERY.md](HOMELAB_DISCOVERY.md)** - Initial infrastructure discovery
2. **[BRICKY_CLEANUP_COMPLETE.md](BRICKY_CLEANUP_COMPLETE.md)** - Node decommissioning
3. **[MIGRATION_COMPLETE.md](MIGRATION_COMPLETE.md)** - Phases 1-5: VM/CT migrations
4. **[PHASE6_REPLICATION_COMPLETE.md](PHASE6_REPLICATION_COMPLETE.md)** - PBS backup setup
5. **[PHASE7_AUTOMATION_COMPLETE.md](PHASE7_AUTOMATION_COMPLETE.md)** - WOL automation
6. **[INTEGRATED_BACKUP_SYSTEM.md](INTEGRATED_BACKUP_SYSTEM.md)** - Complete backup strategy

### Analysis & Planning

- **[CONSOLIDATED_ARCHITECTURE_PLAN.md](CONSOLIDATED_ARCHITECTURE_PLAN.md)** - Original migration plan
- **[TRUENAS_REPLICATION_ANALYSIS.md](TRUENAS_REPLICATION_ANALYSIS.md)** - ZFS replication assessment
- **[CLAUDE_CODE_MEMORY.md](CLAUDE_CODE_MEMORY.md)** - Session context and continuity

### Service Optimization (Nov 2025)

- **[SONARR_OPTIMIZATION.md](SONARR_OPTIMIZATION.md)** - Quality limits and size optimization
- **[DOCKER_UPDATES_2025-11-15.md](DOCKER_UPDATES_2025-11-15.md)** - Container updates and Watchtower fix

---

## Key Features Implemented

### ✅ Automated Backup System

**Triple Backup Strategy:**
1. **ZFS Replication** - 923 GB FileServer data (TrueNAS primary → DR)
2. **Proxmox Backups** - All VMs/CTs to standby host (232 GB NVMe)
3. **PBS Deduplication** - Central backup repository with compression

**Daily Schedule:**
```
02:00 AM - Wake standby via WOL
02:10 AM - ZFS replication (FileServer: 923 GB)
02:46 AM - Proxmox backups (All VMs/CTs)
03:23 AM - Shutdown standby
06:00 AM - Email status alerts
```

### ✅ Wake-on-LAN Power Management

- Standby host powered on ~80 minutes/day
- Automatic startup and shutdown
- 95% power reduction on standby
- Annual savings: ~$875

### ✅ Comprehensive Monitoring

- Email alerts for backup failures
- ZFS replication status monitoring
- Automated health checks
- Detailed logging

### ✅ Disaster Recovery

**Recovery capabilities:**
- **FileServer:** Instant failover via ZFS replication
- **VMs/CTs:** Restore from multiple backup copies
- **RPO:** 24 hours (daily backup cycle)
- **RTO:** Minutes to hours depending on workload

---

## Project Timeline

**Total Duration:** ~8 hours across multiple sessions

- **Phase 1-2:** Discovery and planning (1 hour)
- **Phase 3:** Bricky decommissioning (30 minutes)
- **Phase 4-5:** VM/CT migrations (2 hours)
- **Phase 6:** PBS backup configuration (1 hour)
- **Phase 7:** WOL automation + ZFS integration (3 hours)

---

## Technologies Used

- **Proxmox VE** 8.x - Virtualization platform
- **TrueNAS Scale** - ZFS storage and NFS exports
- **Proxmox Backup Server** - Deduplication and compression
- **ZFS** - Block-level replication and snapshots
- **Wake-on-LAN** - Power management
- **Linux shell scripts** - Automation
- **Cron** - Scheduling
- **SSH** - Remote management

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────┐
│  USW Enterprise 8 PoE Switch (10GbE)                    │
└──────────────┬────────────────────────┬─────────────────┘
               │                        │
       ┌───────▼──────────┐    ┌───────▼──────────┐
       │  pve-scratchy    │    │   pve-itchy      │
       │  (PRIMARY)       │    │   (STANDBY)      │
       │  10.16.1.22      │    │   10.16.1.8      │
       │  12c / 47GB      │    │   8c / 31GB      │
       │                  │    │                  │
       │  7 VMs           │    │   1 VM (DR)      │
       │  8 Containers    │    │   Backup target  │
       │  24/7 operation  │    │   80 min/day     │
       └──────────────────┘    └──────────────────┘
```

---

## Key Workloads

### Running on pve-scratchy (Primary)

**VMs:**
- VM 100: dockc (Docker host) - 92 GB
- VM 102: Ansible-master - 32 GB
- VM 103: Zabbix monitoring - 32 GB
- VM 107: deb-util-01 - 32 GB
- VM 109: docka (Docker host) - 100 GB
- VM 110: TrueNAS primary - 32 GB + 3x 8TB
- VM 112: Plex server - 64 GB (with GPU passthrough)

**Containers:**
- CT 101: watchyourlan - 2 GB
- CT 104: WikiJS - 6 GB
- CT 106: docker00 (IoT) - 8 GB
- CT 108: plexpunnisher - 64 GB
- CT 113: proxmox-datacenter-manager - 10 GB
- CT 129: crafty-s (Minecraft) - 16 GB
- CT 900: Proxmox Backup Server - 20 GB
- CT 901: Tailscale VPN - 8 GB

### Running on pve-itchy (Standby)

- VM 115: TrueNAS DR - 32 GB + 3x 8TB (runs during backup window only)

---

## Lessons Learned

### Technical Challenges

1. **LVM → ZFS migrations not supported** - Had to use same storage type
2. **GPU passthrough blocks live migration** - Must remove/re-add
3. **SFP+ NICs don't support WOL** - Used onboard Ethernet instead
4. **Native replication requires ZFS** - PBS backup was better solution for LVM
5. **TrueNAS DR dependency** - Required careful planning for power-down automation

### Best Practices

1. **Plan storage types carefully** - Migration constraints
2. **Test backups early and often** - Validation is critical
3. **Document as you go** - Detailed logs saved time
4. **Use scripts for automation** - Cron + shell = reliable
5. **Monitor everything** - Email alerts catch issues early

### What Worked Well

- ✅ Comprehensive discovery phase
- ✅ Phased migration approach
- ✅ Testing each component before integration
- ✅ Detailed documentation at each phase
- ✅ Triple backup strategy for redundancy

---

## Future Enhancements

### Potential Improvements

1. **Convert itchy-backups to ZFS** - Better compression and snapshots
2. **Fix Downloads replication** - Reset destination and resync
3. **Add Grafana dashboard** - Visualize backup metrics and trends
4. **Offsite backup integration** - Cloud sync or external drive rotation
5. **Automated testing** - Periodic restore verification
6. **Disaster recovery drills** - Quarterly failover testing

### Monitoring Enhancements

- Backup duration trending
- Storage usage projections
- Success/failure rate tracking
- Integration with existing Zabbix/Grafana stack

---

## Scripts & Automation

### Main Automation Script

**Location:** `/usr/local/bin/wake-backup-shutdown-v2.sh`
**Schedule:** Daily at 2:00 AM
**Function:**
- Send WOL packet to standby
- Wait for boot
- Start TrueNAS DR VM
- Monitor ZFS replication
- Run Proxmox backups
- Graceful shutdown sequence

### Monitoring Script

**Location:** `/usr/local/bin/check-backup-status-v2.sh`
**Schedule:** Daily at 6:00 AM
**Function:**
- Verify backup cycle completion
- Check ZFS replication status
- Detect errors and warnings
- Send email alerts if issues found

---

## Cost Analysis

### Power Consumption

**Before consolidation:**
- pve-itchy: 24/7 @ 200W = 4.8 kWh/day
- pve-scratchy: 24/7 @ 250W = 6.0 kWh/day
- bricky: 24/7 @ 150W = 3.6 kWh/day
- **Total: 14.4 kWh/day**

**After consolidation:**
- pve-scratchy: 24/7 @ 250W = 6.0 kWh/day
- pve-itchy: 80 min/day @ 200W = 0.27 kWh/day
- **Total: 6.27 kWh/day**

**Savings:**
- Daily: 8.13 kWh (56% reduction)
- Monthly: 244 kWh
- Annual: 2,967 kWh
- **Cost savings: ~$875/year @ $0.25/kWh**

---

## Support & Maintenance

### Manual Operations

**View backup logs:**
```bash
tail -f /var/log/wake-backup-shutdown.log
```

**Check ZFS replication:**
```bash
ssh root@10.16.1.6 "midclt call replication.query | jq '.[0].state'"
```

**Test WOL manually:**
```bash
wakeonlan 60:45:cb:69:85:83
```

**Force backup run:**
```bash
/usr/local/bin/wake-backup-shutdown-v2.sh
```

### Emergency Procedures

See [INTEGRATED_BACKUP_SYSTEM.md](INTEGRATED_BACKUP_SYSTEM.md) for detailed recovery procedures including:
- Primary TrueNAS failure (ZFS failover)
- Complete host failure (restore from backups)
- Disaster recovery scenarios

---

## Credits

**Project Lead:** dp @ GetMassive
**Implementation:** Claude Code (Anthropic)
**Hardware:** Custom Proxmox cluster
**Timeline:** November 2025

---

## License

Documentation is provided as-is for reference and learning purposes.

---

**Project Status:** ✅ Complete and operational
**Last Updated:** 2025-11-15
**Next Review:** 2025-12-15 (30-day validation)
