# Phase 6: PBS Replication Complete ✅

**Date:** 2025-11-15
**Duration:** ~10 minutes
**Status:** Successfully Configured

---

## What Was Configured

### Automatic Backup Schedule

**Backup Job ID:** backup-44a0156b-3f6b

**Configuration:**
- **Schedule:** Daily at 02:00 (2 AM)
- **Mode:** Snapshot (suspend mode for LVM volumes)
- **Compression:** zstd
- **Storage:** prox-backup-srv (PBS at 10.16.1.41)
- **Scope:** All VMs and Containers on pve-scratchy
- **Excluded:** VM 115 (TrueNAS DR on pve-itchy)
- **Retention:** keep-last=3, keep-monthly=1
- **Notifications:** Email to dp@getmassive.com.au
- **Status:** Enabled ✅

###Workloads Included in Backup

**VMs (6):**
- VM 100: dockc (92 GB) - Primary Docker host
- VM 102: Anisble-master (32 GB)
- VM 103: zabbix (32 GB)
- VM 107: deb-util-01 (32 GB)
- VM 109: docka (100 GB) - Secondary Docker host
- VM 110: truenas-scale (32 GB) - Primary TrueNAS
- VM 112: deb-srv-plex (64 GB) - Plex server

**Containers (8):**
- CT 101: watchyourlan (2 GB)
- CT 104: wikijs (6 GB)
- CT 106: docker00 (8 GB)
- CT 108: plexpunnisher (64 GB)
- CT 113: proxmox-datacenter-manager (10 GB)
- CT 129: crafty-s (16 GB)
- CT 900: proxbackupsrv (20 GB)
- CT 901: tailscaler (8 GB)

**Total Data:** ~370 GB across 14 workloads

---

## Test Backup Results

### CT 129 (crafty-s) Test Backup
**Test Date:** 2025-11-15 20:49
**Duration:** 4 minutes 55 seconds
**Status:** ✅ Success

**Performance Metrics:**
- Container size: 11.121 GiB
- First sync: 11.93 GB in 165 seconds (~74 MB/s)
- Final sync (after suspend): 18.80 MB in 1 second
- Guest downtime: 1 second ✅ (minimal impact)
- Incremental efficiency: 93.8% data reused
- New data uploaded: 710 MB (compressed to 237 MB)
- Upload speed: 15.64 MB/s average
- Total backup time: 4:55

**Deduplication:**
- Previous backup detected (from March 16, 2025)
- Reused 10.427 GiB (93.8%)
- Only transferred new/changed data

**Backup Location:**
- PBS datastore: proxmoxbackupsrv
- Path: ct/129/2025-11-15T09:49:32Z
- Server: 10.16.1.41 (CT 900)

---

## How It Works

### Daily Backup Process (Automated at 2 AM)

1. **2:00 AM:** Backup job triggers
2. **Vzdump runs** for each VM/CT sequentially
3. **For each workload:**
   - Create snapshot (or suspend if LVM)
   - Sync data to temporary location
   - Finalize and resume guest
   - Upload to PBS with deduplication
   - Compressed with zstd
4. **After all complete:**
   - PBS prunes old backups (keeps last 3 + monthly)
   - Email notification sent
   - Job completes

### Expected Total Time
Based on test backup:
- Small containers (2-20 GB): 2-10 minutes each
- Large containers (64 GB): 15-20 minutes each
- VMs (32-100 GB): 10-30 minutes each

**Estimated total runtime:** 2-3 hours for all 14 workloads
**Completion window:** 2:00 AM - 5:00 AM

---

## Backup vs Replication

### Why PBS Backup Instead of Replication?

**Original Plan:** Use Proxmox replication feature
**Reality:** LVM storage doesn't support native replication (ZFS only)

**Solution:** PBS backup provides better functionality:

**Advantages of PBS Backup:**
1. ✅ Works with all storage types (LVM, ZFS, NFS)
2. ✅ Incremental backups with deduplication (93.8% efficiency)
3. ✅ Compression (zstd) saves space
4. ✅ Retention policies (keep last 3, keep monthly)
5. ✅ Easy restore from any backup point
6. ✅ Verification and integrity checking
7. ✅ Email notifications

**Comparison:**

| Feature | PBS Backup | Replication |
|---------|-----------|-------------|
| Storage support | All types | ZFS only |
| Deduplication | Yes (93.8%) | No |
| Compression | Yes (zstd) | No |
| Retention | Flexible | Manual |
| Point-in-time restore | Multiple points | Last sync only |
| Space efficiency | High | Low |
| Our use case | ✅ Perfect | ❌ Won't work |

---

## Storage Impact

### PBS Datastore (prox-backup-srv)
**Location:** CT 900 on pve-scratchy (10.16.1.41)
**Capacity:** 2 TB
**Current usage:** 315 GB (14.69%)
**After full backup:** ~450-500 GB estimated (22-25%)
**Status:** ✅ Plenty of space

### NFS Backup Storage (proxmoxbackups)
**Location:** TrueNAS DR on pve-itchy (10.16.1.20)
**Capacity:** 8 TB
**Current usage:** 1.4 TB (17.70%)
**Status:** ✅ Available as secondary backup target

---

## Retention Policy

### Current Settings
- **keep-last:** 3 (last 3 daily backups)
- **keep-monthly:** 1 (one monthly backup)

### What This Means
- **Daily backups:** Kept for 3 days, then deleted
- **Monthly backups:** First backup of each month kept indefinitely
- **Example:**
  - Nov 15: Kept (latest)
  - Nov 14: Kept (last-1)
  - Nov 13: Kept (last-2)
  - Nov 12: Deleted (older than 3 days)
  - Nov 1: Kept (monthly)

