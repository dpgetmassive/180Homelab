# HomeLab Monitoring System - November 2025

**Date:** 2025-11-16
**Status:** ✅ Operational
**Alert Method:** ntfy.sh push notifications

---

## Overview

Comprehensive three-layer monitoring system for homelab infrastructure with external deadman switch for complete outage detection.

### Monitoring Layers

1. **Daily Backup Status** - Verifies nightly backup completion and ZFS replication
2. **ZFS Replication Health** - Monitors TrueNAS primary → DR replication
3. **Homelab Online Status** - External heartbeat monitoring via perrett.tech

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    pve-scratchy (10.16.1.22)                │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Daily Backup & Monitoring (6:00 AM)              │   │
│  │  - check-backup-status-ntfy.sh                     │   │
│  │  - Checks backup logs                              │   │
│  │  - Verifies ZFS replication                        │   │
│  │  - Sends ntfy.sh alerts                            │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Heartbeat Sender (every 15 min)                   │   │
│  │  - send-heartbeat.sh                               │   │
│  │  - SSH to perrett.tech                             │   │
│  │  - Update timestamp file                           │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ SSH (port 22)
                              │ Heartbeat every 15 min
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              perrett.tech (www.perrett.tech)                │
│                                                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Heartbeat Monitor (every 15 min)                  │   │
│  │  - check-homelab.sh                                │   │
│  │  - Check timestamp age                             │   │
│  │  - Alert if >30 minutes old                        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  /opt/homelab-monitor/homelab-heartbeat.txt                │
│  (timestamp file)                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS POST
                              │ Alerts when needed
                              ▼
                    ┌──────────────────────┐
                    │    ntfy.sh Cloud     │
                    │  Topic: homelab-     │
                    │  backup-alerts-dp    │
                    └──────────────────────┘
                              │
                              ▼
                    ┌──────────────────────┐
                    │   Mobile App / Web   │
                    │   Push Notifications │
                    └──────────────────────┘
```

---

## Alert Configuration

### ntfy.sh Setup

**Topic:** `homelab-backup-alerts-dp`

**Access Methods:**
- **Mobile App:** Install ntfy.sh app, subscribe to topic
- **Web:** https://ntfy.sh/homelab-backup-alerts-dp
- **Alternative:** Gotify at http://10.16.1.4:8085 (local only)

**Alert Types:**

| Alert | Priority | Tags | When | Frequency |
|-------|----------|------|------|-----------|
| ✅ Backup Success | 3 (default) | white_check_mark | Daily 6:00 AM | Daily |
| ⚠️ Backup Warning | 4 (high) | warning | Issues detected | As needed |
| 🚨 Backup Failed | 5 (urgent) | rotating_light,warning | Backup errors | As needed |
| 🚨 Homelab Offline | 5 (urgent) | warning,skull | >30 min no heartbeat | Every 15 min while offline |
| ⚠️ ZFS Replication Issue | 4 (high) | warning | Replication failed | Daily if failing |

---

## Component Details

### 1. Daily Backup Monitoring

**Script:** `/usr/local/bin/check-backup-status-ntfy.sh` (pve-scratchy)

**Schedule:** Daily at 6:00 AM
```bash
0 6 * * * /usr/local/bin/check-backup-status-ntfy.sh >> /var/log/backup-monitoring.log 2>&1
```

**What it checks:**
- Backup log exists and is recent (<30 minutes old)
- No ERROR lines in backup log
- ZFS replication status (FileServer and Downloads)
- Backup completion messages

**Success criteria:**
- Log file timestamp within last 30 minutes
- No errors in log
- ZFS replication state is "FINISHED"
- Proxmox backups completed successfully

**Alert examples:**

*Success:*
```
Title: ✅ HomeLab Backups Complete
Message: All backups completed successfully
- ZFS Replication: FINISHED (923 GB)
- Proxmox Backups: Success
- Duration: ~90 minutes
Priority: 3
```

*Failure:*
```
Title: 🚨 HomeLab Backup Failed
Message: Backup errors detected!
⚠️ ERROR: backup job failed
⚠️ ZFS replication: FAILED
Priority: 5
```

### 2. Heartbeat Sender

**Script:** `/usr/local/bin/send-heartbeat.sh` (pve-scratchy)

**Schedule:** Every 15 minutes
```bash
*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/heartbeat.log 2>&1
```

**Function:**
```bash
#!/bin/bash
REMOTE_HOST="root@www.perrett.tech"
HEARTBEAT_FILE="/opt/homelab-monitor/homelab-heartbeat.txt"

