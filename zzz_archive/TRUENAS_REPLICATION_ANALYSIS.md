# TrueNAS ZFS Replication Analysis & WOL Integration

**Date:** 2025-11-15
**Analyzed:** Primary TrueNAS (10.16.1.6) → DR TrueNAS (10.16.1.20)

---

## Current Setup

### Replication Task 1: FileServer-to-DR ✅ WORKING

**Configuration:**
- **Source:** Tank/FileServer (VM 110 on pve-scratchy)
- **Destination:** Tank/Data-DR-Copy/FileServer (VM 115 on pve-itchy)
- **Direction:** PUSH (primary to DR)
- **Transport:** SSH
- **Status:** ✅ FINISHED (last run: 1 hour ago)
- **Data Size:** 923 GB
- **Snapshots:** Automatic every 1:50 AM and 7:50 PM (twice daily)
- **Retention:** 4 weeks on source
- **Schedule:** Auto (runs after snapshot creation)

**Last Successful Replication:**
- Started: 2025-11-15 19:50:00
- Finished: 2025-11-15 20:44:16
- Duration: ~54 minutes
- Latest snapshot: auto-2025-11-15_19-50
- Caught up from old snapshots (was behind since 2023-12-21!)

**Issues Found:**
- Had accumulated many old snapshots from 2023
- Was resuming from interrupted transfer
- Now caught up and working properly

### Replication Task 2: Downloads-to-DR ❌ ERROR

**Configuration:**
- **Source:** Tank/Downloads (VM 110 on pve-scratchy)
- **Destination:** Tank/Data-DR-Copy/Downloads (VM 115 on pve-itchy)
- **Direction:** PUSH
- **Status:** ❌ ERROR (last run: 3 hours ago)
- **Error:** "cannot receive incremental stream: most recent snapshot does not match incremental source"
- **Snapshots:** Automatic every 2:00 AM and 7:00 PM (twice daily)
- **Retention:** 2 weeks on source

**Root Cause:**
This error indicates snapshot divergence - the destination has a different snapshot than expected for incremental replication. This typically happens when:
1. Snapshots were manually deleted on destination
2. Replication was interrupted mid-stream
3. Destination dataset was rolled back
4. Configuration changes caused snapshot mismatch

**Fix Required:**
Need to reset the replication by either:
- Finding common snapshot and resuming from there
- Deleting destination dataset and starting fresh
- Using `allow_from_scratch` to force full resync

---

## WOL Integration Strategy

### Can We Apply WOL to ZFS Replication?

**YES! Here's the approach:**

The TrueNAS replication is currently set to run automatically whenever a snapshot is created. Since VM 115 (TrueNAS DR) is on pve-itchy, we can integrate this with our WOL automation.

### Option 1: Coordinated Replication During Backup Window (RECOMMENDED)

**Concept:**
Run ZFS replication at the same time as Proxmox backups, during the WOL window when pve-itchy is already awake.

**Schedule:**
```
02:00 AM - WOL sent to pve-itchy
02:01 AM - pve-itchy boots (~3 minutes)
02:05 AM - VM 115 (TrueNAS DR) starts
02:10 AM - ZFS replication runs (primary → DR)
02:30 AM - Proxmox backups start
03:00 AM - All complete, shutdown pve-itchy
```

**Implementation:**
1. Change TrueNAS snapshot schedule to 2:10 AM (instead of 1:50 AM and 7:50 PM)
2. Modify WOL script to:
   - Wait for pve-itchy to boot
   - Start VM 115 (TrueNAS DR)
   - Wait for VM 115 to be ready
   - Trigger replication (or wait for auto-replication)
   - Run Proxmox backups
   - Shutdown sequence

**Benefits:**
- ✅ Single WOL window (efficient)
- ✅ Both replications happen together
- ✅ Minimal pve-itchy uptime
- ✅ No need for second WOL event
- ✅ Synchronized backup strategy

**Drawbacks:**
- ⚠️ Twice-daily replication becomes once-daily
- ⚠️ Longer WOL window (~1 hour total)
- ⚠️ VM 115 must start (uses more resources)

### Option 2: Disable Replication, Rely on Proxmox Backups

**Concept:**
Since we're now backing up the primary TrueNAS (VM 110) via Proxmox, the DR TrueNAS becomes redundant.

**Implementation:**
1. Disable both replication tasks
2. Power down VM 115 permanently
3. Rely on Proxmox backups of VM 110
4. Restore VM 110 to pve-itchy if primary fails

**Benefits:**
- ✅ Simplest solution
- ✅ VM 115 no longer needed (save resources)
- ✅ Proxmox backups already configured
- ✅ No ZFS replication complexity

**Drawbacks:**
- ⚠️ Lose real-time data sync (RPO = 24 hours)
- ⚠️ Lose ZFS snapshot benefits on DR
- ⚠️ Longer recovery time (restore VM vs failover)

### Option 3: Keep Current Schedule, Manually Start VM 115

**Concept:**
Keep replication at current times (1:50 AM, 7:50 PM), but require VM 115 to be manually powered on or always-on.

