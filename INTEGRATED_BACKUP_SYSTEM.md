# Integrated Backup System: ZFS Replication + Proxmox Backups

**Date:** 2025-11-15
**Version:** 2.0
**Status:** Fully Configured ✅

---

## Overview

Successfully integrated TrueNAS ZFS replication with Proxmox backup automation in a single coordinated WOL window. Both backup strategies now run together, maximizing efficiency and maintaining comprehensive data protection.

---

## Daily Automated Schedule

### Timeline

```
02:00 AM - Wake pve-itchy
├─ WOL packet sent to MAC: 60:45:cb:69:85:83
├─ Wait for boot (~3 minutes)
└─ pve-itchy online

02:05 AM - Start VM 115 (TrueNAS DR)
├─ qm start 115
├─ Wait for VM boot (~90 seconds)
└─ Wait for SSH availability

02:08 AM - TrueNAS DR ready
└─ Both TrueNAS servers online

02:10 AM - TrueNAS snapshot created (automatic)
├─ Snapshot: Tank/FileServer@auto-2025-11-15_02-10
└─ Triggers ZFS replication automatically

02:11 AM - ZFS replication starts
├─ Source: Tank/FileServer (10.16.1.6)
├─ Destination: Tank/Data-DR-Copy/FileServer (10.16.1.20)
├─ Method: Incremental send/receive
├─ Size: 923 GB (only changed blocks transferred)
└─ Estimated duration: 35-50 minutes

02:45 AM - ZFS replication completes
├─ Script monitors for completion
└─ Logs status (success/error/timeout)

02:46 AM - Proxmox backups start
├─ Source: All VMs/CTs on pve-scratchy
├─ Destination: itchy-backups (232 GB on NVMe)
├─ Excludes: VM 115 (TrueNAS DR)
└─ Estimated duration: 30-40 minutes

03:20 AM - Proxmox backups complete
└─ All workloads backed up

03:21 AM - Shutdown VM 115
├─ qm shutdown 115
└─ Wait 30s for graceful shutdown

03:22 AM - Shutdown pve-itchy
├─ shutdown -h now
└─ Wait 30s

03:23 AM - All powered down
└─ Cycle complete

06:00 AM - Status check and alerts
├─ Verify backup cycle completed
├─ Check ZFS replication state
├─ Email alert if any issues
└─ Email: dp@getmassive.com.au
```

### Resource Usage

**pve-itchy uptime:** ~80 minutes/day (5.5%)
**VM 115 uptime:** ~75 minutes/day
**Power savings:** ~94-95% compared to 24/7 operation

---

## What Gets Backed Up

### Method 1: ZFS Replication (Large Datasets)

**FileServer (923 GB):**
- **Source:** VM 110 Tank/FileServer
- **Destination:** VM 115 Tank/Data-DR-Copy/FileServer
- **Schedule:** Daily at 2:10 AM
- **Type:** Incremental block-level replication
- **Retention:** 4 weeks of snapshots on source
- **Benefits:**
  - Very fast (only changed blocks)
  - Instant failover capability
  - Point-in-time recovery via snapshots
  - Native ZFS checksums and verification

**Why ZFS for FileServer:**
- 923 GB is too large for frequent Proxmox backups
- Block-level incremental is much more efficient
- Provides better RPO through snapshot retention
- Can mount replicated dataset immediately if primary fails

### Method 2: Proxmox Backups (VMs & Containers)

**All VMs (except VM 115):**
- VM 100: dockc (92 GB)
- VM 102: Ansible-master (32 GB)
- VM 103: zabbix (32 GB)
- VM 107: deb-util-01 (32 GB)
- VM 109: docka (100 GB)
- VM 110: truenas-scale (32 GB) - **includes smaller datasets**
- VM 112: deb-srv-plex (64 GB)

**All Containers:**
- CT 101: watchyourlan (2 GB)
- CT 104: wikijs (6 GB)
- CT 106: docker00 (8 GB)
- CT 108: plexpunnisher (64 GB)
- CT 113: proxmox-datacenter-manager (10 GB)
- CT 129: crafty-s (16 GB)
- CT 900: proxbackupsrv (20 GB)
- CT 901: tailscaler (8 GB)

**Storage:** itchy-backups (232 GB NVMe on pve-itchy)

**Why Proxmox for VMs/CTs:**
- Manageable sizes
- Includes configuration and state
- Easy restore from web UI
- Centralized backup management