TIMESTAMP=$(date +%s)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_HOST \
    "echo $TIMESTAMP > $HEARTBEAT_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "$(date): Heartbeat sent successfully"
else
    echo "$(date): Failed to send heartbeat"
fi
```

**Authentication:** SSH key at `/root/.ssh/id_rsa` (no password required)

**Heartbeat format:** Unix timestamp (seconds since epoch)

### 3. Heartbeat Monitor (External)

**Script:** `/opt/homelab-monitor/check-homelab.sh` (perrett.tech)

**Schedule:** Every 15 minutes
```bash
*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1
```

**Function:**
```bash
#!/bin/bash
HEARTBEAT_FILE="/opt/homelab-monitor/homelab-heartbeat.txt"
NTFY_TOPIC="homelab-backup-alerts-dp"
MAX_AGE_MINUTES=30

if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "No heartbeat file - waiting for first check-in"
    exit 0
fi

LAST_HEARTBEAT=$(cat "$HEARTBEAT_FILE")
CURRENT_TIME=$(date +%s)
AGE_MINUTES=$(( ($CURRENT_TIME - $LAST_HEARTBEAT) / 60 ))

if [ $AGE_MINUTES -gt $MAX_AGE_MINUTES ]; then
    echo "$(date): Last heartbeat $AGE_MINUTES minutes ago"
    echo "ALERT SENT: Offline for $AGE_MINUTES minutes"

    curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
        -H "Title: 🚨 Homelab Offline" \
        -H "Priority: 5" \
        -H "Tags: warning,skull" \
        -d "⚠️ Homelab has not checked in for $AGE_MINUTES minutes. Last heartbeat: $(date -d @$LAST_HEARTBEAT)" \
        > /dev/null
else
    echo "$(date): Heartbeat OK (age: $AGE_MINUTES minutes)"
fi
```

**Alert threshold:** 30 minutes (allows 2 missed heartbeats)

**Alert example:**
```
Title: 🚨 Homelab Offline
Message: ⚠️ Homelab has not checked in for 35 minutes.
Last heartbeat: Sun Nov 16 12:00:00 AEDT 2025
Priority: 5
Tags: warning,skull
```

---

## Manual Operations

### Check Monitoring Status

**On pve-scratchy:**
```bash
# Check backup monitoring status
tail -50 /var/log/backup-monitoring.log

# Check heartbeat sending
tail -50 /var/log/heartbeat.log

# View last 10 heartbeat attempts
tail -10 /var/log/heartbeat.log

# Check if cron jobs are running
crontab -l | grep -E "check-backup|send-heartbeat"

# Test heartbeat manually
/usr/local/bin/send-heartbeat.sh

# Test backup monitoring manually
/usr/local/bin/check-backup-status-ntfy.sh
```

**On perrett.tech:**
```bash
# SSH from homelab
ssh root@www.perrett.tech

# Check monitoring logs
tail -50 /var/log/homelab-monitor.log

# Check heartbeat file
cat /opt/homelab-monitor/homelab-heartbeat.txt

# Calculate age of last heartbeat
echo "Last heartbeat: $(date -d @$(cat /opt/homelab-monitor/homelab-heartbeat.txt))"

# Test monitoring manually
/opt/homelab-monitor/check-homelab.sh

# Check cron job
crontab -l | grep check-homelab
```

### Send Test Alerts

**Test ntfy.sh directly:**
```bash
# From any system
curl -X POST "https://ntfy.sh/homelab-backup-alerts-dp" \
    -H "Title: Test Alert" \
    -H "Priority: 3" \
    -H "Tags: information_source" \
    -d "This is a test notification"
