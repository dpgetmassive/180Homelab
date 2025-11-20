# Proxmox Monitoring System

Real-time monitoring dashboard for 180 Homelab Proxmox infrastructure.

## Overview

Web-based monitoring dashboard providing comprehensive visibility into Proxmox cluster health, VM/CT status, resource utilization, and backup operations.

**Production Access**: http://10.16.1.18:81 (n100uck)
**Development Access**: http://localhost:81

## Features

### Cluster Overview
- **Cluster Quorum**: Real-time corosync quorum status with node count and voting information
- **Node Status**: Real-time availability and health for pve-scratchy and pve-itchy
- **Resource Gauges**: CPU load, memory usage, and storage capacity with color-coded alerts
- **Top CPU Consumer**: Identifies VMs/CTs consuming most CPU resources
- **System Metrics**: Workload counts, hardware specs, pending updates, uptime

### Metrics Display

Each Proxmox node shows detailed metrics in priority order:

1. **Workloads**: VM and container counts ("X VMs | X CTs")
2. **Hardware**: CPU cores, RAM, and available storage ("X cores | XGB RAM | XXG free")
3. **Updates**: Total and security updates available ("X total (X security)")
4. **Uptime**: System uptime in human-readable format

### Alerts and Notifications

- **ntfy Integration**: Push notifications to gmdojo-monitoring topic
- **Resource Thresholds**:
  - CPU Load: Warning at 125% (10/8 cores), Critical at 150% (12/8 cores)
  - Memory/Storage: Warning at 80%, Critical at 90%
- **Security Updates**: Highlighted in red when available
- **healthchecks.io**: Heartbeat monitoring with 15-minute check-in

### ZFS Replication Monitoring

- **Replication Status**: Current state of FileServer → DR replication
- **Last Run Time**: Timestamp of most recent replication
- **Historical Data**: Recent replication events and outcomes
- **Size Tracking**: Amount of data replicated

### Log Aggregation

- **Backup Logs**: Latest entries from orchestration script
- **System Logs**: Proxmox system events and warnings
- **Error Tracking**: Automatic highlighting of errors and failures

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Monitoring Architecture                   │
└─────────────────────────────────────────────────────────┘

Flask App (Port 81):
┌──────────────────┐
│  proxmox_status  │
│   .py (Python)   │
└────────┬─────────┘
         │
         ├─> SSH to pve-scratchy (10.16.1.22)
         │   ├─> qm list (VM status)
         │   ├─> pct list (CT status)
         │   ├─> pvecm status (cluster)
         │   └─> apt list --upgradable
         │
         ├─> SSH to pve-itchy (10.16.1.8)
         │   └─> Same commands
         │
         ├─> SSH to TrueNAS Primary (10.16.1.6)
         │   └─> midclt call replication.query
         │
         └─> ntfy.sh API (notifications)
             └─> https://ntfy.sh/gmdojo-monitoring
```

## Technical Details

### Core Technology
- **Framework**: Flask (Python 3)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Transfer**: JSON REST API with AJAX polling
- **Transport**: SSH key-based authentication for remote queries

### SSH Configuration

The monitoring system uses passwordless SSH keys configured in ~/.ssh/config:

```
Host scratchy
    HostName 10.16.1.22
    User root
    IdentityFile ~/.ssh/id_rsa

Host itchy
    HostName 10.16.1.8
    User root
    IdentityFile ~/.ssh/id_rsa
```

### Files

```
/Users/dp/developerland/homelab/monitoring/
├── proxmox_status.py          # Main Flask application
├── venv/                       # Python virtual environment
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Dependencies

```
Flask==3.0.0
requests==2.31.0
```

## Production Deployment

The monitoring dashboard is deployed on **n100uck** (10.16.1.18) - a dedicated Debian 12 host for infrastructure monitoring.

### Installation on n100uck

```bash
# Install Python dependencies
apt update && apt install -y python3-pip python3-venv

# Create monitoring directory
mkdir -p /opt/proxmox-monitoring
cd /opt/proxmox-monitoring

# Copy files (from development machine)
scp proxmox_status.py requirements.txt root@10.16.1.18:/opt/proxmox-monitoring/

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure SSH access to Proxmox nodes
ssh-keyscan -H 10.16.1.22 10.16.1.8 10.16.1.6 >> ~/.ssh/known_hosts

# Copy SSH public key to all monitored hosts
cat ~/.ssh/id_rsa.pub | ssh root@10.16.1.22 "cat >> ~/.ssh/authorized_keys"
cat ~/.ssh/id_rsa.pub | ssh root@10.16.1.8 "cat >> ~/.ssh/authorized_keys"
cat ~/.ssh/id_rsa.pub | ssh root@10.16.1.6 "cat >> ~/.ssh/authorized_keys"

# Create SSH config for aliases
cat > ~/.ssh/config <<'EOF'
Host scratchy
    HostName 10.16.1.22
    User root
    IdentityFile ~/.ssh/id_rsa

Host itchy
    HostName 10.16.1.8
    User root
    IdentityFile ~/.ssh/id_rsa
EOF
chmod 600 ~/.ssh/config

# Start monitoring service
nohup python3 proxmox_status.py > /var/log/proxmox-monitoring.log 2>&1 &
```

