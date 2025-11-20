# 180 Homelab Infrastructure

Production homelab infrastructure documentation for Get Massive Dojo training environment.

## Overview

This repository contains comprehensive documentation for the 180 Homelab infrastructure, including:

- **Proxmox Cluster**: 2-node cluster (pve-scratchy + pve-itchy)
- **TrueNAS Storage**: Primary and DR instances with ZFS replication
- **Backup System**: Automated VM/CT backups with offsite redundancy
- **Monitoring**: Real-time cluster health and resource tracking

## Quick Access

### Infrastructure Components

- **pve-scratchy** (10.16.1.22) - Primary Proxmox host: 12 cores, 48GB RAM
- **pve-itchy** (10.16.1.8) - Backup Proxmox host: 8 cores, 32GB RAM
- **TrueNAS Primary** (10.16.1.6) - VM 110: Main file server (923GB datasets)
- **TrueNAS DR** (10.16.1.20) - VM 115: Disaster recovery target

### Key Services

- **Monitoring Dashboard**: http://localhost:81
- **ntfy Notifications**: https://ntfy.sh/gmdojo-monitoring
- **Healthchecks**: https://hc-ping.com/94a543b5-6322-40e5-9648-cb2d534f3567

## Documentation

### [Backup System](./backups/README.md)

Comprehensive backup and disaster recovery documentation:

- **Daily Automated Backups**: 2:00 AM orchestration
- **ZFS Replication**: Block-level replication (923GB FileServer dataset)
- **VM/CT Backups**: vzdump with zstd compression
- **Offsite Protection**: Backblaze B2 CloudSync for critical data
- **TrueNAS Configs**: Daily database exports

**Key Files**:
- [Backup System Overview](./backups/README.md)
- [Orchestration Script Details](./backups/proxmox-backup-orchestration.md)

### [Monitoring System](./monitoring/README.md)

Real-time monitoring dashboard and alerting:

- **Flask Dashboard**: Web-based cluster monitoring (port 81)
- **Resource Tracking**: CPU, memory, storage with configurable thresholds
- **Top CPU Consumer**: Identifies VMs/CTs consuming most resources
- **ntfy Integration**: Push notifications for alerts
- **ZFS Replication Status**: Monitor replication health

**Key Files**:
- [Monitoring System Overview](./monitoring/README.md)
- [proxmox_status.py](./monitoring/proxmox_status.py) - Main Flask application

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                180 Homelab Architecture                      │
└─────────────────────────────────────────────────────────────┘

Primary Site (pve-scratchy - 10.16.1.22):
├─ VM 110: TrueNAS Primary (10.16.1.6)
│  └─> 923GB FileServer dataset
│      └─> ZFS Replication → TrueNAS DR (daily 2:10 AM)
│      └─> Backblaze B2 CloudSync (continuous)
├─ VM 100-109: Production workloads
└─ Containers: Various services

Backup Site (pve-itchy - 10.16.1.8):
├─ VM 115: TrueNAS DR (10.16.1.20)
│  └─> Receives ZFS replication from Primary
├─ NFS Storage: 7.4TB for VM/CT backups
└─ Backup Target: All pve-scratchy VMs/CTs

Monitoring:
├─ Flask Dashboard (port 81)
├─ ntfy.sh push notifications
└─ healthchecks.io heartbeat
```

## Backup Schedule

| Time | Task | Description |
|------|------|-------------|
| 2:00 AM | Orchestration Start | Script begins on pve-scratchy |
| 2:10 AM | ZFS Snapshot | TrueNAS creates FileServer snapshot |
| 2:11 AM | ZFS Replication | 923GB dataset → DR (35-50 min) |
| 2:46 AM | Proxmox Backups | VM/CT vzdump backups begin |
| 2:48 AM | Config Backups | TrueNAS database exports |
| 3:20 AM | Complete | All backups finished |
| 6:00 AM | Status Check | Email notification sent |

## Recovery Time Objectives (RTO)

| Scenario | Recovery Time | Data Loss (RPO) |
|----------|---------------|-----------------|
| FileServer failure | < 10 minutes | < 24 hours |
| Single VM failure | < 30 minutes | < 24 hours |
| pve-scratchy total failure | 2-4 hours | < 24 hours |
| Catastrophic (both hosts) | 1-2 days | < 24 hours |

## Common Operations

### Check Backup Status

```bash
# View latest backup log
ssh root@10.16.1.22 "tail -100 /var/log/proxmox-backup-orchestration.log"