```

**Test backup monitoring:**
```bash
# From pve-scratchy
/usr/local/bin/check-backup-status-ntfy.sh
```

**Test heartbeat monitoring:**
```bash
# From pve-scratchy
/usr/local/bin/send-heartbeat.sh
```

### Chaos Monkey Test

**Synthetic deadman switch test:**
```bash
# From pve-scratchy
/tmp/test-deadman-switch.sh
```

This test:
1. Backs up current heartbeat
2. Sets fake old timestamp (35 minutes ago)
3. Triggers monitoring check
4. Sends alert (you should receive notification)
5. Restores original heartbeat
6. Clears alert state

**Expected:** Alert notification on your device within seconds

---

## Troubleshooting

### No Alerts Received

**Check ntfy.sh subscription:**
```bash
# Verify topic subscription in ntfy.sh app
# Topic: homelab-backup-alerts-dp

# Test alert manually
curl -X POST "https://ntfy.sh/homelab-backup-alerts-dp" \
    -H "Title: Test" \
    -d "Testing notifications"
```

**If test works but automated alerts don't:**
1. Check cron jobs are running:
   ```bash
   # On pve-scratchy
   systemctl status cron
   crontab -l

   # On perrett.tech
   systemctl status cron
   crontab -l
   ```

2. Check script execution:
   ```bash
   # Run scripts manually
   /usr/local/bin/check-backup-status-ntfy.sh
   /usr/local/bin/send-heartbeat.sh
   ```

3. Check log files for errors:
   ```bash
   tail -100 /var/log/backup-monitoring.log
   tail -100 /var/log/heartbeat.log
   ```

**If ntfy.sh app not receiving:**
- Check app permissions (notifications enabled)
- Verify internet connectivity on mobile device
- Try web interface: https://ntfy.sh/homelab-backup-alerts-dp
- Check ntfy.sh service status: https://ntfy.sh/stats

### Heartbeat Not Sending

**Symptoms:**
- Offline alerts even when homelab is running
- `/var/log/heartbeat.log` shows "Failed to send heartbeat"

**Diagnosis:**
```bash
# On pve-scratchy
# Test SSH connectivity
ssh -v root@www.perrett.tech "echo 'Connection successful'"

# Check SSH key
ls -la /root/.ssh/id_rsa*

# Test heartbeat manually with debug
bash -x /usr/local/bin/send-heartbeat.sh
```

**Common causes:**

1. **SSH key authentication failed:**
   ```bash
   # Regenerate SSH key
   ssh-keygen -t rsa -b 4096 -f /root/.ssh/id_rsa -N ""

   # Copy public key
   cat /root/.ssh/id_rsa.pub

   # Add to perrett.tech:/root/.ssh/authorized_keys
   ```

2. **Network connectivity issues:**
   ```bash
   # Check if perrett.tech is reachable
   ping -c 3 www.perrett.tech

   # Check DNS resolution
   nslookup www.perrett.tech

   # Check Tailscale VPN
   tailscale status
   ```

3. **Firewall blocking SSH:**
   ```bash
   # On perrett.tech - check SSH is listening
   netstat -tlnp | grep :22

   # Check firewall rules
   iptables -L -n | grep 22
   ```

**Fix:**
```bash
# Re-establish SSH key trust
ssh-copy-id root@www.perrett.tech
# OR manually add key to authorized_keys

# Test connection
ssh root@www.perrett.tech "date"

# If successful, heartbeat should work
/usr/local/bin/send-heartbeat.sh
```

### Heartbeat Monitoring Not Working

**Symptoms:**
- No offline alerts even after stopping heartbeat
- Monitor script not running

**Diagnosis:**
```bash
# On perrett.tech
# Check if monitoring script exists
ls -la /opt/homelab-monitor/check-homelab.sh

# Check if executable
[ -x /opt/homelab-monitor/check-homelab.sh ] && echo "Executable" || echo "Not executable"

# Check heartbeat file
cat /opt/homelab-monitor/homelab-heartbeat.txt

# Run monitor manually
bash -x /opt/homelab-monitor/check-homelab.sh