**Implementation:**
1. Keep VM 115 powered on 24/7
2. Replication runs automatically as configured
3. OR: Manually start VM 115 before replication times

**Benefits:**
- ✅ No changes to working replication
- ✅ Twice-daily replication maintained
- ✅ Best RPO (12 hours)

**Drawbacks:**
- ⚠️ VM 115 must be powered 24/7 (defeats WOL goal)
- ⚠️ OR requires manual intervention
- ⚠️ pve-itchy can't be powered down

---

## Recommended Solution

### Hybrid Approach: Daily Coordinated Replication + Proxmox Backups

**Best of both worlds:**

1. **Keep FileServer replication** (923 GB of data)
   - Too large for frequent Proxmox backups
   - ZFS replication is efficient (only changed blocks)
   - Schedule: Once daily at 2:10 AM during WOL window

2. **Disable Downloads replication** (currently broken)
   - Smaller dataset, can rely on Proxmox backups
   - Avoids fixing the snapshot mismatch issue

3. **Modify WOL script** to handle both backup types

### Updated Daily Schedule

```
02:00 AM - Wake pve-itchy (WOL)
02:01 AM - pve-itchy boots
02:05 AM - Start VM 115 (TrueNAS DR)
02:08 AM - VM 115 ready, SSH available
02:10 AM - TrueNAS snapshot created on primary
02:11 AM - ZFS replication starts (FileServer)
02:45 AM - ZFS replication complete (~35 min for 923 GB)
02:46 AM - Proxmox backups start (all VMs/CTs)
03:20 AM - Proxmox backups complete (~35 min)
03:21 AM - Shutdown VM 115
03:22 AM - Shutdown pve-itchy

Total pve-itchy uptime: ~80 minutes/day
Total VM 115 uptime: ~75 minutes/day
```

### Implementation Steps

**1. Update TrueNAS Snapshot Schedule:**
```bash
# On primary TrueNAS (10.16.1.6)
# Change snapshot time from 1:50 AM to 2:10 AM
# Remove 7:50 PM snapshot (or keep for additional backup point)
```

**2. Modify WOL Script:**
```bash
#!/bin/bash
# Enhanced wake-backup-shutdown script with ZFS replication

LOG_FILE="/var/log/wake-backup-shutdown.log"
ITCHY_MAC="60:45:cb:69:85:83"
ITCHY_IP="10.16.1.8"
TRUENAS_DR_IP="10.16.1.20"
MAX_WAIT=300

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Wake pve-itchy
log "=== Starting wake-backup-shutdown cycle ==="
wakeonlan $ITCHY_MAC
sleep 180  # Wait for boot

# Start VM 115 (TrueNAS DR)
log "Starting VM 115 (TrueNAS DR)..."
ssh root@$ITCHY_IP "qm start 115"
sleep 120  # Wait for TrueNAS to boot

# Wait for TrueNAS DR to be SSH-accessible
log "Waiting for TrueNAS DR to be ready..."
ELAPSED=0
while ! ssh -o ConnectTimeout=5 root@$TRUENAS_DR_IP "echo ready" >/dev/null 2>&1; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    if [ $ELAPSED -ge 300 ]; then
        log "ERROR: TrueNAS DR did not become ready"
        exit 1
    fi
done

log "TrueNAS DR is ready!"

# Trigger replication on primary TrueNAS
# (Replication will auto-run when snapshot is created at 2:10 AM)
# OR manually trigger it:
# ssh root@10.16.1.6 "midclt call replication.run 4"

# Wait for replication to complete (monitor it)
log "Monitoring ZFS replication..."
sleep 60  # Give it time to start

# Check replication status
while ssh root@10.16.1.6 "midclt call replication.query | jq -r '.[0].job.state'" | grep -q "RUNNING"; do
    log "Replication still running..."
    sleep 60
done

log "ZFS replication complete!"

# Now run Proxmox backups
log "Starting Proxmox backups..."
vzdump --all 1 --storage itchy-backups --compress zstd --mode snapshot --exclude 115

log "Backups complete, shutting down VM 115..."
ssh root@$ITCHY_IP "qm shutdown 115"
sleep 30

log "Shutting down pve-itchy..."
ssh root@$ITCHY_IP "shutdown -h now"
sleep 30

log "=== Cycle complete ==="
```

**3. Fix Downloads Replication (Optional):**

If you want to keep it, reset the replication:
```bash
# On TrueNAS DR (10.16.1.20)
# Option 1: Delete and recreate
zfs destroy -r Tank/Data-DR-Copy/Downloads

# Option 2: Find common snapshot and manually sync
# This requires identifying which snapshot matches on both sides
```

---

## Storage Considerations

### Current Data Sizes

**FileServer:**
- Primary: 923 GB
- DR Copy: 923 GB
- Replication time: ~35-50 minutes
- Bandwidth: ~400-500 Mbps (efficient incremental)

**Downloads:**
- Size: Unknown (needs checking)
- Currently broken
- Would benefit from reset

