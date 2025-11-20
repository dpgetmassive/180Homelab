# Homelab Heartbeat Monitoring System

**Status:** ✅ Active (v2.0 - with recovery notifications)
**Created:** 2025-11-16
**Last Updated:** 2025-11-17
**Maintainer:** DevOps

---

## Overview

A **dead-simple heartbeat monitoring system** that alerts via ntfy when the homelab stops responding. Uses SSH-based heartbeat checks every 15 minutes with a 30-minute grace period.

### Why This Design?

- **Minimal dependencies:** Just SSH and cron
- **No external services:** No Cloudflare Tunnels, no TLS certificates, no complex routing
- **Easy to debug:** Two bash scripts, two cron jobs, one timestamp file
- **Predictable:** If SSH works, monitoring works

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Homelab (pve-scratchy @ 10.16.1.22)                        │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Cron: */15 * * * *                                │    │
│  │  /usr/local/bin/send-heartbeat.sh                  │    │
│  │                                                     │    │
│  │  • Generates timestamp                              │    │
│  │  • SSH to www.perrett.tech                         │    │
│  │  • Writes timestamp to remote file                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │ SSH every 15 min
                       │ (writes timestamp)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  External Monitor (www.perrett.tech)                         │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  /opt/homelab-monitor/homelab-heartbeat.txt        │    │
│  │  Contains: Unix timestamp of last heartbeat        │    │
│  └────────────────────────────────────────────────────┘    │
│                       ▲                                      │
│                       │ read timestamp                       │
│                       │                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Cron: */15 * * * *                                │    │
│  │  /opt/homelab-monitor/check-homelab.sh             │    │
│  │                                                     │    │
│  │  • Read last heartbeat timestamp                   │    │
│  │  • Calculate age in minutes                        │    │
│  │  • If age > 30 minutes → send ntfy alert          │    │
│  │  • Alert repeats every 15 min while offline       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│                       │ ntfy alert (if offline)              │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  ntfy.sh/homelab-backup-alerts-dp                  │    │
│  │  🚨 Homelab Offline                                │    │
│  │  Priority: 5 (urgent)                              │    │
│  │  Tags: warning,skull                               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Heartbeat Sender (Homelab)

**Location:** `/usr/local/bin/send-heartbeat.sh` on pve-scratchy (10.16.1.22)

```bash
#!/bin/bash
# Homelab Heartbeat - sends check-in to perrett.tech every 15 minutes

REMOTE_HOST="root@www.perrett.tech"
HEARTBEAT_FILE="/opt/homelab-monitor/homelab-heartbeat.txt"

# Send current timestamp to perrett.tech
TIMESTAMP=$(date +%s)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_HOST "echo $TIMESTAMP > $HEARTBEAT_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "$(date): Heartbeat sent successfully"
else
    echo "$(date): Failed to send heartbeat"
fi
```

**Cron Schedule:** `*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1`

**What it does:**
1. Generates Unix timestamp (seconds since epoch)
2. SSH to www.perrett.tech as root
3. Writes timestamp to `/opt/homelab-monitor/homelab-heartbeat.txt`
4. Logs success/failure to `/var/log/homelab-heartbeat.log`

**SSH Key:** Uses root's SSH key on pve-scratchy (no password required)

---

### 2. Heartbeat Monitor (External)

**Location:** `/opt/homelab-monitor/check-homelab.sh` on www.perrett.tech
**Version:** 2.0 (with recovery notifications)

