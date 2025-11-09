# Beszel Alerts and Notifications Setup Guide

**Your Options**: Telegram ✅ | n8n (via webhooks) ✅

**Last Updated:** 2025-11-10

---

## Beszel Alert Capabilities

Beszel can alert on:
- **CPU usage** - Percentage threshold
- **Memory usage** - Percentage threshold
- **Disk usage** - Percentage threshold per filesystem
- **Bandwidth** - Network usage spikes
- **Temperature** - CPU/system temperature
- **System status** - Offline/unreachable systems

---

## Supported Notification Channels

### ✅ You Have:
- **Telegram** - Direct native support
- **n8n** - Via webhook (generic HTTP)

### Also Available (All Native):
- **Chat**: Slack, Discord, Teams, Mattermost, Matrix, Zulip
- **Mobile**: Pushover, Pushbullet, Bark
- **Monitoring**: Gotify, Ntfy, OpsGenie
- **Automation**: IFTTT, Home Assistant
- **Enterprise**: Google Chat, Lark
- **Messaging**: Signal, WeCom, Rocketchat
- **Generic**: Webhook (for anything else)

---

## Option 1: Telegram Notifications (Recommended)

### Advantages:
- ✅ Native Beszel support
- ✅ Simple setup (~5 minutes)
- ✅ Mobile notifications
- ✅ Fast and reliable
- ✅ No additional infrastructure needed

### Setup Steps:

#### 1. Create Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send: `/newbot`
3. Follow prompts to create bot
4. **Save the Bot Token** (looks like: `110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`)

#### 2. Get Your Chat ID

**Method A: Using a bot**
1. Search for **@userinfobot** in Telegram
2. Send: `/start`
3. **Save your Chat ID** (looks like: `123456789`)

**Method B: Using your bot**
1. Send any message to your new bot
2. Visit: `https://api.telegram.org/bot<YourBotToken>/getUpdates`
3. Find `"chat":{"id":123456789}` in JSON
4. **Save the Chat ID**

#### 3. Configure in Beszel

1. Open Beszel UI: https://beszel.rova.getmassive.com.au
2. Go to **Settings → Alerts** (or similar section)
3. Click **Add Notification Channel**
4. Select **Telegram**
5. Fill in:
   - **Bot Token**: (from step 1)
   - **Chat ID**: (from step 2)
   - **Name**: `Homelab Telegram` (or your choice)
6. Click **Test** to verify
7. Click **Save**

#### 4. Set Up Alerts

For each critical system, configure alerts:

**Proxmox (pve-rover01)**:
- CPU > 85% for 5 minutes
- Memory > 90% for 5 minutes
- Disk > 90%
- System offline

**Docker Host (rova-docka)**:
- CPU > 80% for 5 minutes
- Memory > 85% for 5 minutes
- Disk > 85% (logs can fill up)
- System offline

**Pi-hole (rova-pihole)**:
- System offline (DNS critical!)
- Memory > 80%

**Plex (rover-plexd)**:
- CPU > 95% for 15 minutes (transcoding spikes are normal)
- Memory > 90%
- System offline

**SABnzbd (rova-sabnzbd)**:
- Disk > 90% (download space)
- System offline

**All Systems**:
- System offline for > 5 minutes

### Example Telegram Message:

```
🚨 ALERT: pve-rover01
CPU usage: 87%
Threshold: 85%
Duration: 6 minutes
Time: 2025-11-10 14:23:45

Status: CRITICAL
```

---

## Option 2: n8n Webhook (Advanced)

### Advantages:
- ✅ Full automation control
- ✅ Can trigger complex workflows
- ✅ Multi-channel notifications (Telegram + others)
- ✅ Data transformation and enrichment
- ✅ Can integrate with other systems

### Use Cases:
- Send to multiple channels (Telegram + Slack)
- Create tickets in ticketing system
- Log alerts to database
- Trigger remediation workflows
- Send different alerts to different people

### Setup Steps:

#### 1. Create n8n Webhook

1. Open n8n: (your n8n URL)
2. Create new workflow: **Beszel Alerts**
3. Add **Webhook** node:
   - **Method**: POST
   - **Path**: `beszel-alerts` (or your choice)
   - **Response**: Return immediately
4. Note the webhook URL (e.g., `https://n8n.example.com/webhook/beszel-alerts`)

#### 2. Add Processing Nodes

**Example Workflow**:

```
Webhook → Filter by Severity → Switch (by system type) → Send Notifications
```