# Check cron
crontab -l | grep check-homelab
```

**Common causes:**

1. **Script not executable:**
   ```bash
   chmod +x /opt/homelab-monitor/check-homelab.sh
   ```

2. **Cron job not installed:**
   ```bash
   # Add cron job
   (crontab -l 2>/dev/null; echo "*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1") | crontab -
   ```

3. **Heartbeat file missing:**
   ```bash
   # Create directory
   mkdir -p /opt/homelab-monitor

   # Set permissions
   chmod 755 /opt/homelab-monitor

   # Wait for next heartbeat or send manually
   ```

4. **curl not installed:**
   ```bash
   # Install curl
   apt-get update && apt-get install -y curl
   ```

### Backup Monitoring Not Working

**Symptoms:**
- No daily 6 AM alerts
- Log file shows errors

**Diagnosis:**
```bash
# On pve-scratchy
# Check script exists
ls -la /usr/local/bin/check-backup-status-ntfy.sh

# Check backup log exists
ls -la /var/log/wake-backup-shutdown.log

# Run monitoring manually
bash -x /usr/local/bin/check-backup-status-ntfy.sh

# Check cron job
crontab -l | grep check-backup
```

**Common causes:**

1. **Backup didn't run:**
   ```bash
   # Check backup script
   ls -la /usr/local/bin/wake-backup-shutdown-v2.sh

   # Check backup cron
   crontab -l | grep wake-backup

   # Check last backup run
   tail -100 /var/log/wake-backup-shutdown.log
   ```

2. **ZFS replication check failing:**
   ```bash
   # Test TrueNAS API access
   ssh root@10.16.1.6 "midclt call replication.query | jq '.[0].state'"

   # If SSH fails, check TrueNAS primary (VM 110)
   qm list | grep 110
   ```

3. **Log file too old:**
   ```bash
   # Check backup log timestamp
   stat /var/log/wake-backup-shutdown.log

   # If older than 24 hours, backup didn't run
   # Check standby host (pve-itchy) is responding
   ping -c 3 10.16.1.8

   # Check WOL is working
   wakeonlan 60:45:cb:69:85:83
   ```

**Fix:**
```bash
# Re-run backup manually
/usr/local/bin/wake-backup-shutdown-v2.sh

# After successful backup, monitoring should work
/usr/local/bin/check-backup-status-ntfy.sh
```

### False Positive Offline Alerts

**Symptoms:**
- Receiving offline alerts but homelab is running
- Heartbeat is being sent but monitoring doesn't see it

**Diagnosis:**
```bash
# On pve-scratchy - check heartbeat is sending
tail -20 /var/log/heartbeat.log

# Should see "Heartbeat sent successfully" every 15 minutes

# On perrett.tech - check heartbeat file
cat /opt/homelab-monitor/homelab-heartbeat.txt
echo "Age: $(( ($(date +%s) - $(cat /opt/homelab-monitor/homelab-heartbeat.txt)) / 60 )) minutes"

# Check monitoring log
tail -20 /var/log/homelab-monitor.log
```

**Common causes:**

1. **Time sync issues:**
   ```bash
   # On both systems
   date

   # Check NTP sync
   timedatectl status

   # If out of sync, sync time
   systemctl restart systemd-timesyncd
   ```

2. **Heartbeat file permissions:**
   ```bash
   # On perrett.tech
   ls -la /opt/homelab-monitor/homelab-heartbeat.txt

   # Should be readable by root
   chmod 644 /opt/homelab-monitor/homelab-heartbeat.txt
   ```

3. **Monitoring threshold too low:**
   ```bash
   # Edit check-homelab.sh
   # Change MAX_AGE_MINUTES=30 to higher value if needed
   # Example: MAX_AGE_MINUTES=45
   ```

### Alert Flood / Too Many Notifications

**Symptoms:**
- Multiple alerts every 15 minutes
- Alert fatigue

**Causes:**
1. **Persistent offline condition** - Homelab actually offline
2. **Heartbeat sending failed** - Network or SSH issues
3. **Alert state not clearing** - Monitoring continues alerting

**Fix for alert flood:**
```bash
# On perrett.tech - add alert cooldown to monitoring script
# Edit /opt/homelab-monitor/check-homelab.sh

# Add alert tracking (add after NTFY_TOPIC line):
ALERT_FILE="/opt/homelab-monitor/last-alert.txt"