### Storage Impact
With ~370 GB per full backup:
- 3 daily backups: ~400 GB (with deduplication)
- Plus monthly snapshots
- **Total expected:** 500-800 GB (well within 2 TB capacity)

---

## Disaster Recovery Capabilities

### What Can Be Recovered

**Full VM/CT Restore:**
- Any workload from any of last 3 days
- Any workload from first-of-month backups
- Restore to pve-scratchy or pve-itchy
- Restore to different storage if needed

**Individual File Restore:**
- Browse backup contents
- Extract specific files/directories
- No need to restore entire VM/CT

### RTO (Recovery Time Objective)
- Small container (10 GB): ~5-10 minutes
- Large container (64 GB): ~20-30 minutes
- VM (100 GB): ~30-60 minutes
- Full infrastructure: ~4-6 hours

### RPO (Recovery Point Objective)
- **Daily backups:** Maximum 24 hours data loss
- **With 2 AM schedule:** Worst case = lose up to 1 day of changes

---

## Monitoring & Notifications

### Email Notifications
- **Recipient:** dp@getmassive.com.au
- **Trigger:** Always (success and failure)
- **Contents:**
  - Backup start/completion time
  - Duration
  - Success/failure status
  - Size and compression stats
  - Any errors or warnings

### Manual Monitoring
```bash
# Check backup job status
pvesh get /cluster/backup/backup-44a0156b-3f6b

# List recent backups on PBS
ssh root@10.16.1.41 "proxmox-backup-manager backup list"

# Check PBS datastore usage
ssh root@10.16.1.41 "proxmox-backup-manager datastore list"

# View backup logs
less /var/log/vzdump.log
```

---

## Testing & Validation

### Test Backup Completed ✅
- CT 129 backed up successfully
- Deduplication working (93.8% reuse)
- Compression working (3x reduction)
- Minimal downtime (1 second)
- Email notification sent

### Recommended Tests

**Before First Automated Run:**
1. ✅ Test backup of one container (completed)
2. ⏭️ Test restore of that backup
3. ⏭️ Wait for automated 2 AM run
4. ⏭️ Verify all workloads backed up
5. ⏭️ Check email notification received

**Monthly:**
1. Test restore of at least one VM
2. Test restore of at least one container
3. Verify monthly retention working
4. Check PBS storage usage trends

---

## Current Limitations

### TrueNAS DR (VM 115) Not Backed Up
**Reason:** VM 115 is on pve-itchy and excluded from backup job
**Impact:** DR TrueNAS not protected by PBS
**Mitigation:**
- TrueNAS has own ZFS snapshots
- Data is replicated from primary TrueNAS
- Offsite backups exist
- Can be rebuilt if needed

**Future Option:** Create separate backup job for itchy workloads

### No Real-Time Replication
**Current:** Daily backups at 2 AM (24-hour RPO)
**Not Possible:** Real-time/continuous replication with LVM storage
**Acceptable:** For homelab use, daily is sufficient
**Improvement:** Could add additional backup at 2 PM for 12-hour RPO

---

## Phase 7 Status: BLOCKED

### Power Management Not Implemented
**Reason:** TrueNAS DR (VM 115) must remain powered on 24/7
- Hosts NFS exports for PBS and proxmoxbackups
- Located on pve-itchy
- Prevents pve-itchy from powering down

### Options to Unblock Phase 7

**Option A: Migrate NFS exports to primary TrueNAS**
- Move backup NFS to VM 110 (10.16.1.6) on pve-scratchy
- Allows pve-itchy to power down
- Both TrueNAS instances on same host (consolidation complete)

**Option B: Keep current setup**
- pve-itchy stays powered 24/7 for TrueNAS DR
- Skip automated power-down
- Still have backups for disaster recovery

**Option C: Retire TrueNAS DR**
- Power down VM 115
- Use only primary TrueNAS
- Rely on PBS backups + offsite backups
- Simplest but removes DR capability

**Recommendation:** Decide on TrueNAS strategy before proceeding to Phase 7

---

## Summary

### ✅ Phase 6 Complete

**Configured:**
- Automated daily backups at 2 AM
- All 14 workloads on pve-scratchy included
- PBS with deduplication and compression
- Retention: last 3 days + monthly
- Email notifications

**Tested:**
- Manual backup successful
- Deduplication working (93.8% efficiency)
- Minimal downtime (1 second)
- Performance acceptable (15.64 MB/s)

**Ready:**
- First automated backup will run tomorrow at 2:00 AM
- PBS has sufficient capacity (2 TB datastore)
- Disaster recovery capability established

### 📊 Current Architecture

```
pve-scratchy (PRIMARY) ──2AM Daily──> PBS (CT 900)
    │                                    │
    ├─ 7 VMs                        ┌────▼────┐
    ├─ 8 Containers                 │ 2 TB    │
    │                                │ 315 GB  │
    └─ Backup job: all workloads    │  used   │
                                     └─────────┘
                                          │
                                          │ NFS mount
                                          ▼
                                   TrueNAS DR
                                   (VM 115 on pve-itchy)
                                   - 3x 8TB drives
                                   - NFS exports
                                   - 24/7 powered
```

### 🎯 Next Steps

**Phase 6 Follow-up:**
1. Wait for first automated backup (tomorrow 2 AM)
2. Verify email notification received
3. Check all workloads backed up successfully
4. Test restore of one VM and one container

**Phase 7 Blocker:**
- Decide TrueNAS DR strategy
- Either migrate NFS or accept 24/7 operation

---

**Status:** PBS replication configured and tested successfully! ✅
**Daily backups will begin tomorrow at 2:00 AM.**