```bash
#!/bin/bash
# Homelab Deadman Switch Monitor v2.0
# Added: Recovery notifications when homelab comes back online
HEARTBEAT_FILE="/opt/homelab-monitor/homelab-heartbeat.txt"
STATE_FILE="/opt/homelab-monitor/last-state.txt"
OFFLINE_SINCE_FILE="/opt/homelab-monitor/offline-since.txt"
NTFY_TOPIC="homelab-backup-alerts-dp"
MAX_AGE_MINUTES=30

if [ ! -f "$HEARTBEAT_FILE" ]; then
    echo "No heartbeat file - waiting for first check-in"
    exit 0
fi

LAST_HEARTBEAT=$(cat "$HEARTBEAT_FILE")
CURRENT_TIME=$(date +%s)
AGE_MINUTES=$(( ($CURRENT_TIME - $LAST_HEARTBEAT) / 60 ))

echo "$(date): Last heartbeat $AGE_MINUTES minutes ago"

# Read previous state (default to "online" if no state file exists)
if [ -f "$STATE_FILE" ]; then
    LAST_STATE=$(cat "$STATE_FILE")
else
    LAST_STATE="online"
fi

if [ $AGE_MINUTES -gt $MAX_AGE_MINUTES ]; then
    # Homelab is offline
    if [ "$LAST_STATE" != "offline" ]; then
        # State transition: online → offline
        echo "$CURRENT_TIME" > "$OFFLINE_SINCE_FILE"
        echo "offline" > "$STATE_FILE"

        curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
            -H "Title: 🚨 Homelab Offline" \
            -H "Priority: 5" \
            -H "Tags: warning,skull" \
            -d "⚠️ Homelab offline for $AGE_MINUTES minutes. Last heartbeat: $(date -d @$LAST_HEARTBEAT "+%Y-%m-%d %H:%M:%S %Z")" > /dev/null
        echo "ALERT SENT: Offline for $AGE_MINUTES minutes (state transition)"
    else
        # Still offline (send periodic reminders)
        curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
            -H "Title: 🚨 Homelab Offline" \
            -H "Priority: 5" \
            -H "Tags: warning,skull" \
            -d "⚠️ Homelab offline for $AGE_MINUTES minutes. Last heartbeat: $(date -d @$LAST_HEARTBEAT "+%Y-%m-%d %H:%M:%S %Z")" > /dev/null
        echo "ALERT SENT: Still offline for $AGE_MINUTES minutes"
    fi
else
    # Homelab is online
    if [ "$LAST_STATE" = "offline" ]; then
        # State transition: offline → online (RECOVERY!)
        echo "online" > "$STATE_FILE"

        # Calculate downtime duration
        if [ -f "$OFFLINE_SINCE_FILE" ]; then
            OFFLINE_SINCE=$(cat "$OFFLINE_SINCE_FILE")
            DOWNTIME_SECONDS=$(( $CURRENT_TIME - $OFFLINE_SINCE ))
            DOWNTIME_MINUTES=$(( $DOWNTIME_SECONDS / 60 ))
            DOWNTIME_HOURS=$(( $DOWNTIME_MINUTES / 60 ))
            DOWNTIME_REMAINING_MINUTES=$(( $DOWNTIME_MINUTES % 60 ))

            if [ $DOWNTIME_HOURS -gt 0 ]; then
                DOWNTIME_TEXT="${DOWNTIME_HOURS}h ${DOWNTIME_REMAINING_MINUTES}m"
            else
                DOWNTIME_TEXT="${DOWNTIME_MINUTES}m"
            fi

            rm -f "$OFFLINE_SINCE_FILE"
        else
            DOWNTIME_TEXT="unknown duration"
        fi

        curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" \
            -H "Title: ✅ Homelab Online" \
            -H "Priority: 3" \
            -H "Tags: white_check_mark,tada" \
            -d "🎉 Homelab is back online! Downtime: $DOWNTIME_TEXT. Last heartbeat: $(date -d @$LAST_HEARTBEAT "+%Y-%m-%d %H:%M:%S %Z")" > /dev/null
        echo "RECOVERY ALERT SENT: Back online after $DOWNTIME_TEXT"
    else
        # Still online (no alert needed)
        echo "online" > "$STATE_FILE"
        echo "Status: Online (healthy)"
    fi
fi
```

**Cron Schedule:** `*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1`

**What it does:**
1. Reads timestamp from `/opt/homelab-monitor/homelab-heartbeat.txt`
2. Calculates age in minutes
3. Tracks previous state (online/offline) in `/opt/homelab-monitor/last-state.txt`
4. If age > 30 minutes:
   - Marks as offline and sends ntfy alert
   - Records offline timestamp for downtime calculation
5. If age < 30 minutes and was previously offline:
   - Sends recovery notification with downtime duration
   - Clears offline timestamp
6. Logs all state transitions and checks to `/var/log/homelab-monitor.log`

**Alert Behavior:**

**Offline Alerts:**
- **Threshold:** 30 minutes (allows for 1 missed heartbeat + grace period)
- **Repeat:** Every 15 minutes while offline
- **Priority:** 5 (urgent)
- **Tags:** warning, skull
- **Title:** 🚨 Homelab Offline