**Sample n8n Workflow**:

1. **Webhook** - Receive alert from Beszel
2. **Set** - Parse/format data
3. **Switch** - Route by severity:
   - Critical → Telegram + SMS
   - Warning → Telegram only
   - Info → Log only
4. **Telegram** - Send notification
5. **HTTP Request** (optional) - Log to external system

#### 3. Configure in Beszel

1. Open Beszel UI
2. Go to **Settings → Alerts**
3. Click **Add Notification Channel**
4. Select **Webhook** (or Generic HTTP)
5. Fill in:
   - **Webhook URL**: (from step 1)
   - **Method**: POST
   - **Headers**:
     ```json
     {
       "Content-Type": "application/json",
       "Authorization": "Bearer <your-secret-token>"
     }
     ```
   - **Name**: `n8n Automation`
6. Click **Test**
7. Click **Save**

#### 4. Beszel Webhook Payload

Beszel will send data like:

```json
{
  "system": "pve-rover01",
  "system_id": "abc123",
  "alert_type": "cpu",
  "metric": "cpu_usage",
  "value": 87.5,
  "threshold": 85,
  "severity": "critical",
  "timestamp": "2025-11-10T14:23:45Z",
  "duration": 360,
  "message": "CPU usage above threshold"
}
```

(Note: Exact payload format may vary - check Beszel docs or test webhook)

#### 5. n8n Processing Example

**Parse and Format**:
```javascript
// In n8n Function node
const alert = $json;
const emoji = alert.severity === 'critical' ? '🚨' : '⚠️';

return {
  message: `${emoji} ALERT: ${alert.system}\n` +
           `${alert.metric}: ${alert.value}%\n` +
           `Threshold: ${alert.threshold}%\n` +
           `Time: ${alert.timestamp}`
};
```

**Send to Telegram**:
Use Telegram node with formatted message.

**Send to Multiple Channels**:
```
Webhook → Parse → [Telegram, Slack, Discord, Email]
```

---

## Recommended Setup: Telegram + n8n Combo

### Best of Both Worlds:

1. **Telegram (Direct)** - For immediate critical alerts
   - System offline alerts
   - Critical thresholds (CPU > 90%, etc.)
   - Fast, no dependency on n8n

2. **n8n Webhook** - For everything else
   - Warning-level alerts
   - Batch notifications
   - Complex workflows
   - Logging and tracking

### Configuration:

**In Beszel**:
- Create two notification channels:
  1. `Telegram Direct` (native Telegram)
  2. `n8n Automation` (webhook)

**Alert Rules**:
- **Critical alerts** → Telegram Direct
- **Warning alerts** → n8n (which can also send to Telegram + log)
- **Info alerts** → n8n only (for logging)

---

## Alert Rule Examples

### Critical Infrastructure

**Proxmox Host (pve-rover01)**:
```
Alert: CPU > 85% for 5 minutes
Notify: Telegram Direct
Severity: Critical

Alert: Memory > 90% for 5 minutes
Notify: Telegram Direct
Severity: Critical

Alert: System offline > 2 minutes
Notify: Telegram Direct
Severity: Critical
```

**Docker Host (rova-docka)**:
```
Alert: Disk > 85%
Notify: Telegram Direct
Severity: Critical
Note: Docker logs can fill disk fast

Alert: Memory > 85% for 10 minutes
Notify: n8n
Severity: Warning
```

**Pi-hole (rova-pihole)**:
```
Alert: System offline > 3 minutes
Notify: Telegram Direct
Severity: Critical
Note: DNS is critical service

Alert: Memory > 80%
Notify: n8n
Severity: Warning
```

### Media Services

**Plex (rover-plexd)**:
```
Alert: CPU > 95% for 20 minutes
Notify: n8n
Severity: Warning
Note: Transcoding spikes are normal, only alert if sustained

Alert: System offline > 10 minutes
Notify: Telegram Direct
Severity: Warning
```

**SABnzbd (rova-sabnzbd)**:
```
Alert: Disk > 90%
Notify: Telegram Direct
Severity: Critical
Note: Download space

Alert: System offline > 5 minutes
Notify: n8n
Severity: Warning
```

**Sonarr/Radarr**:
```
Alert: System offline > 10 minutes
Notify: n8n
Severity: Warning

Alert: Memory > 90%
Notify: n8n
Severity: Warning
```

### Monitoring Systems