# Modify alert section to only alert once per hour:
if [ $AGE_MINUTES -gt $MAX_AGE_MINUTES ]; then
    # Check if we already alerted recently
    if [ -f "$ALERT_FILE" ]; then
        LAST_ALERT=$(cat "$ALERT_FILE")
        ALERT_AGE=$(( ($CURRENT_TIME - $LAST_ALERT) / 60 ))

        if [ $ALERT_AGE -lt 60 ]; then
            echo "$(date): Already alerted $ALERT_AGE minutes ago, skipping"
            exit 0
        fi
    fi

    # Send alert
    curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" ...

    # Record alert time
    echo "$CURRENT_TIME" > "$ALERT_FILE"
fi
```

**Temporary silence:**
```bash
# Disable monitoring temporarily (on perrett.tech)
crontab -l > /tmp/cron.backup
crontab -l | grep -v check-homelab | crontab -

# Re-enable later
crontab /tmp/cron.backup
```

### Backup Success Alert Not Sent

**Symptoms:**
- Backups complete successfully
- No success alert at 6 AM

**Diagnosis:**
```bash
# Check monitoring script ran
grep "$(date +%Y-%m-%d)" /var/log/backup-monitoring.log

# Check backup log has success indicators
grep -i "success\|complete" /var/log/wake-backup-shutdown.log | tail -10

# Run monitoring manually
/usr/local/bin/check-backup-status-ntfy.sh
```

**Common causes:**

1. **Backup log indicates issues:**
   ```bash
   # Check for warnings or errors
   grep -i "error\|warn\|fail" /var/log/wake-backup-shutdown.log | tail -20

   # If issues found, monitoring correctly didn't send success alert
   # Fix backup issues first
   ```

2. **ZFS replication not finished:**
   ```bash
   # Check TrueNAS replication status
   ssh root@10.16.1.6 "midclt call replication.query | jq '.[] | {name: .name, state: .state}'"

   # If state is not "FINISHED", monitoring waits
   ```

3. **Monitoring script logic error:**
   ```bash
   # Run with debug
   bash -x /usr/local/bin/check-backup-status-ntfy.sh 2>&1 | tee /tmp/monitor-debug.log

   # Check for logic issues in output
   ```

---

## Maintenance

### Update Scripts

**Backup monitoring:**
```bash
# Edit script on pve-scratchy
nano /usr/local/bin/check-backup-status-ntfy.sh

# Test changes
/usr/local/bin/check-backup-status-ntfy.sh

# No restart needed (cron will use new version)
```

**Heartbeat sender:**
```bash
# Edit script on pve-scratchy
nano /usr/local/bin/send-heartbeat.sh

# Test changes
/usr/local/bin/send-heartbeat.sh

# No restart needed
```

**Heartbeat monitor:**
```bash
# SSH to perrett.tech
ssh root@www.perrett.tech

# Edit script
nano /opt/homelab-monitor/check-homelab.sh

# Test changes
/opt/homelab-monitor/check-homelab.sh

# No restart needed
```

### Change Alert Thresholds

**Heartbeat timeout (default: 30 minutes):**
```bash
# On perrett.tech
nano /opt/homelab-monitor/check-homelab.sh

# Change line:
MAX_AGE_MINUTES=30
# To desired value (e.g., 45 for 45 minutes)
```

**Backup log age (default: 30 minutes):**
```bash
# On pve-scratchy
nano /usr/local/bin/check-backup-status-ntfy.sh

# Change line:
MAX_AGE_MINUTES=30
# To desired value
```

### Change Alert Frequency

**Heartbeat check interval (default: every 15 minutes):**
```bash
# On pve-scratchy
crontab -e

# Change line:
*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/heartbeat.log 2>&1
# To desired interval (e.g., */30 for every 30 minutes)

# On perrett.tech
crontab -e

# Change line:
*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1
# To same interval as heartbeat sender
```

**Backup monitoring time (default: 6:00 AM):**
```bash
# On pve-scratchy
crontab -e