**Recovery Alerts:**
- **Trigger:** When homelab comes back online after being offline
- **Priority:** 3 (moderate)
- **Tags:** white_check_mark, tada
- **Title:** ✅ Homelab Online
- **Includes:** Total downtime duration (e.g., "2h 45m")

---

### 3. Data Storage

**Files on www.perrett.tech:**

#### Heartbeat File
**Path:** `/opt/homelab-monitor/homelab-heartbeat.txt`
**Contents:** Single Unix timestamp (integer)
**Example:**
```
1763377674
```

**Decode timestamp:**
```bash
date -d @1763377674 "+%Y-%m-%d %H:%M:%S %Z"
# Output: 2025-11-17 11:07:54 UTC
```

#### State File
**Path:** `/opt/homelab-monitor/last-state.txt`
**Contents:** Current state ("online" or "offline")
**Purpose:** Track state transitions for recovery detection
**Example:**
```
online
```

#### Offline Since File
**Path:** `/opt/homelab-monitor/offline-since.txt`
**Contents:** Unix timestamp when offline state started
**Purpose:** Calculate total downtime duration for recovery notification
**Lifecycle:** Created when going offline, deleted on recovery
**Example:**
```
1763377674
```

---

## Monitoring Thresholds

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Heartbeat interval** | 15 minutes | Frequent enough for timely alerts, not too chatty |
| **Check interval** | 15 minutes | Matches heartbeat frequency |
| **Offline threshold** | 30 minutes | Allows for 1 missed heartbeat + grace period |
| **Alert repeat** | Every 15 min | Persistent reminders until fixed |

**Timeline Example:**
- T+0: Homelab goes offline
- T+15: Missed first heartbeat check (monitor: "Last heartbeat 15 minutes ago")
- T+30: Missed second heartbeat check
- T+30: **First offline alert sent** (age > 30 minutes, state changes to "offline")
- T+45: Second offline alert sent
- T+60: Third offline alert sent
- ... continues every 15 minutes until homelab recovers
- T+105: Heartbeat received! (homelab back online)
- T+105: **Recovery alert sent** ("Homelab is back online! Downtime: 1h 45m")
- T+120: Normal operation resumes (no more alerts)

---

## Logs

### Homelab Sender Logs

**Location:** `/var/log/homelab-heartbeat.log` on pve-scratchy

**Example:**
```
Mon Nov 17 10:07:55 PM AEDT 2025: Heartbeat sent successfully
Mon Nov 17 10:15:01 PM AEDT 2025: Heartbeat sent successfully
Mon Nov 17 10:30:01 PM AEDT 2025: Heartbeat sent successfully
```

**View recent logs:**
```bash
ssh root@10.16.1.22 "tail -50 /var/log/homelab-heartbeat.log"
```

---

### External Monitor Logs

**Location:** `/var/log/homelab-monitor.log` on www.perrett.tech

**Example (healthy):**
```
Mon Nov 17 03:45:01 UTC 2025: Last heartbeat 15 minutes ago
Status: Online (healthy)
Mon Nov 17 04:00:01 UTC 2025: Last heartbeat 15 minutes ago
Status: Online (healthy)
Mon Nov 17 04:15:01 UTC 2025: Last heartbeat 15 minutes ago
Status: Online (healthy)
```

**Example (offline):**
```
Mon Nov 17 06:00:01 UTC 2025: Last heartbeat 30 minutes ago
ALERT SENT: Offline for 30 minutes (state transition)
Mon Nov 17 06:15:01 UTC 2025: Last heartbeat 45 minutes ago
ALERT SENT: Still offline for 45 minutes
Mon Nov 17 06:30:01 UTC 2025: Last heartbeat 60 minutes ago
ALERT SENT: Still offline for 60 minutes
```

**Example (recovery):**
```
Mon Nov 17 07:45:01 UTC 2025: Last heartbeat 15 minutes ago
RECOVERY ALERT SENT: Back online after 1h 45m
Mon Nov 17 08:00:01 UTC 2025: Last heartbeat 15 minutes ago
Status: Online (healthy)
```

**View recent logs:**
```bash
ssh root@www.perrett.tech "tail -50 /var/log/homelab-monitor.log"
```

---

## Troubleshooting

### Problem: Getting "Homelab Offline" Alerts

#### Step 1: Check if Heartbeat Sender is Running

```bash
ssh root@10.16.1.22 "crontab -l | grep heartbeat"
```

**Expected output:**
```
*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1
```