**Beszel Hub (rova-beszel)**:
```
Alert: System offline > 2 minutes
Notify: Telegram Direct
Severity: Critical
Note: Monitor the monitor!

Alert: Memory > 80%
Notify: n8n
Severity: Warning
```

**CheckMK (rova-checkmk)**:
```
Alert: System offline > 10 minutes
Notify: n8n
Severity: Warning
Note: Secondary monitoring, less critical
```

---

## Alert Best Practices

### Avoid Alert Fatigue

1. **Set appropriate thresholds** - Not too sensitive
2. **Use duration requirements** - Avoid transient spikes
3. **Prioritize alerts** - Not everything is critical
4. **Group related alerts** - Batch similar notifications
5. **Test thoroughly** - Ensure alerts work before relying on them

### Threshold Guidelines

**CPU**:
- Warning: > 70% for 10 minutes
- Critical: > 85% for 5 minutes

**Memory**:
- Warning: > 80% for 10 minutes
- Critical: > 90% for 5 minutes

**Disk**:
- Warning: > 80%
- Critical: > 90%

**System Offline**:
- Critical: > 5 minutes (for critical systems)
- Warning: > 10 minutes (for non-critical)

### Alert Hierarchy

**Critical** (Telegram Direct):
- System completely offline
- Disk > 90% (data loss risk)
- Critical service down (DNS, firewall, etc.)

**Warning** (n8n → Telegram):
- High resource usage
- Non-critical service down
- Performance degradation

**Info** (n8n → Log only):
- Service restarts
- Threshold recoveries
- Routine events

---

## n8n Workflow Templates

### Template 1: Basic Alert Router

```
1. Webhook (Receive from Beszel)
2. Set (Parse payload)
3. Switch (Route by severity):
   - critical → Telegram
   - warning → Telegram
   - info → No notification
4. Telegram (Send message)
```

### Template 2: Smart Alert with Deduplication

```
1. Webhook
2. Set (Parse and enrich)
3. Redis (Check if already alerted in last hour)
4. IF (Not duplicate):
   - Yes → Continue
   - No → Stop
5. Telegram (Send)
6. Redis (Store alert key)
```

### Template 3: Multi-Channel with Escalation

```
1. Webhook
2. Set (Parse)
3. Switch (By severity):
   - critical → [Telegram + SMS + Create ticket]
   - warning → [Telegram only]
   - info → [Log to database]
4. Wait (15 minutes)
5. Check if still alerting
6. If yes → Escalate (call on-call)
```

---

## Testing Alerts

### Test in Beszel UI

1. Go to notification channel settings
2. Click **Test Notification**
3. Verify message received

### Test from Command Line

Trigger high CPU to test alert:
```bash
ssh pve-rover01
stress-ng --cpu 8 --timeout 60s
```

Watch for alert in ~5-10 minutes (depending on poll interval + duration threshold).

### Test n8n Webhook

```bash
curl -X POST https://n8n.example.com/webhook/beszel-alerts \
  -H "Content-Type: application/json" \
  -d '{
    "system": "test-system",
    "alert_type": "cpu",
    "value": 95,
    "threshold": 85,
    "severity": "critical"
  }'
```

---

## Monitoring the Monitors

Don't forget to alert when monitoring itself fails:

1. **Beszel Hub offline** - Critical alert via external monitoring (e.g., UptimeRobot)
2. **Telegram bot unreachable** - Fallback to n8n webhook
3. **n8n offline** - Fallback to Telegram direct

---

## Next Steps

1. **Choose your approach**:
   - Simple: Telegram only
   - Advanced: Telegram + n8n
   - Hybrid: Telegram for critical, n8n for everything else

2. **Set up Telegram bot** (~5 minutes)

3. **Configure initial alerts** (~15 minutes):
   - Critical systems offline
   - Disk > 90%
   - CPU/Memory > 85%

4. **Test alerts** (~10 minutes)

5. **(Optional) Set up n8n workflows** (~30-60 minutes)

6. **Fine-tune thresholds** (ongoing, based on false positives)

---

## Time Estimates

- **Telegram only**: 20-30 minutes total
- **Telegram + n8n basic**: 45-60 minutes
- **Telegram + n8n advanced**: 1-2 hours

---

## Documentation

This guide: `/root/homelab-docs/operations/beszel-alerts-guide.md`

Related:
- [Beszel Setup Guide](beszel-setup-guide.md)
- [Add Systems Guide](beszel-add-systems.md)