# Change line:
0 6 * * * /usr/local/bin/check-backup-status-ntfy.sh >> /var/log/backup-monitoring.log 2>&1
# To desired time (e.g., 0 7 for 7:00 AM)
```

### View Historical Alerts

**Via ntfy.sh web:**
```
https://ntfy.sh/homelab-backup-alerts-dp
```

Shows recent alerts (last ~24 hours cached by ntfy.sh)

**Via local logs:**
```bash
# Backup monitoring history
grep -E "ALERT|SUCCESS" /var/log/backup-monitoring.log | tail -50

# Heartbeat history
tail -100 /var/log/heartbeat.log

# Offline alerts (on perrett.tech)
grep "ALERT SENT" /var/log/homelab-monitor.log
```

### Rotate Log Files

**Setup log rotation:**
```bash
# On pve-scratchy
cat > /etc/logrotate.d/homelab-monitoring << 'EOF'
/var/log/backup-monitoring.log
/var/log/heartbeat.log
{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF

# On perrett.tech
cat > /etc/logrotate.d/homelab-monitoring << 'EOF'
/var/log/homelab-monitor.log
{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### Disable Monitoring Temporarily

**For maintenance window:**
```bash
# On pve-scratchy - disable both monitoring types
crontab -l > /tmp/cron.backup
crontab -l | grep -v -E "check-backup|send-heartbeat" | crontab -

# On perrett.tech - disable heartbeat monitoring
crontab -l > /tmp/cron.backup
crontab -l | grep -v check-homelab | crontab -

# After maintenance, restore
# On both systems:
crontab /tmp/cron.backup
```

**Silent alert for known outage:**
```bash
# Send manual "maintenance mode" notification
curl -X POST "https://ntfy.sh/homelab-backup-alerts-dp" \
    -H "Title: 🔧 Maintenance Mode" \
    -H "Priority: 2" \
    -H "Tags: tools" \
    -d "Homelab entering maintenance. Monitoring disabled until $(date -d '+4 hours' +'%H:%M')"
```

---

## Testing & Validation

### Monthly Validation Checklist

**Test all monitoring functions:**

1. **Backup monitoring:**
   ```bash
   /usr/local/bin/check-backup-status-ntfy.sh
   # Verify alert received
   ```

2. **Heartbeat sending:**
   ```bash
   /usr/local/bin/send-heartbeat.sh
   tail -5 /var/log/heartbeat.log
   # Should show "successfully" message
   ```

3. **Heartbeat monitoring:**
   ```bash
   ssh root@www.perrett.tech "/opt/homelab-monitor/check-homelab.sh"
   # Should show "Heartbeat OK"
   ```

4. **Chaos monkey test:**
   ```bash
   /tmp/test-deadman-switch.sh
   # Verify offline alert received
   ```

5. **Check cron jobs:**
   ```bash
   # On pve-scratchy
   crontab -l

   # On perrett.tech
   ssh root@www.perrett.tech "crontab -l"
   ```

6. **Verify log rotation:**
   ```bash
   ls -lh /var/log/*monitoring*.gz
   ls -lh /var/log/heartbeat*.gz
   ```

**Expected results:**
- ✅ All alerts received within 30 seconds
- ✅ All scripts execute without errors
- ✅ Cron jobs present and correct
- ✅ Logs rotating properly

---

## Emergency Procedures

### Complete Monitoring Failure

**If no alerts for >24 hours:**

1. **Check homelab is online:**
   ```bash
   ping -c 3 10.16.1.22
   ssh root@10.16.1.22 "uptime"
   ```

2. **Check all monitoring components:**
   ```bash
   # Cron running?
   ssh root@10.16.1.22 "systemctl status cron"

   # Scripts present?
   ssh root@10.16.1.22 "ls -la /usr/local/bin/*backup*.sh /usr/local/bin/send-heartbeat.sh"

   # Logs show activity?
   ssh root@10.16.1.22 "tail -20 /var/log/heartbeat.log"
   ```

3. **Check external monitor:**
   ```bash
   ssh root@www.perrett.tech "systemctl status cron"
   ssh root@www.perrett.tech "tail -20 /var/log/homelab-monitor.log"
   ```

4. **Test ntfy.sh:**
   ```bash
   curl -X POST "https://ntfy.sh/homelab-backup-alerts-dp" \
       -H "Title: Test" \
       -d "Testing emergency alert"
   ```

5. **Rebuild if needed:**
   - Re-deploy scripts from `/Users/dp/developerland/homelab/` documentation
   - Re-establish SSH keys
   - Re-install cron jobs
   - Run validation tests

### Migrate to New External Monitor

**If perrett.tech unavailable:**

1. **Setup new external server:**
   ```bash
   # On new server
   mkdir -p /opt/homelab-monitor

   # Copy monitoring script
   scp root@www.perrett.tech:/opt/homelab-monitor/check-homelab.sh /opt/homelab-monitor/

   # Install cron job
   (crontab -l 2>/dev/null; echo "*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1") | crontab -
   ```

2. **Update homelab sender:**
   ```bash
   # On pve-scratchy
   # Edit send-heartbeat.sh
   nano /usr/local/bin/send-heartbeat.sh

   # Change REMOTE_HOST to new server
   REMOTE_HOST="root@new-server.example.com"

   # Setup SSH key
   ssh-copy-id root@new-server.example.com
   ```

3. **Test new setup:**
   ```bash
   /usr/local/bin/send-heartbeat.sh
   ssh root@new-server.example.com "cat /opt/homelab-monitor/homelab-heartbeat.txt"
   ```

### Switch to Gotify

**If ntfy.sh unavailable or prefer self-hosted:**

1. **Gotify is already installed:**
   - URL: http://10.16.1.4:8085
   - User: admin
   - Password: Getmassiv3

2. **Create application token:**
   - Login to Gotify web UI
   - Go to "Apps" → "Create Application"
   - Name: "HomeLab Monitoring"
   - Copy token

3. **Update monitoring scripts:**
   ```bash
   # Replace ntfy.sh calls with Gotify
   # Change:
   curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
       -H "Title: $title" \
       -d "$message"

   # To:
   GOTIFY_TOKEN="your-token-here"
   GOTIFY_URL="http://10.16.1.4:8085"
   curl -s -X POST "$GOTIFY_URL/message?token=$GOTIFY_TOKEN" \
       -F "title=$title" \
       -F "message=$message" \
       -F "priority=5"
   ```

4. **Limitations:**
   - Requires VPN/internal network access
   - No external alerts if network down
   - Consider keeping ntfy.sh for external monitoring

---

## Performance & Costs

### Resource Usage

**Monitoring overhead:**
- CPU: <0.1% average
- Memory: ~10 MB total (scripts + logs)
- Network: ~1 KB per heartbeat (96 KB/day)
- Storage: ~100 KB/day logs (3 MB/month)

**External monitoring (perrett.tech):**
- CPU: <0.01%
- Memory: ~5 MB
- Storage: ~50 KB/day logs
- Bandwidth: Negligible

### Cost Analysis

**ntfy.sh (free tier):**
- Cost: $0/month
- Unlimited notifications
- 24 hour message retention
- No registration required

**Gotify (self-hosted):**
- Cost: $0/month (runs on existing VM 100)
- Unlimited notifications
- Permanent message storage
- Requires VPN for external access

**Total monitoring cost:** $0/month

---

## Related Documentation

- [README.md](README.md) - HomeLab overview
- [INTEGRATED_BACKUP_SYSTEM.md](INTEGRATED_BACKUP_SYSTEM.md) - Backup architecture
- [PHASE7_AUTOMATION_COMPLETE.md](PHASE7_AUTOMATION_COMPLETE.md) - WOL automation
- [DOCKER_UPDATES_2025-11-15.md](DOCKER_UPDATES_2025-11-15.md) - Docker container management

---

## Support & Contact

**ntfy.sh Support:**
- Website: https://ntfy.sh
- Docs: https://docs.ntfy.sh
- Status: https://ntfy.sh/stats

**Gotify Support:**
- GitHub: https://github.com/gotify/server
- Docs: https://gotify.net/docs

**For homelab-specific issues:**
- Check logs first
- Run validation tests
- Consult troubleshooting section above

---

**Status:** ✅ Fully operational
**Last Updated:** 2025-11-16
**Last Validated:** 2025-11-16 (chaos monkey test passed)
**Next Review:** 2025-12-16 (30-day validation)