**If missing:** Re-add to crontab:
```bash
ssh root@10.16.1.22 "crontab -l | { cat; echo ''; echo '# Homelab heartbeat sender (check-in to www.perrett.tech every 15 minutes)'; echo '*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1'; } | crontab -"
```

#### Step 2: Check Heartbeat Sender Logs

```bash
ssh root@10.16.1.22 "tail -20 /var/log/homelab-heartbeat.log"
```

**Good output:**
```
Mon Nov 17 10:15:01 PM AEDT 2025: Heartbeat sent successfully
```

**Bad output:**
```
Mon Nov 17 10:15:01 PM AEDT 2025: Failed to send heartbeat
```

**If failing:** Check SSH connectivity to www.perrett.tech

#### Step 3: Test SSH Connectivity

```bash
ssh root@10.16.1.22 "ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@www.perrett.tech 'echo test'"
```

**Expected:** `test`

**If failing:**
- Check SSH key: `ssh root@10.16.1.22 "ls -la /root/.ssh/"`
- Check network: `ssh root@10.16.1.22 "ping -c 3 www.perrett.tech"`
- Check DNS: `ssh root@10.16.1.22 "host www.perrett.tech"`

#### Step 4: Check Heartbeat File on External Server

```bash
ssh root@www.perrett.tech "ls -l /opt/homelab-monitor/homelab-heartbeat.txt && cat /opt/homelab-monitor/homelab-heartbeat.txt"
```

**Expected output:**
```
-rw-r--r-- 1 root root 11 Nov 17 11:07 /opt/homelab-monitor/homelab-heartbeat.txt
1763377674
```

**Check timestamp age:**
```bash
ssh root@www.perrett.tech "cat /opt/homelab-monitor/homelab-heartbeat.txt && echo '' && date -d @\$(cat /opt/homelab-monitor/homelab-heartbeat.txt) '+%Y-%m-%d %H:%M:%S %Z' && echo 'Current time:' && date '+%Y-%m-%d %H:%M:%S %Z'"
```

**If timestamp is old (>30 minutes):** Heartbeat sender is not running or failing

#### Step 5: Test Heartbeat Sender Manually

```bash
ssh root@10.16.1.22 "/usr/local/bin/send-heartbeat.sh"
```

**Expected:** `Heartbeat sent successfully`

**Then verify it was received:**
```bash
ssh root@www.perrett.tech "cat /opt/homelab-monitor/homelab-heartbeat.txt && date -d @\$(cat /opt/homelab-monitor/homelab-heartbeat.txt) '+%Y-%m-%d %H:%M:%S %Z'"
```

**Timestamp should match current time (within a few seconds)**

---

### Problem: Not Getting Alerts When Homelab is Offline

#### Step 1: Check Monitor Script is Running

```bash
ssh root@www.perrett.tech "crontab -l | grep homelab"
```

**Expected output:**
```
*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1
```

#### Step 2: Check Monitor Logs

```bash
ssh root@www.perrett.tech "tail -20 /var/log/homelab-monitor.log"
```

**Should show checks every 15 minutes with age calculations**

#### Step 3: Test Monitor Script Manually

```bash
ssh root@www.perrett.tech "/opt/homelab-monitor/check-homelab.sh"
```

**Should output:**
```
Mon Nov 17 11:15:01 UTC 2025: Last heartbeat 7 minutes ago
```

**If age > 30 minutes:**
```
Mon Nov 17 11:15:01 UTC 2025: Last heartbeat 45 minutes ago
ALERT SENT: Offline for 45 minutes
```

#### Step 4: Test ntfy Directly

```bash
curl -X POST "https://ntfy.sh/homelab-backup-alerts-dp" \
    -H "Title: Test Alert" \
    -H "Priority: 3" \
    -H "Tags: test" \
    -d "This is a test alert from troubleshooting"
```

**You should receive a notification immediately**

**If not:** Check your ntfy subscription settings

---

### Problem: Heartbeat Timing Issues

#### Check Both Servers' Clocks

**Homelab:**
```bash
ssh root@10.16.1.22 "date && timedatectl status"
```

**External monitor:**
```bash
ssh root@www.perrett.tech "date && timedatectl status"
```

**Both should:**
- Show correct current time
- Have NTP synchronized: `System clock synchronized: yes`
- Use UTC or consistent timezone

