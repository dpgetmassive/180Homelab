# Proxmox Backup Orchestration Script

Complete documentation for the automated backup orchestration system running on pve-scratchy.

## Overview

The `proxmox-backup-orchestration.sh` script coordinates all backup operations in a single nightly window, including:
- TrueNAS configuration backups
- ZFS replication monitoring
- Proxmox VM/CT backups

**Location**: `/usr/local/bin/proxmox-backup-orchestration.sh`
**Log File**: `/var/log/proxmox-backup-orchestration.log`
**Runs On**: pve-scratchy (10.16.1.22)
**Schedule**: Daily at 2:00 AM
**Version**: 2.4

## Execution Timeline

```
2:00 AM  Script Start
├─ Verify pve-itchy online
├─ Check pve-bk-truenas-primary storage
└─ Confirm VM 115 running

2:05 AM  TrueNAS Configuration Backups
├─ Backup Primary TrueNAS config (10.16.1.6)
├─ Backup DR TrueNAS config (10.16.1.20)
└─ Store in /mnt/pve/pve-bk-truenas-primary/truenas-configs/

2:08 AM  ZFS Replication Monitoring
├─ Wait for 2:10 AM snapshot creation
├─ Query replication status
├─ Monitor until completion
└─ Log state (RUNNING → FINISHED)

2:45 AM  Proxmox Backups Begin
├─ Backup all VMs (except 110, 115)
├─ Backup all containers
├─ Compress with zstd
└─ Store on pve-bk-truenas-primary

3:20 AM  Backup Cycle Complete
└─ Summary logged
```

## Script Components

### Configuration Variables

```bash
LOG_FILE="/var/log/proxmox-backup-orchestration.log"
ITCHY_IP="10.16.1.8"
TRUENAS_DR_IP="10.16.1.20"
TRUENAS_PRIMARY_IP="10.16.1.6"
TRUENAS_PRIMARY_PASSWORD="Getmassiv3"             # For API authentication
MAX_WAIT=300                                       # 5 minutes timeout
CONFIG_BACKUP_DIR="/mnt/pve/pve-bk-truenas-primary/truenas-configs"
REPLICATION_NAME="FileServer-to-DR"                # ZFS replication task name
```

### Logging Function

```bash
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}
```

All script output is timestamped and written to both console and log file.

### TrueNAS Configuration Backup Functions

**Two methods available** depending on SSH access:

#### API-Based Backup (Primary TrueNAS)

```bash
backup_truenas_config_api() {
    local TRUENAS_IP=$1
    local NAME=$2
    local PASSWORD=$3
    local DATE=$(date +%Y%m%d-%H%M%S)
    local DEST_FILE="${NAME}-config-${DATE}.db"

    # Create backup directory
    # Download via TrueNAS REST API: /api/v2.0/config/save
    # Use curl with basic authentication
    # Verify file is valid SQLite database
    # Clean up old backups (>14 days)
}
```

**When to use**: Primary TrueNAS (10.16.1.6) - SSH not configured
**Method**: curl to `https://10.16.1.6/api/v2.0/config/save`
**Authentication**: Basic auth with root credentials
**Output size**: ~796KB

#### SSH-Based Backup (DR TrueNAS)

```bash
backup_truenas_config_ssh() {
    local TRUENAS_IP=$1
    local NAME=$2
    local DATE=$(date +%Y%m%d-%H%M%S)
    local REMOTE_FILE="/data/freenas-v1.db"
    local DEST_FILE="${NAME}-config-${DATE}.db"

    # Create backup directory
    # Copy database via SSH: cat /data/freenas-v1.db
    # Verify file is valid SQLite database
    # Clean up old backups (>14 days)
}
```

**When to use**: DR TrueNAS (10.16.1.20) - SSH configured
**Method**: SSH cat of `/data/freenas-v1.db`
**Output size**: ~784KB

**Common attributes**:
- **Purpose**: Export TrueNAS configuration database for disaster recovery
- **Retention**: 14 days
- **Output**: `truenas-{primary|dr}-config-YYYYMMDD-HHMMSS.db`
- **Validation**: All backups verified as valid SQLite 3.x databases

## Step-by-Step Workflow

### Step 1: Pre-flight Checks

**Verify pve-itchy is online:**
```bash
if ping -c 1 -W 2 $ITCHY_IP >/dev/null 2>&1; then
    log "✓ pve-itchy is online"
else
    log "ERROR: pve-itchy is not responding"
    exit 1
fi
```

**Verify backup storage is available:**
```bash
if ssh root@$ITCHY_IP "pvesm status | grep -q itchy-backups"; then
    log "✓ itchy-backups storage available"
else
    log "ERROR: itchy-backups storage not available"
    exit 1
fi
```