**Access**: http://10.16.1.18:81

### Service Management

```bash
# Check if running
lsof -ti:81

# View logs
tail -f /var/log/proxmox-monitoring.log

# Restart service
lsof -ti:81 | xargs kill -9
cd /opt/proxmox-monitoring && source venv/bin/activate && nohup python3 proxmox_status.py > /var/log/proxmox-monitoring.log 2>&1 &
```

## Development Installation

For local development:

```bash
cd /Users/dp/developerland/homelab/monitoring

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python3 proxmox_status.py
```

The app will start on http://localhost:81

## Configuration

### Node Configuration (proxmox_status.py:16-51)

```python
NODES = {
    'pve-scratchy': {
        'ip': '10.16.1.22',
        'ssh_alias': 'scratchy',
        'checks': [
            ('Workloads', 'echo "$(qm list | tail -n +2 | wc -l) VMs | $(pct list | tail -n +2 | wc -l) CTs"'),
            ('Hardware', 'echo "$(nproc) cores | $(free -g | grep Mem | awk \'{print $2}\')GB RAM | $(df -h / | tail -1 | awk \'{print $4}\') free"'),
            ('Updates', 'echo "$(apt list --upgradable 2>/dev/null | grep -v Listing | wc -l) total ($(apt list --upgradable 2>/dev/null | grep -i security | wc -l) security)"'),
            ('Uptime', 'uptime -p'),
            ('Cluster Status', 'pvecm status | grep "Quorum information" | wc -l'),
        ],
        'gauges': ['CPU Load', 'Memory Usage', 'Storage'],
        'logs': '/var/log/proxmox-backup-orchestration.log'
    },
    'pve-itchy': {
        # Similar configuration
    }
}
```

### Alert Thresholds (proxmox_status.py:1200-1210)

```python
# Load thresholds (tuned for backup operations)
if resource == 'Load':
    if percent >= 150:  # 12/8 cores - very high
        new_state = 'critical'
    elif percent >= 125:  # 10/8 cores - high but acceptable during backups
        new_state = 'warning'
else:
    # Standard thresholds for memory/storage
    if percent >= 90:
        new_state = 'critical'
    elif percent >= 80:
        new_state = 'warning'
```

### ntfy Integration

```python
NTFY_TOPIC = 'gmdojo-monitoring'
NTFY_URL = f'https://ntfy.sh/{NTFY_TOPIC}/json'
```

Subscribe to alerts:
```bash
# Web: https://ntfy.sh/gmdojo-monitoring
# Mobile: Install ntfy app, subscribe to 'gmdojo-monitoring'
```

## API Endpoints

### GET /api/status
Returns complete cluster status including:
- Node availability and metrics
- Resource gauge values (CPU, memory, storage)
- Top CPU consumer per host
- Warning/error counts

**Example Response**:
```json
{
  "nodes": {
    "pve-scratchy": {
      "reachable": true,
      "metrics": [
        {"label": "Workloads", "value": "19 VMs | 0 CTs"},
        {"label": "Hardware", "value": "12 cores | 48GB RAM | 423G free"},
        {"label": "Updates", "value": "0 total (0 security)"},
        {"label": "Uptime", "value": "up 3 days, 5 hours"},
        {"label": "Cluster Status", "value": "1"}
      ],
      "gauges": {
        "CPU Load": {"value": 45.2, "state": "ok"},
        "Memory Usage": {"value": 67.3, "state": "ok"},
        "Storage": {"value": 42.1, "state": "ok"}
      },
      "top_consumer": "100 (TrueNAS-Primary) - 12.3% CPU"
    }
  },
  "counts": {
    "up": 2,
    "down": 0,
    "warnings": 0
  }
}
```

### GET /api/logs/<node>
Returns recent log entries for specified node.

### GET /api/ntfy
Returns recent ntfy notifications from monitoring topic.

### GET /api/zfs_replication
Returns ZFS replication status from TrueNAS Primary.

## Operation

### Starting the Service

**Manual Start**:
```bash
cd /Users/dp/developerland/homelab/monitoring
source venv/bin/activate
python3 proxmox_status.py
```

**Background Start**:
```bash
cd /Users/dp/developerland/homelab/monitoring && lsof -ti:81 | xargs kill -9 2>/dev/null; sleep 1; source venv/bin/activate && python3 proxmox_status.py &
```

**Check if Running**:
```bash
lsof -ti:81
curl -s http://localhost:81/api/status | jq '.nodes | keys'
```

### Stopping the Service

```bash
lsof -ti:81 | xargs kill -9
```

### Restarting After Changes

```bash
cd /Users/dp/developerland/homelab/monitoring && lsof -ti:81 | xargs kill -9 2>/dev/null; sleep 1; source venv/bin/activate && python3 proxmox_status.py &
```

## Monitoring and Troubleshooting

### Common Issues

**Dashboard shows "Loading..." indefinitely**:
- Check Flask app is running: `lsof -ti:81`
- Check SSH connectivity: `ssh scratchy "echo test"`
- Review browser console for JavaScript errors