**If clocks are wrong:**
```bash
# Enable NTP
ssh root@10.16.1.22 "timedatectl set-ntp true"
ssh root@www.perrett.tech "timedatectl set-ntp true"

# Force sync
ssh root@10.16.1.22 "systemctl restart systemd-timesyncd"
ssh root@www.perrett.tech "systemctl restart systemd-timesyncd"
```

---

### Problem: Too Many Alerts (Alert Fatigue)

**Current settings:**
- Alert threshold: 30 minutes
- Alert repeat: Every 15 minutes

**Option 1: Increase threshold**

Edit `/opt/homelab-monitor/check-homelab.sh` on www.perrett.tech:
```bash
MAX_AGE_MINUTES=60  # Change from 30 to 60
```

**Option 2: Reduce alert frequency**

Change monitor cron to run every 30 minutes:
```cron
*/30 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1
```

**Option 3: Add alert throttling**

Modify script to only send alert every N checks:
```bash
# Track alert count
ALERT_COUNT_FILE="/opt/homelab-monitor/alert-count.txt"
[ -f "$ALERT_COUNT_FILE" ] && ALERT_COUNT=$(cat "$ALERT_COUNT_FILE") || ALERT_COUNT=0

# Only send every 4th alert (= every hour if checking every 15 min)
if [ $(($ALERT_COUNT % 4)) -eq 0 ]; then
    # Send alert
    curl -s -X POST "https://ntfy.sh/$NTFY_TOPIC" ...
fi

# Increment counter
echo $(($ALERT_COUNT + 1)) > "$ALERT_COUNT_FILE"
```

---

### Problem: Alerts Not Stopping After Homelab Recovers

#### Check Heartbeat is Being Sent

```bash
ssh root@10.16.1.22 "tail -5 /var/log/homelab-heartbeat.log"
```

**Should show recent successful heartbeats (within last 15 minutes)**

#### Check Timestamp File is Fresh

```bash
ssh root@www.perrett.tech "cat /opt/homelab-monitor/homelab-heartbeat.txt && date -d @\$(cat /opt/homelab-monitor/homelab-heartbeat.txt) '+%Y-%m-%d %H:%M:%S %Z' && date '+%Y-%m-%d %H:%M:%S %Z'"
```

**Timestamp should be within last 15-30 minutes**

#### Manual Recovery Test

1. Send heartbeat manually:
```bash
ssh root@10.16.1.22 "/usr/local/bin/send-heartbeat.sh"
```

2. Wait 1 minute for monitor to check (or run manually):
```bash
ssh root@www.perrett.tech "/opt/homelab-monitor/check-homelab.sh"
```

3. Should output: `Last heartbeat N minutes ago` where N < 30

---

## Common Failure Scenarios

### Scenario 1: Cron Job Removed

**Symptom:** No logs in `/var/log/homelab-heartbeat.log` for hours

**Cause:** Crontab edited and heartbeat sender removed

**Fix:**
```bash
ssh root@10.16.1.22 "crontab -l | { cat; echo '*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1'; } | crontab -"
```

**Prevention:** Document crontab changes, use version control for cron configs

---

### Scenario 2: SSH Key Lost/Changed

**Symptom:** Heartbeat logs show `Failed to send heartbeat`

**Cause:** SSH key on pve-scratchy doesn't match authorized_keys on www.perrett.tech

**Diagnosis:**
```bash
ssh root@10.16.1.22 "ssh -v root@www.perrett.tech 'echo test' 2>&1 | grep -i 'permission denied\|authentication'"
```

**Fix:**
1. Generate new key on pve-scratchy (if needed):
```bash
ssh root@10.16.1.22 "ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ''"
```

2. Copy to www.perrett.tech:
```bash
ssh root@10.16.1.22 "cat /root/.ssh/id_ed25519.pub" | ssh root@www.perrett.tech "mkdir -p /root/.ssh && cat >> /root/.ssh/authorized_keys"
```

3. Test:
```bash
ssh root@10.16.1.22 "ssh root@www.perrett.tech 'echo success'"
```

---

### Scenario 3: Network Outage

**Symptom:** Alerts start exactly when internet/WAN fails

**Cause:** Homelab can't reach www.perrett.tech

**Expected behavior:** This is working as designed - alerts mean homelab is unreachable

**If false positive (network is fine):**
- Check firewall rules on homelab
- Check ISP routing: `ssh root@10.16.1.22 "traceroute www.perrett.tech"`
- Check DNS: `ssh root@10.16.1.22 "host www.perrett.tech"`