### pve-itchy Storage Impact

**Current:**
- VM 115: Uses 32 GB disk + 3x 8TB passthrough drives
- Running only during replication window
- Receives ~923 GB of replicated data

**After changes:**
- Same storage requirements
- Reduced uptime (~75 min/day vs 24/7)
- Significant power savings

---

## Comparison: ZFS Replication vs Proxmox Backups

| Feature | ZFS Replication | Proxmox Backup |
|---------|-----------------|----------------|
| **Speed** | Very fast (block-level incremental) | Slower (file-level) |
| **Efficiency** | Only changed blocks | Deduplication helps but less efficient |
| **Snapshots** | Native ZFS snapshots on both sides | Single backup copy |
| **Failover** | Instant (mount replicated dataset) | Slow (restore from backup) |
| **RPO** | As frequent as snapshots (2x daily) | Daily backup window |
| **RTO** | Minutes (failover to DR) | Hours (restore VM) |
| **Bandwidth** | Efficient (only diffs) | Full backup on first run |
| **Use Case** | Large datasets (>100 GB) | VMs, configs, smaller data |

**Verdict:** ZFS replication is superior for large datasets like FileServer (923 GB), but Proxmox backups are fine for VMs and smaller data.

---

## Monitoring Enhancements

### Add Replication Monitoring

**Check replication status:**
```bash
#!/bin/bash
# /usr/local/bin/check-replication-status.sh

TRUENAS_PRIMARY="10.16.1.6"
ALERT_EMAIL="dp@getmassive.com.au"

# Check replication state
STATE=$(ssh root@$TRUENAS_PRIMARY "midclt call replication.query | jq -r '.[0].state.state'")
ERROR=$(ssh root@$TRUENAS_PRIMARY "midclt call replication.query | jq -r '.[0].state.error'")

if [ "$STATE" = "ERROR" ]; then
    echo "ZFS Replication ERROR: $ERROR" | mail -s "[ALERT] TrueNAS Replication Failed" $ALERT_EMAIL
elif [ "$STATE" != "FINISHED" ]; then
    echo "ZFS Replication in unexpected state: $STATE" | mail -s "[WARNING] TrueNAS Replication Status" $ALERT_EMAIL
fi
```

**Add to cron:**
```
# Check replication status at 3 AM (after it should complete)
0 3 * * * /usr/local/bin/check-replication-status.sh
```

---

## Recommendations Summary

### Immediate Actions

1. ✅ **Keep FileServer replication** - it's working and efficient for 923 GB
2. ❌ **Disable or fix Downloads replication** - currently broken, decision needed
3. 🔄 **Modify WOL script** to coordinate both replication types
4. 📅 **Change snapshot schedule** to 2:10 AM (during WOL window)
5. 📊 **Add replication monitoring** to existing monitoring script

### Decision Points

**Question 1: What to do with Downloads replication?**
- **Option A:** Fix it (reset destination and resync)
- **Option B:** Disable it (rely on Proxmox backups)
- **Option C:** Fix it later (disable for now)

**Question 2: Keep twice-daily replication?**
- **Option A:** Once daily at 2:10 AM (during WOL window)
- **Option B:** Twice daily (requires VM 115 to be always-on OR second WOL event)

**Question 3: What's the acceptable RPO for FileServer data?**
- Daily replication = 24-hour RPO (lose up to 1 day of changes)
- Twice-daily = 12-hour RPO (lose up to 12 hours)
- Hourly snapshots locally + daily replication = Best of both

### Recommended Configuration

**For FileServer (923 GB):**
- Schedule: Once daily at 2:10 AM
- Retention: 4 weeks on source, 1 month on DR
- Method: ZFS replication (efficient for large data)

**For Downloads:**
- Recommendation: Disable replication, rely on Proxmox backups
- Alternative: Fix snapshot mismatch and replicate during WOL window

**For Other Data:**
- Use Proxmox backups to pve-itchy
- Smaller datasets, easier to manage

---

## Summary

### Current State
- ✅ FileServer replication working (923 GB, last run 1h ago)
- ❌ Downloads replication broken (snapshot mismatch error)
- 🔄 Both replicate to VM 115 on pve-itchy (currently 24/7)

### Proposed State
- ✅ FileServer replication at 2:10 AM during WOL window
- ❓ Downloads replication (fix, disable, or defer decision)
- 🔄 VM 115 only runs ~75 minutes/day
- 📊 Monitoring for both replication and backups
- ⚡ Power savings: ~97% reduction in pve-itchy uptime

### Integration Benefits
- Single WOL window for all backup operations
- Coordinated shutdown after completion
- Comprehensive monitoring and alerting
- Significant power savings
- Maintains ZFS replication benefits for large datasets

---

**Next Steps:**
1. Decide on Downloads replication strategy
2. Modify WOL script to include VM 115 startup
3. Change TrueNAS snapshot schedule to 2:10 AM
4. Add replication monitoring
5. Test coordinated backup cycle
6. Monitor first automated run

Would you like me to implement any of these changes?