### Method 3: PBS Deduplication (Central Repository)

**All Proxmox VMs/CTs also backed up to PBS:**
- **Destination:** prox-backup-srv (CT 900)
- **Storage:** Primary TrueNAS (10.16.1.6)
- **Features:** Deduplication, compression, verification
- **Retention:** Last 3 backups + monthly snapshots

This provides **triple redundancy:**
1. Live data on pve-scratchy
2. Daily backup to pve-itchy
3. Deduplicated backup to PBS

---

## Configuration Details

### TrueNAS Snapshot Schedule

**Task ID:** 7
**Dataset:** Tank/FileServer
**Schedule:** 2:10 AM daily
**Naming:** auto-%Y-%m-%d_%H-%M
**Retention:** 4 weeks

```json
{
  "schedule": {
    "minute": "10",
    "hour": "2",
    "dom": "*",
    "month": "*",
    "dow": "*"
  }
}
```

### TrueNAS Replication Job

**Task ID:** 4
**Name:** FileServer-to-DR
**Type:** PUSH (primary → DR)
**Transport:** SSH
**Auto-run:** Yes (triggers on snapshot creation)
**Retention:** CUSTOM (1 month on destination)

**SSH Credentials:**
- Host: 10.16.1.20 (TrueNAS DR)
- Username: root
- Authentication: SSH key (ID: 1)

### Automation Scripts

**Primary script:** `/usr/local/bin/wake-backup-shutdown-v2.sh`
- Enhanced version 2.0
- Handles WOL, VM startup, replication monitoring, backups, shutdown
- Comprehensive logging to `/var/log/wake-backup-shutdown.log`
- Error handling and timeouts

**Monitoring script:** `/usr/local/bin/check-backup-status-v2.sh`
- Checks both Proxmox backups and ZFS replication
- Monitors for errors, warnings, and timeouts
- Sends email alerts to dp@getmassive.com.au
- Logs to `/var/log/last-backup-check`

### Cron Schedule

```cron
# On pve-scratchy (10.16.1.22)

# Wake pve-itchy, run ZFS replication + Proxmox backups, then shut down
0 2 * * * /usr/local/bin/wake-backup-shutdown-v2.sh

# Check if backup/replication completed successfully
0 6 * * * /usr/local/bin/check-backup-status-v2.sh
```

---

## Monitoring & Alerts

### Email Notifications

**Recipient:** dp@getmassive.com.au
**Frequency:** Daily at 6:00 AM (after backup window)

**Alert Conditions:**
1. ❌ Backup cycle did not complete
2. ⚠️ Backup cycle completed with errors
3. ⚠️ Backup cycle completed with warnings
4. ❌ ZFS replication failed
5. ⚠️ ZFS replication stuck (running > 2 hours)
6. ❌ TrueNAS unreachable
7. ❌ Log file missing

**Silent conditions (no email):**
- ✅ All backups completed successfully
- ✅ ZFS replication finished
- ✅ No errors or warnings

### Manual Monitoring

**Check backup logs:**
```bash
# View today's backup cycle
tail -f /var/log/wake-backup-shutdown.log

# Check last 100 lines
tail -100 /var/log/wake-backup-shutdown.log

# Search for errors
grep ERROR /var/log/wake-backup-shutdown.log
```

**Check ZFS replication status:**
```bash
# On primary TrueNAS
ssh root@10.16.1.6 "midclt call replication.query | jq '.[0].state'"

# Check last snapshot
ssh root@10.16.1.6 "zfs list -t snapshot Tank/FileServer | tail -1"
```

**Check pve-itchy status:**
```bash
# Is it powered on?
ping -c 3 10.16.1.8

# Is VM 115 running?
ssh root@10.16.1.8 "qm status 115"
```

---

## Recovery Procedures

### Scenario 1: Primary TrueNAS Failure (VM 110)

**FileServer data lost or corrupted:**

1. **Mount replicated dataset on DR:**
```bash
# On TrueNAS DR (10.16.1.20)
zfs set readonly=off Tank/Data-DR-Copy/FileServer
zfs set mountpoint=/mnt/FileServer-Failover Tank/Data-DR-Copy/FileServer
zfs mount Tank/Data-DR-Copy/FileServer
```

2. **Update NFS exports to point to failover mount**

3. **Update DNS/IPs if needed**