---

### Scenario 4: www.perrett.tech Down/Rebooted

**Symptom:** Monitor stops checking, no alerts even if homelab goes down

**Diagnosis:**
```bash
ssh root@www.perrett.tech "systemctl status cron && crontab -l"
```

**Fix:** Cron should auto-start on boot, but verify:
```bash
ssh root@www.perrett.tech "systemctl enable cron && systemctl start cron"
```

---

### Scenario 5: Disk Full on www.perrett.tech

**Symptom:** Monitor stops logging, may stop working

**Diagnosis:**
```bash
ssh root@www.perrett.tech "df -h / && du -sh /var/log /opt/homelab-monitor"
```

**Fix:**
```bash
# Truncate log files
ssh root@www.perrett.tech "truncate -s 0 /var/log/homelab-monitor.log"

# Set up log rotation
ssh root@www.perrett.tech "cat > /etc/logrotate.d/homelab-monitor << 'EOF'
/var/log/homelab-monitor.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
"
```

---

## Maintenance

### Log Rotation

**Homelab sender logs:**
```bash
# Create logrotate config on pve-scratchy
ssh root@10.16.1.22 "cat > /etc/logrotate.d/homelab-heartbeat << 'EOF'
/var/log/homelab-heartbeat.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
"
```

**External monitor logs:**
```bash
# Create logrotate config on www.perrett.tech
ssh root@www.perrett.tech "cat > /etc/logrotate.d/homelab-monitor << 'EOF'
/var/log/homelab-monitor.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
EOF
"
```

---

### Viewing Status at a Glance

**One-liner health check:**
```bash
echo "=== Homelab Heartbeat Status ===" && \
ssh root@10.16.1.22 "echo 'Sender cron:' && crontab -l | grep heartbeat && echo 'Last send:' && tail -1 /var/log/homelab-heartbeat.log" && \
ssh root@www.perrett.tech "echo 'Monitor cron:' && crontab -l | grep homelab && echo 'Heartbeat age:' && echo \$(( (\$(date +%s) - \$(cat /opt/homelab-monitor/homelab-heartbeat.txt)) / 60 )) minutes && echo 'Last check:' && tail -1 /var/log/homelab-monitor.log"
```

**Expected output:**
```
=== Homelab Heartbeat Status ===
Sender cron:
*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1
Last send:
Mon Nov 17 10:15:01 PM AEDT 2025: Heartbeat sent successfully
Monitor cron:
*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1
Heartbeat age:
7 minutes
Last check:
Mon Nov 17 11:08:01 UTC 2025: Last heartbeat 8 minutes ago
```

---

## Testing

### End-to-End Test

1. **Stop the heartbeat sender** (simulate homelab offline):
```bash
ssh root@10.16.1.22 "crontab -l | grep -v 'send-heartbeat.sh' | crontab -"
```

2. **Wait 35 minutes** (30 min threshold + 5 min buffer)

3. **Should receive ntfy alert:** "🚨 Homelab Offline"

4. **Re-enable heartbeat sender:**
```bash
ssh root@10.16.1.22 "crontab -l | { cat; echo '*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1'; } | crontab -"
```