# Check if backups completed today
ssh root@10.16.1.22 "grep 'Backup Cycle Summary' /var/log/proxmox-backup-orchestration.log | tail -1"

# Check storage usage
ssh root@10.16.1.8 "df -h /mnt/pve/pve-bk-truenas-primary"
```

### Manual Backup Execution

```bash
# Run full backup orchestration
ssh root@10.16.1.22 "/usr/local/bin/proxmox-backup-orchestration.sh"

# Backup single VM
vzdump 100 --storage pve-bk-truenas-primary --compress zstd --mode snapshot
```

### Monitor Cluster Health

```bash
# Access monitoring dashboard
open http://localhost:81

# Check Proxmox cluster status
pvecm status

# View VM/CT list
qm list && pct list
```

## Storage Locations

```
pve-itchy (10.16.1.8):
├─ /mnt/pve/pve-bk-truenas-primary/
│  ├─ dump/                          # Proxmox VM/CT backups
│  │  ├─ vzdump-qemu-100-*.vma.zst   # VM backups (zstd compressed)
│  │  └─ vzdump-lxc-101-*.tar.zst    # CT backups
│  └─ truenas-configs/                # TrueNAS config backups
│     ├─ truenas-primary-config-*.db  # Primary configs
│     └─ truenas-dr-config-*.db       # DR configs
│
└─ VM 115 (TrueNAS DR - 10.16.1.20):
   └─ Tank/Data-DR-Copy/FileServer/   # Replicated ZFS dataset
```

## Recent Updates

### 2025-11-20: TrueNAS Config Backup Fix (v2.4)
- Fixed Primary TrueNAS config backup using REST API instead of SSH
- Added `backup_truenas_config_api()` function using curl to `/api/v2.0/config/save`
- SSH method still used for DR TrueNAS where it's configured
- Primary config backups now successfully captured (796KB SQLite database)

### 2025-11-20: Backup Script Fix (v2.3)
- Fixed storage verification logic (SSH remote → local check)
- Corrected NFS mount configuration
- Successfully tested with 19 VMs/CTs

### 2025-11-20: Monitoring Improvements
- Fixed metrics display order
- Added top CPU consumer tracking
- Raised load alert thresholds for backup operations
- Dynamic hardware detection
- Improved ntfy notification parsing

## Pending Tasks

- [ ] Add Backblaze CloudSync job status to monitoring dashboard
- [ ] Implement "Last Successful Backup" timestamp with 24-hour alert
- [ ] Add Grafana integration for historical metrics

## Archive

Legacy documentation from previous infrastructure iterations has been moved to:
- [zzz_archive/](./zzz_archive/) - Historical migration docs, old planning documents

This archive is static and preserved for reference only.

## Support and Contact

**Maintainer**: Get Massive Dojo Infrastructure Team
**Repository**: https://github.com/dpgetmassive/180Homelab
**Issues**: https://github.com/dpgetmassive/180Homelab/issues

For backup system issues:
1. Check logs at `/var/log/proxmox-backup-orchestration.log`
2. Verify storage availability
3. Review troubleshooting sections in documentation

For monitoring issues:
1. Check Flask app is running: `lsof -ti:81`
2. Verify SSH connectivity
3. Review browser console for errors

---

**Last Updated**: 2025-11-20
**Infrastructure Status**: Active - 2 hosts, 19 VMs/CTs