**Recovery Time:** < 10 minutes (instant failover)
**Data Loss:** Maximum 24 hours (since last replication)

### Scenario 2: pve-scratchy Complete Failure

**All VMs/CTs lost:**

1. **Power on pve-itchy**
2. **Restore VMs from itchy-backups:**
```bash
# Restore from most recent backup
qmrestore /mnt/pve/itchy-backups/dump/vzdump-qemu-100-*.vma.zst 100

# Or restore from PBS
proxmox-backup-client restore ...
```

3. **Start essential services first** (DNS, storage, VPN)
4. **Restore remaining workloads**

**Recovery Time:** 2-4 hours for essential services, 6-8 hours for complete
**Data Loss:** Maximum 24 hours

### Scenario 3: Both Hosts Failure

**Catastrophic failure:**

1. **Restore from offsite backups** (user has these)
2. **Or rebuild infrastructure**
3. **PBS backups still on primary TrueNAS** (separate storage)

---

## Performance Expectations

### ZFS Replication

**FileServer (923 GB):**
- **First run:** Full send (~2-3 hours)
- **Daily incremental:** 35-50 minutes
- **Data transferred:** Only changed blocks
- **Compression:** Native ZFS compression
- **Network:** 10GbE between hosts

**Estimated bandwidth:**
- Full: ~80-100 MB/s
- Incremental: Varies based on changes (typically < 10% of dataset)

### Proxmox Backups

**All VMs/CTs (~500 GB total):**
- **First backup:** 60-90 minutes
- **Incremental:** 30-40 minutes (only changed blocks with zstd)
- **Storage:** 232 GB available on itchy-backups
- **Compression:** zstd (3:1 ratio typical)

**Storage growth:**
- Initial: ~150-200 GB (with compression)
- Daily growth: +10-20 GB
- **Recommendation:** Keep last 5-7 days

### Total Window

**Expected:**
- ZFS replication: 35-50 min
- Proxmox backups: 30-40 min
- Overhead: 15-20 min
- **Total: 80-110 minutes**

**Actual will vary based on:**
- Amount of data changed
- Network conditions
- Disk I/O performance
- Number of VMs/CTs

---

## Maintenance Tasks

### Weekly

**Check storage usage:**
```bash
# itchy-backups capacity
ssh root@10.16.1.8 "df -h /mnt/pve/itchy-nvme"

# Oldest backups
ssh root@10.16.1.8 "ls -lth /mnt/pve/itchy-nvme/proxmox-backups/dump/ | tail -10"
```

**Clean old backups if needed:**
```bash
# Delete backups older than 7 days
find /mnt/pve/itchy-nvme/proxmox-backups/dump/ -name "*.vma.zst" -mtime +7 -delete
```

### Monthly

**Verify ZFS replication integrity:**
```bash
# Check snapshot list on both sides
ssh root@10.16.1.6 "zfs list -t snapshot Tank/FileServer | tail -5"
ssh root@10.16.1.20 "zfs list -t snapshot Tank/Data-DR-Copy/FileServer | tail -5"

# Compare sizes
ssh root@10.16.1.6 "zfs list Tank/FileServer"
ssh root@10.16.1.20 "zfs list Tank/Data-DR-Copy/FileServer"
```

**Test restore:**
- Restore one VM from itchy-backups
- Verify it boots and data is intact
- Delete test VM after verification

### Quarterly

**Full disaster recovery test:**
1. Power off pve-scratchy (simulate failure)
2. Boot pve-itchy
3. Mount replicated FileServer dataset
4. Restore critical VMs
5. Verify services operational
6. Document any issues or improvements

---

## Deferred Items

### Downloads Replication (Currently Disabled)

**Status:** ❌ ERROR - snapshot mismatch
**Decision:** Deferred for now
**Alternative:** Rely on Proxmox backups

**If you want to fix it later:**
```bash
# Option 1: Reset destination
ssh root@10.16.1.20 "zfs destroy -r Tank/Data-DR-Copy/Downloads"
# Then let replication recreate it

# Option 2: Find common snapshot
# Identify matching snapshot on both sides and manually sync
```

**Estimated effort:** 30-60 minutes to troubleshoot and fix

---

## Comparison to Original Setup

### Before