5. **Send heartbeat manually** (don't wait 15 min):
```bash
ssh root@10.16.1.22 "/usr/local/bin/send-heartbeat.sh"
```

6. **Wait 15 minutes** for next monitor check

7. **Alerts should stop**

---

### Quick Test (Fast Failure)

**Temporarily reduce threshold for testing:**

```bash
# On www.perrett.tech, edit monitor script
ssh root@www.perrett.tech "sed -i 's/MAX_AGE_MINUTES=30/MAX_AGE_MINUTES=2/' /opt/homelab-monitor/check-homelab.sh"

# Stop heartbeat sender
ssh root@10.16.1.22 "crontab -l | grep -v 'send-heartbeat.sh' | crontab -"

# Wait 3 minutes

# Run monitor manually
ssh root@www.perrett.tech "/opt/homelab-monitor/check-homelab.sh"

# Should send alert immediately

# Restore normal threshold
ssh root@www.perrett.tech "sed -i 's/MAX_AGE_MINUTES=2/MAX_AGE_MINUTES=30/' /opt/homelab-monitor/check-homelab.sh"

# Re-enable heartbeat
ssh root@10.16.1.22 "crontab -l | { cat; echo '*/15 * * * * /usr/local/bin/send-heartbeat.sh >> /var/log/homelab-heartbeat.log 2>&1'; } | crontab -"
ssh root@10.16.1.22 "/usr/local/bin/send-heartbeat.sh"
```

---

## Known Limitations

1. **Single point of monitoring:** If www.perrett.tech goes down, no monitoring
   - **Mitigation:** Use a reliable external VPS with high uptime SLA
   - **Alternative:** Add secondary monitor on different provider

2. **SSH dependency:** Requires SSH connectivity and key authentication
   - **Mitigation:** Keep SSH keys secure and backed up
   - **Alternative:** Use API-based heartbeat (webhook to perrett.tech endpoint)

3. **30-minute detection window:** Minimum 30 min before first alert
   - **Why:** Prevents false positives from transient network issues
   - **Trade-off:** Faster detection = more false alarms

4. **Alert fatigue:** Repeated alerts every 15 min while offline
   - **Mitigation:** Implement alert throttling or escalation
   - **Best practice:** Fix quickly to stop alerts

5. **No detailed diagnostics:** Only knows "online" or "offline", not what failed
   - **By design:** Simplicity over granularity
   - **Alternative:** Add Uptime Kuma or Prometheus for detailed monitoring

---

## Disaster Recovery

### Recreate on New External Server

If www.perrett.tech is destroyed/replaced:

1. **Create monitoring directory:**
```bash
ssh root@NEW_SERVER "mkdir -p /opt/homelab-monitor"
```

2. **Install monitor script:**
```bash
ssh root@NEW_SERVER "cat > /opt/homelab-monitor/check-homelab.sh << 'EOF'
#!/bin/bash
HEARTBEAT_FILE=\"/opt/homelab-monitor/homelab-heartbeat.txt\"
NTFY_TOPIC=\"homelab-backup-alerts-dp\"
MAX_AGE_MINUTES=30

if [ ! -f \"\$HEARTBEAT_FILE\" ]; then
    echo \"No heartbeat file - waiting for first check-in\"
    exit 0
fi

LAST_HEARTBEAT=\$(cat \"\$HEARTBEAT_FILE\")
CURRENT_TIME=\$(date +%s)
AGE_MINUTES=\$(( (\$CURRENT_TIME - \$LAST_HEARTBEAT) / 60 ))

echo \"\$(date): Last heartbeat \$AGE_MINUTES minutes ago\"

if [ \$AGE_MINUTES -gt \$MAX_AGE_MINUTES ]; then
    curl -s -X POST \"https://ntfy.sh/\$NTFY_TOPIC\" \\
        -H \"Title: 🚨 Homelab Offline\" \\
        -H \"Priority: 5\" \\
        -H \"Tags: warning,skull\" \\
        -d \"⚠️ Homelab offline for \$AGE_MINUTES minutes. Last heartbeat: \$(date -d @\$LAST_HEARTBEAT \"+%Y-%m-%d %H:%M:%S %Z\")\" > /dev/null
    echo \"ALERT SENT: Offline for \$AGE_MINUTES minutes\"
fi
EOF
"
```

3. **Make executable:**
```bash
ssh root@NEW_SERVER "chmod +x /opt/homelab-monitor/check-homelab.sh"
```

4. **Add to crontab:**
```bash
ssh root@NEW_SERVER "crontab -l | { cat; echo '*/15 * * * * /opt/homelab-monitor/check-homelab.sh >> /var/log/homelab-monitor.log 2>&1'; } | crontab -"
```

5. **Update homelab sender:**
```bash
ssh root@10.16.1.22 "sed -i 's/www.perrett.tech/NEW_SERVER/' /usr/local/bin/send-heartbeat.sh"
```

6. **Test connection:**
```bash
ssh root@10.16.1.22 "/usr/local/bin/send-heartbeat.sh"
```

---

### Backup/Restore

**Backup configuration:**
```bash
# From homelab
ssh root@10.16.1.22 "cat /usr/local/bin/send-heartbeat.sh" > send-heartbeat.sh.backup
ssh root@10.16.1.22 "crontab -l" > crontab-scratchy.backup

# From external monitor
ssh root@www.perrett.tech "cat /opt/homelab-monitor/check-homelab.sh" > check-homelab.sh.backup
ssh root@www.perrett.tech "crontab -l" > crontab-perrett.backup
```

**Restore:**
```bash
# Upload and install scripts
scp send-heartbeat.sh.backup root@10.16.1.22:/usr/local/bin/send-heartbeat.sh
ssh root@10.16.1.22 "chmod +x /usr/local/bin/send-heartbeat.sh"

scp check-homelab.sh.backup root@www.perrett.tech:/opt/homelab-monitor/check-homelab.sh
ssh root@www.perrett.tech "chmod +x /opt/homelab-monitor/check-homelab.sh"

# Restore crontabs
cat crontab-scratchy.backup | ssh root@10.16.1.22 "crontab -"
cat crontab-perrett.backup | ssh root@www.perrett.tech "crontab -"
```

---

## Improvement Ideas (Future)

### Idea 1: HTTP Webhook Instead of SSH

**Current:** SSH connection every 15 minutes
**Alternative:** HTTP POST to webhook endpoint

**Pros:**
- No SSH key management
- Easier to implement from non-Linux systems
- Can add HMAC signature for security

**Cons:**
- Need web server on www.perrett.tech
- More attack surface (exposed endpoint)

**Implementation:**
```bash
# Sender (homelab)
curl -X POST https://www.perrett.tech/heartbeat \
    -H "X-Signature: $(echo -n "$(date +%s)" | openssl sha256 -hmac "$SECRET")" \
    -d "timestamp=$(date +%s)"

# Receiver (www.perrett.tech)
# Simple nginx + php/python script to write timestamp to file
```

---

### Idea 2: Add Response Time Metrics

**Enhancement:** Track how long heartbeat takes to send

```bash
START=$(date +%s%3N)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $REMOTE_HOST "echo $TIMESTAMP > $HEARTBEAT_FILE" 2>/dev/null
END=$(date +%s%3N)
DURATION=$(($END - $START))
echo "$(date): Heartbeat sent successfully (${DURATION}ms)"
```

**Use case:** Detect network degradation before complete failure

---

### Idea 3: Multi-Level Alerting

**Enhancement:** Different alert priorities based on duration

```bash
if [ $AGE_MINUTES -gt 120 ]; then
    PRIORITY=5  # Urgent after 2 hours
elif [ $AGE_MINUTES -gt 60 ]; then
    PRIORITY=4  # High after 1 hour
else
    PRIORITY=3  # Default after 30 min
fi
```

---

### ~~Idea 4: Add "Recovery" Notification~~ ✅ IMPLEMENTED (v2.0)

**Status:** ✅ **Implemented in v2.0 (2025-11-17)**

**What was added:**
- State tracking in `/opt/homelab-monitor/last-state.txt`
- Offline timestamp tracking in `/opt/homelab-monitor/offline-since.txt`
- Recovery notifications when transitioning offline → online
- Downtime duration calculation (e.g., "1h 45m")
- Different alert priorities: 5 (urgent) for offline, 3 (moderate) for recovery

**Example notification:**
```
✅ Homelab Online
🎉 Homelab is back online! Downtime: 1h 45m.
Last heartbeat: 2025-11-17 11:28:19 UTC
```

---

## Related Documentation

- Backup System: `INTEGRATED_BACKUP_SYSTEM.md`
- Monitoring Stack: `MONITORING_SYSTEM.md`
- Cloudflare Tunnel (deprecated for monitoring): `CLOUDFLARE_TUNNEL_FIX_2025-11-17.md`

---

## Change Log

| Date | Change | By |
|------|--------|-----|
| 2025-11-16 | Initial setup (v1.0) | DevOps |
| 2025-11-17 | Heartbeat sender removed from cron, re-added | DevOps |
| 2025-11-17 | Documentation created (v1.0) | DevOps |
| 2025-11-17 | Added recovery notifications (v2.0) | DevOps |

---

## Support

**If monitoring breaks:**
1. Read this doc
2. Follow troubleshooting steps
3. Check logs on both servers
4. Test manually
5. If still broken, check network/SSH/DNS fundamentals

**Emergency disable monitoring:**
```bash
# Stop alerts (comment out monitor cron)
ssh root@www.perrett.tech "crontab -l | sed 's/^*/# */' | crontab -"

# Re-enable
ssh root@www.perrett.tech "crontab -l | sed 's/^# *//' | crontab -"
```

---

**Last validated:** 2025-11-17 22:07 AEDT
**Status:** ✅ Working (heartbeat age < 15 minutes)