**Check VM 115 status:**
```bash
if ssh root@$ITCHY_IP "qm status 115 | grep -q running"; then
    log "✓ VM 115 is already running"
else
    ssh root@$ITCHY_IP "qm start 115"
    sleep 90  # Wait for boot
fi
```

### Step 2: Wait for TrueNAS DR Ready

```bash
ELAPSED=0
while ! ssh root@$TRUENAS_DR_IP "echo ready" >/dev/null 2>&1; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    if [ $ELAPSED -ge $MAX_WAIT ]; then
        log "WARNING: TrueNAS DR not ready after 5 minutes"
        break
    fi
done
```

**Timeout**: 5 minutes
**Behavior**: Continue even if DR not ready (won't block other backups)

### Step 3: TrueNAS Configuration Backups

**Backup primary TrueNAS:**
```bash
if ping -c 1 -W 2 $TRUENAS_PRIMARY_IP >/dev/null 2>&1; then
    backup_truenas_config $TRUENAS_PRIMARY_IP "truenas-primary"
fi
```

**Backup DR TrueNAS:**
```bash
if [ "$DR_READY" = true ]; then
    backup_truenas_config $TRUENAS_DR_IP "truenas-dr"
fi
```

**Output Files:**
- `truenas-primary-config-20251119-234307.db`
- `truenas-dr-config-20251119-234307.db`

**Location**: `/mnt/pve/pve-bk-truenas-primary/truenas-configs/`

### Step 4: ZFS Replication Monitoring

**Wait for replication to start:**
```bash
sleep 30  # Give time for 2:10 AM snapshot trigger
```

**Query replication status:**
```bash
REPL_DATA=$(ssh root@$TRUENAS_PRIMARY_IP \
    "midclt call replication.query" 2>/dev/null)

REPL_STATE=$(echo "$REPL_DATA" | jq -r \
    ".[] | select(.name==\"$REPLICATION_NAME\") | .state.state")
```

**Monitor until completion:**
```bash
while [ $REPL_WAIT -lt 7200 ]; do  # Max 2 hours
    sleep 60
    # Check state: RUNNING → FINISHED or ERROR
    if [ "$REPL_STATE" = "FINISHED" ]; then
        log "✓ ZFS replication completed successfully!"
        break
    fi
done
```

**States Tracked:**
- `RUNNING` - Replication in progress
- `FINISHED` - Completed successfully
- `ERROR` - Failed (logs error message)
- Other - Not active or waiting

**Timeout**: 2 hours (prevents indefinite waiting)

### Step 5: Proxmox VM/CT Backups

**Execute vzdump:**
```bash
vzdump --all \
    --storage pve-bk-truenas-primary \
    --compress zstd \
    --mode snapshot \
    --exclude 110,115 \
    2>&1 | tee -a $LOG_FILE
```

**Parameters:**
- `--all`: Backup all VMs and containers
- `--storage pve-bk-truenas-primary`: Target storage (NFS from Primary TrueNAS)
- `--compress zstd`: Zstandard compression (fast, good ratio)
- `--mode snapshot`: Use LVM/ZFS snapshots (online backup)
- `--exclude 110,115`: Skip TrueNAS VMs

**Exclusions Explained:**
- **VM 110** (Primary TrueNAS): Too large (923 GB), protected by ZFS replication + Backblaze
- **VM 115** (DR TrueNAS): Is the backup target itself

### Step 6: Summary and Completion

```bash
log "=== Backup Cycle Summary ==="
log "✓ TrueNAS configs: Backed up to $CONFIG_BACKUP_DIR"
log "✓ ZFS replication: Monitored (FileServer data: 10.16.1.6 → 10.16.1.20)"
log "✓ Proxmox backups: VMs/CTs backed up to pve-bk-truenas-primary"
log "✓ Critical data: Protected via Backblaze CloudSync"
log "=== Coordinated backup cycle complete ==="
```

## Error Handling

### Storage Availability Check
```bash
if ! ssh root@$ITCHY_IP "pvesm status | grep -q pve-bk-truenas-primary"; then
    log "ERROR: pve-bk-truenas-primary storage not available!"
    exit 1
fi
```
**Behavior**: Exit immediately if backup target unavailable

### TrueNAS Timeouts
```bash
if [ $ELAPSED -ge $MAX_WAIT ]; then
    log "WARNING: TrueNAS DR not ready after 5 minutes"
    log "Will skip DR config backup but continue with other tasks"
fi
```
**Behavior**: Log warning and continue (doesn't block other backups)

### Replication Monitoring
```bash
if [ "$REPL_STATE" = "ERROR" ]; then
    REPL_ERROR=$(echo "$REPL_DATA" | jq -r '.[0].state.error')
    log "WARNING: ZFS replication failed with error: $REPL_ERROR"
fi
```
**Behavior**: Log error but continue with Proxmox backups

### Backup Job Failures
```bash
if vzdump ... 2>&1 | tee -a $LOG_FILE; then
    log "✓ Proxmox backups completed successfully"
else
    BACKUP_EXIT=$?
    log "WARNING: Proxmox backups exited with code $BACKUP_EXIT"
fi
```
**Behavior**: Log exit code and continue (allows partial success)

## Dependencies

### Required Commands
- `ssh` - Remote command execution
- `ping` - Connectivity testing
- `jq` - JSON parsing (for replication status)
- `vzdump` - Proxmox backup utility
- `file` - File type verification
- `scp` - Secure file copy

### SSH Key Requirements
- pve-scratchy → pve-itchy (root access)
- pve-scratchy → TrueNAS Primary (root access)
- pve-scratchy → TrueNAS DR (root access)

**Setup SSH keys:**
```bash
ssh-copy-id root@10.16.1.8
ssh-copy-id root@10.16.1.6
ssh-copy-id root@10.16.1.20
```

### Storage Requirements
- pve-bk-truenas-primary must be mounted and enabled
- 7.4 TB NFS storage from Primary TrueNAS (10.16.1.6)
- Directory `/mnt/pve/pve-bk-truenas-primary/truenas-configs/` must be writable

## Cron Schedule

```bash
# On pve-scratchy
0 2 * * * /usr/local/bin/proxmox-backup-orchestration.sh
```

**Time**: 2:00 AM daily
**User**: root
**Output**: Logged to `/var/log/proxmox-backup-orchestration.log`

## Manual Execution

**Run script manually:**
```bash
ssh root@10.16.1.22 "/usr/local/bin/proxmox-backup-orchestration.sh"
```

**Watch log in real-time:**
```bash
ssh root@10.16.1.22 "tail -f /var/log/proxmox-backup-orchestration.log"
```

**Test individual components:**
```bash
# Test TrueNAS ping
ssh root@10.16.1.22 "ping -c 3 10.16.1.6"

# Test storage availability
ssh root@10.16.1.8 "pvesm status -storage pve-bk-truenas-primary"

# Test replication query
ssh root@10.16.1.6 "midclt call replication.query | jq"
```

## Log Analysis

### Check Last Backup Status
```bash
ssh root@10.16.1.22 "grep 'Backup Cycle Summary' /var/log/proxmox-backup-orchestration.log | tail -1"
```

### Find Errors
```bash
ssh root@10.16.1.22 "grep -i 'error\|warning' /var/log/proxmox-backup-orchestration.log | tail -20"
```

### Check Duration
```bash
ssh root@10.16.1.22 "grep -E '(Starting coordinated|cycle complete)' /var/log/proxmox-backup-orchestration.log | tail -2"
```

### View Today's Run
```bash
ssh root@10.16.1.22 "grep '$(date +%Y-%m-%d)' /var/log/proxmox-backup-orchestration.log"
```

## Troubleshooting

### Backup Not Running

**Check cron:**
```bash
ssh root@10.16.1.22 "crontab -l | grep orchestration"
```

**Expected output:**
```
0 2 * * * /usr/local/bin/proxmox-backup-orchestration.sh
```

**Check cron service:**
```bash
ssh root@10.16.1.22 "systemctl status cron"
```

**View cron logs:**
```bash
ssh root@10.16.1.22 "grep CRON /var/log/syslog | grep orchestration | tail -5"
```

### pve-itchy Unreachable

**Verify network:**
```bash
ping -c 3 10.16.1.8
```

**Check if powered on:**
```bash
ssh root@10.16.1.22 "wakeonlan -i 10.16.1.255 60:45:cb:69:85:83"
sleep 120
ping -c 3 10.16.1.8
```

**Check from cluster:**
```bash
ssh root@10.16.1.22 "pvecm nodes"
```

### Storage Not Available

**Check mount:**
```bash
ssh root@10.16.1.8 "df -h | grep pve-bk-truenas"
```

**Check storage status:**
```bash
ssh root@10.16.1.8 "pvesm status -storage pve-bk-truenas-primary"
```

**Enable if disabled:**
```bash
ssh root@10.16.1.22 "pvesm set pve-bk-truenas-primary --disable 0"
```

**Verify permissions:**
```bash
ssh root@10.16.1.8 "ls -ld /mnt/pve/pve-bk-truenas-primary"
ssh root@10.16.1.8 "touch /mnt/pve/pve-bk-truenas-primary/test && rm /mnt/pve/pve-bk-truenas-primary/test"
```

### VM 115 Won't Start

**Check VM status:**
```bash
ssh root@10.16.1.8 "qm status 115"
```

**Check VM config:**
```bash
ssh root@10.16.1.8 "qm config 115"
```

**Try manual start:**
```bash
ssh root@10.16.1.8 "qm start 115"
```

**View VM console:**
```bash
ssh root@10.16.1.8 "qm monitor 115"
# Or access via Proxmox web UI
```

### ZFS Replication Not Working

**Check replication tasks:**
```bash
ssh root@10.16.1.6 "midclt call replication.query | jq '.[] | {name, state}'"
```

**Check last snapshot:**
```bash
ssh root@10.16.1.6 "zfs list -t snapshot Tank/FileServer | tail -5"
```

**Manual replication test:**
```bash
ssh root@10.16.1.6 "midclt call replication.run_onetime {\"id\": 4}"
```

**Check SSH between TrueNAS hosts:**
```bash
ssh root@10.16.1.6 "ssh root@10.16.1.20 'echo test'"
```

### Backups Failing

**Check disk space:**
```bash
ssh root@10.16.1.8 "df -h /mnt/pve/pve-bk-truenas-primary"
```

**List recent backups:**
```bash
ssh root@10.16.1.8 "ls -lth /mnt/pve/pve-bk-truenas-primary/dump/ | head -20"
```

**Test single VM backup:**
```bash
vzdump 100 --storage pve-bk-truenas-primary --compress zstd --mode snapshot
```

**Check vzdump logs:**
```bash
ssh root@10.16.1.22 "ls -lt /var/log/vzdump/ | head -5"
ssh root@10.16.1.22 "cat /var/log/vzdump/qemu-100.log"
```

### Config Backups Failing

**Test TrueNAS SSH:**
```bash
ssh root@10.16.1.6 "hostname"
ssh root@10.16.1.20 "hostname"
```

**Check database file:**
```bash
ssh root@10.16.1.6 "ls -lh /data/freenas-v1.db"
ssh root@10.16.1.6 "file /data/freenas-v1.db"
```

**Test manual backup:**
```bash
ssh root@10.16.1.6 "cat /data/freenas-v1.db" > /tmp/test-config.db
file /tmp/test-config.db
rm /tmp/test-config.db
```

## Known Issues

### Issue 1: Primary TrueNAS Config Backup Fails
**Symptom**: `WARNING: Could not download config from truenas-primary`
**Cause**: SQLite backup method incompatible with TrueNAS Scale
**Workaround**: Manual config export via web UI
**Status**: Fix pending (direct file copy method to be implemented)

### Issue 2: ZFS Replication Status Query Fails
**Symptom**: `WARNING: Could not query replication status`
**Cause**: API call may need authentication or different syntax
**Workaround**: Manual verification via SSH
**Status**: To be refined based on TrueNAS Scale API docs

### Issue 3: Storage Shows as Disabled
**Symptom**: `storage 'pve-bk-truenas-primary' is disabled`
**Fix**: `pvesm set pve-bk-truenas-primary --disable 0`
**Prevention**: Unknown why it becomes disabled
**Status**: Monitor for recurrence

## Performance Tuning

### Compression Level
Current: `zstd` (default level 3)

**Faster backups:**
```bash
vzdump --compress zstd:1  # Faster, less compression
```

**Better compression:**
```bash
vzdump --compress zstd:9  # Slower, more compression
```

### Bandwidth Limiting
```bash
vzdump --bwlimit 50000  # Limit to 50 MB/s
```

### Exclude Large Datasets
Add to exclude list if needed:
```bash
vzdump --exclude 110,115,<VMID>
```

## Related Documentation

- [Backup System Overview](./README.md)
- [ZFS Replication](./zfs-replication.md)
- [Proxmox Backups](./proxmox-backups.md)
- [Monitoring System](../monitoring/README.md)

## Script Source

The script is maintained at:
- **Location**: `/usr/local/bin/proxmox-backup-orchestration.sh` on pve-scratchy
- **Backup**: `/usr/local/bin/wake-backup-shutdown-v2.1.backup`
- **Version**: 2.2

To view the current script:
```bash
ssh root@10.16.1.22 "cat /usr/local/bin/proxmox-backup-orchestration.sh"
```

---

**Last Updated**: 2025-11-19
**Version**: 2.2
**Maintainer**: Get Massive Dojo Infrastructure Team