**Backup Strategy:**
- TrueNAS replication: 2x daily (1:50 AM, 7:50 PM)
- Proxmox backups: Daily to PBS
- TrueNAS DR: Running 24/7 on pve-itchy
- pve-itchy: Always powered on
- Downloads replication: Broken

**Power Usage:**
- pve-itchy: 24/7 (~200W)
- VM 115: 24/7 (~50W)
- **Total: ~250W continuous = 6 kWh/day**

### After

**Backup Strategy:**
- TrueNAS replication: 1x daily at 2:10 AM (coordinated)
- Proxmox backups: Daily to itchy-backups + PBS
- TrueNAS DR: Runs ~75 min/day
- pve-itchy: Runs ~80 min/day
- Downloads replication: Deferred/disabled

**Power Usage:**
- pve-itchy: ~80 min/day (~200W)
- VM 115: ~75 min/day (~50W)
- **Total: ~0.33 kWh/day**

**Savings:**
- Power: 95% reduction
- Cost: ~$45/month → ~$2.50/month
- **Annual savings: ~$500-600**

---

## Success Criteria

### What "Working" Looks Like

**Daily (automated):**
- ✅ pve-itchy wakes at 2:00 AM
- ✅ VM 115 starts automatically
- ✅ TrueNAS snapshot created at 2:10 AM
- ✅ ZFS replication completes successfully
- ✅ Proxmox backups complete successfully
- ✅ VM 115 shuts down gracefully
- ✅ pve-itchy shuts down gracefully
- ✅ No error emails received at 6:00 AM

**Verification:**
1. Check email at 6 AM - should be none (or success confirmation)
2. Check log file shows "cycle complete"
3. Verify latest snapshot exists on both TrueNAS servers
4. Confirm backups exist in itchy-backups
5. pve-itchy should be offline (ping fails)

---

## Next Steps

### Immediate (Tonight)

**Option 1: Wait for automatic run at 2 AM tomorrow**
- Script will run automatically
- Check email at 6 AM for status
- Review logs in morning

**Option 2: Manual test now**
```bash
# Run the new script manually
ssh root@10.16.1.22 "/usr/local/bin/wake-backup-shutdown-v2.sh"

# Watch logs in real-time
ssh root@10.16.1.22 "tail -f /var/log/wake-backup-shutdown.log"
```

### Short Term (Next Week)

1. Monitor first 3-5 automated runs
2. Tune timeouts if needed
3. Adjust retention if storage fills up
4. Verify email alerts working
5. Test manual failover to TrueNAS DR

### Long Term (Future)

1. **Convert itchy-backups to ZFS** (optional)
   - Better compression
   - Snapshots for backup versioning
   - Data integrity checks

2. **Fix Downloads replication** (if desired)
   - Reset destination dataset
   - Re-establish replication

3. **Add metrics dashboard**
   - Backup duration trends
   - Storage usage over time
   - Success/failure rates
   - Integration with Grafana

4. **Offsite backup integration**
   - Sync critical backups to cloud
   - Or external drive rotation
   - Test restore from offsite

---

## Summary

### ✅ Phase 7 Enhanced: Complete

**Implemented:**
1. ✅ TrueNAS snapshot schedule changed to 2:10 AM
2. ✅ Enhanced WOL script (v2.0) with ZFS replication support
3. ✅ VM 115 startup/shutdown automation
4. ✅ ZFS replication monitoring
5. ✅ Enhanced monitoring script with replication status
6. ✅ Email alerts for both backup types
7. ✅ Coordinated daily schedule
8. ✅ Comprehensive logging

**Active Protection:**
- 🔄 ZFS replication: 923 GB FileServer data
- 💾 Proxmox backups: All VMs/CTs to pve-itchy
- 🔐 PBS backups: Deduplicated copies on primary TrueNAS
- 📧 Email monitoring: Daily status reports
- ⚡ Power savings: 95% reduction

**Ready:**
- First coordinated run: Tomorrow at 2:00 AM
- Monitoring alert: 6:00 AM
- Both backup strategies: Fully automated
- Disaster recovery: Multiple restore options

---

**Status:** Integrated backup system successfully configured! ✅

**Your comprehensive backup strategy now includes:**
- Fast ZFS replication for large datasets
- Full Proxmox backups for VMs/CTs
- Central PBS deduplication
- Automated WOL power management
- Comprehensive monitoring and alerts
- 95% power savings on standby host

**Everything runs in a single 80-minute window at 2 AM daily.**