**Metrics not updating**:
- Check SSH key authentication is working
- Verify commands run successfully when executed manually
- Check Flask logs for Python exceptions

**ntfy notifications not appearing**:
- Verify internet connectivity
- Check ntfy.sh is accessible: `curl https://ntfy.sh/gmdojo-monitoring/json`
- Confirm NTFY_TOPIC variable is correct

**ZFS replication status not loading**:
- Check SSH access to TrueNAS: `ssh root@10.16.1.6 "echo test"`
- Verify midclt command works: `ssh root@10.16.1.6 "midclt call replication.query"`
- Check replication task name matches REPLICATION_NAME variable

### Debug Mode

Enable verbose logging by modifying proxmox_status.py:

```python
app.run(host='0.0.0.0', port=81, debug=True)
```

View detailed logs in terminal where Flask is running.

### Health Checks

**Manual API Test**:
```bash
# Get cluster status
curl -s http://localhost:81/api/status | jq '.'

# Get pve-scratchy logs
curl -s http://localhost:81/api/logs/pve-scratchy

# Get ntfy notifications
curl -s http://localhost:81/api/ntfy | jq '.[]'

# Get ZFS replication status
curl -s http://localhost:81/api/zfs_replication | jq '.'
```

**SSH Connectivity Test**:
```bash
ssh scratchy "qm list"
ssh itchy "pct list"
ssh root@10.16.1.6 "midclt call replication.query"
```

## Recent Changes

### 2025-11-20: Production Deployment
- Deployed monitoring dashboard on n100uck (10.16.1.18)
- Configured passwordless SSH access from n100uck to all monitored hosts
- Service running on dedicated Debian 12 host for 24/7 availability
- Dashboard accessible at http://10.16.1.18:81

### 2025-11-20: Cluster Quorum Monitoring
- Added cluster quorum status to top stats row
- Displays node count and voting information (e.g., "2 nodes (3/3 votes)")
- Queries corosync via `pvecm status` command
- Shows green when quorate, red when inquorate
- Removed redundant "Cluster Status" from individual node cards

### 2025-11-20: CloudSync Integration
- Added Backblaze B2 CloudSync status monitoring
- Displays CloudSync job state, progress, and last run time
- Monitors offsite backup to Backblaze B2
- Top stats row shows CloudSync summary alongside ZFS replication

### 2025-11-20: Metrics Order Fix
- Fixed metrics display order issue where Workloads appeared at bottom
- Changed metrics data structure from dictionary to array to preserve order
- Updated frontend JavaScript to iterate over array instead of object entries
- Updated warning count calculation to use array `.find()` method

### 2025-11-20: Consolidated Metrics Display
- Merged VM and LXC counts into single "Workloads" row
- Consolidated CPU cores, RAM, and storage into "Hardware" row
- Combined total and security updates into "Updates" row
- Reorganized display order: Workloads → Hardware → Updates → Uptime → Cluster Status

### 2025-11-20: Top CPU Consumer Feature
- Changed from tracking top memory consumer to top CPU consumer
- Added support for both VMs and containers
- Displays VM/CT ID, name, and CPU percentage
- Helps identify "what's smashing a box"

### 2025-11-20: Load Alert Threshold Tuning
- Raised load alert thresholds to prevent false alarms during backups
- Warning threshold: 80% → 125% (10/8 cores)
- Critical threshold: 90% → 150% (12/8 cores)
- Backups no longer trigger load alerts

### 2025-11-20: Dynamic Hardware Detection
- Changed from hardcoded CPU/RAM values to dynamic SSH queries
- Uses `nproc` for core count and `free -g` for RAM amount
- Correctly shows scratchy: 12 cores/48GB, itchy: 8 cores/32GB

### 2025-11-20: ntfy Notification Parsing
- Fixed nested JSON parsing for notifications
- Improved error handling for malformed messages
- Better display of notification titles and content

## Integration with Backup System

The monitoring system works closely with the backup orchestration:

- **Backup Status**: Tracks last successful backup via log parsing
- **Storage Monitoring**: Alerts when backup storage approaches capacity
- **Replication Tracking**: Monitors ZFS replication that protects TrueNAS data
- **Resource Alerts**: Warns if backups are impacting system resources

See [Backup System Documentation](../backups/README.md) for details.

## Future Enhancements

- [ ] Add Backblaze CloudSync job status display
- [ ] Implement "Last Successful Backup" timestamp with 24-hour alert
- [ ] Add Grafana dashboard integration
- [ ] Create historical trend graphs for resources
- [ ] Implement email alerting in addition to ntfy
- [ ] Add VM/CT drill-down pages with detailed metrics
- [ ] Create mobile-optimized responsive layout
- [ ] Add authentication for remote access

## Related Documentation

- [Backup System](../backups/README.md)
- [Infrastructure Inventory](../INVENTORY.md)
- [Network Configuration](../NETWORK.md)

---

**Last Updated**: 2025-11-20
**Status**: Active and monitoring 2 Proxmox nodes, 19 VMs/CTs
**Maintainer**: Get Massive Dojo Infrastructure Team
