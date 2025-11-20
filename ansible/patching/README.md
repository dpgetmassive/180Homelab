# Ansible Automated Patching System

Automated patch management system for 180 Homelab infrastructure with daily status reporting, asset auto-discovery, and optional automatic patching.

## Overview

This system provides:
- **Daily patch status reporting** with HTML dashboards
- **Automatic asset discovery** from Proxmox (VMs and LXC containers)
- **Zero-downtime patching** via serial execution
- **Scheduled automation** via cron
- **Optional automatic patching** (disabled by default for safety)

## Architecture

### Control Node
- **n100uck** (10.16.1.18) - Ansible control node
- All scripts and playbooks run from here
- Reports generated to `/opt/ansible/reports/`

### Managed Infrastructure (19 hosts)
- 2 Proxmox hosts
- 2 TrueNAS systems
- 2 Infrastructure nodes
- 11 LXC Containers
- 2 VMs

## Components

### 1. Patch Status Report (`patch_status_report.yml`)
**Location**: `/opt/ansible/playbooks/patch_status_report.yml`

Ansible playbook that:
- Checks all hosts for available updates
- Identifies systems requiring reboots
- Generates HTML report with visual status dashboard
- Tracks system uptime and last update time

**Output**: `/opt/ansible/reports/patch-status-YYYY-MM-DD.html`

### 2. Asset Auto-Discovery (`ansible_auto_discovery.sh`)
**Location**: `/usr/local/bin/ansible_auto_discovery.sh`

Bash script that:
- Scans Proxmox hosts for VMs and containers
- Discovers IP addresses via guest agent and ARP
- Updates Ansible inventory automatically
- Maintains inventory backups
- Generates discovery reports

**Features**:
- Auto-discovers new VMs/containers
- Updates inventory dynamically
- Network scanning for IP discovery
- Validates inventory syntax before applying

### 3. Daily Automation Orchestrator (`ansible_daily_automation.sh`)
**Location**: `/usr/local/bin/ansible_daily_automation.sh`

Master script that:
- Orchestrates all automation tasks
- Runs asset discovery
- Generates patch status reports
- Optionally applies patches (if enabled)
- Cleans up old reports (keeps 30 days)
- Sends notifications (if mail configured)

**Environment Variables**:
- `AUTO_PATCH_ENABLED=true` - Enable automatic patching (default: false)

### 4. Quick Patch All (`quick_patch_all.yml`)
**Location**: `/opt/ansible/playbooks/quick_patch_all.yml`

Ansible playbook for patching:
- Updates APT cache
- Performs dist-upgrade
- Auto-removes unnecessary packages
- Patches 3 hosts at a time (`serial: 3`)
- Patches LXC containers via `pct exec`
- Checks for reboot requirements

## Installation

### Prerequisites
```bash
# On Ansible control node (n100uck)
apt-get update
apt-get install ansible nmap sshpass
```

### Deploy Files

```bash
# Copy playbooks
scp patch_status_report.yml root@10.16.1.18:/opt/ansible/playbooks/
scp quick_patch_all.yml root@10.16.1.18:/opt/ansible/playbooks/

# Copy scripts
scp ansible_auto_discovery.sh root@10.16.1.18:/usr/local/bin/
scp ansible_daily_automation.sh root@10.16.1.18:/usr/local/bin/

# Set permissions
ssh root@10.16.1.18 "chmod +x /usr/local/bin/ansible_*.sh"

# Create directories
ssh root@10.16.1.18 "mkdir -p /opt/ansible/reports /var/log/ansible-automation"
```

### Configure Cron Schedule

```bash
ssh root@10.16.1.18 "cat > /etc/cron.d/ansible-automation <<'EOF'
# Ansible Automation - Daily Patching and Reporting

# Daily patch status report (runs at 2 AM)
0 2 * * * root /usr/local/bin/ansible_daily_automation.sh >> /var/log/ansible-automation/cron.log 2>&1

# Weekly asset auto-discovery (runs every Sunday at 1 AM)
0 1 * * 0 root /usr/local/bin/ansible_auto_discovery.sh >> /var/log/ansible-automation/cron.log 2>&1
EOF
chmod 644 /etc/cron.d/ansible-automation"
```

## Usage

### Manual Commands

**Run patch status report:**
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-playbook playbooks/patch_status_report.yml"
```

**Run asset discovery:**
```bash
ssh root@10.16.1.18 "/usr/local/bin/ansible_auto_discovery.sh"
```

**Dry run patch all:**
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-playbook playbooks/quick_patch_all.yml --check"
```

**Patch all infrastructure:**
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-playbook playbooks/quick_patch_all.yml"
```

**Patch specific host:**
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-playbook playbooks/quick_patch_all.yml --limit dockc"
```

**Patch specific group:**
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-playbook playbooks/quick_patch_all.yml --limit containers"
```

### View Reports

**Latest patch status:**
```bash
ssh root@10.16.1.18 "ls -lh /opt/ansible/reports/"
```

**View automation logs:**
```bash
ssh root@10.16.1.18 "tail -f /var/log/ansible-automation/daily-automation.log"
ssh root@10.16.1.18 "tail -f /var/log/ansible-automation/ansible-discovery.log"
```

## Configuration

### Enable Automatic Patching

```bash
# WARNING: This will automatically patch systems daily at 2 AM
ssh root@10.16.1.18 "echo 'AUTO_PATCH_ENABLED=true' >> /etc/environment"
```

### Customize Schedule

Edit `/etc/cron.d/ansible-automation` on n100uck:
```cron
# Change time (currently 2 AM daily)
0 2 * * * root /usr/local/bin/ansible_daily_automation.sh ...

# Change discovery frequency (currently weekly Sunday 1 AM)
0 1 * * 0 root /usr/local/bin/ansible_auto_discovery.sh ...
```

### Exclude Hosts from Patching

Modify inventory or use `--limit`:
```bash
# Exclude TrueNAS systems
--limit '!truenas'

# Only patch containers
--limit containers

# Exclude specific hosts
--limit '!dockc,!docka'
```

## Features

### Zero-Downtime Patching
- Uses `serial: 3` to patch hosts in batches
- Services remain running during updates
- Only reboots if explicitly required (detected but not automatic)

### Asset Auto-Discovery
- Automatically finds new Proxmox VMs and containers
- Updates inventory without manual intervention
- Discovers IP addresses via multiple methods:
  - QEMU guest agent
  - MAC address → ARP table lookup
  - LXC container introspection

### Status Reporting
- HTML dashboard with color-coded status
- Shows available updates per host
- Identifies systems requiring reboots
- Tracks system uptime and kernel versions
- Historical reports kept for 30 days

### Safety Features
- Automatic patching disabled by default
- Dry run mode available (`--check`)
- Inventory backups before changes
- Syntax validation before applying
- Excludes critical systems (TrueNAS) by default
- Serial execution prevents mass outages

## Troubleshooting

### Check Ansible Connectivity
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible all -m ping --one-line"
```

### Verify Inventory
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible-inventory --list | grep ansible_host"
```

### Test Individual Host
```bash
ssh root@10.16.1.18 "cd /opt/ansible && ansible dockc -m command -a 'apt list --upgradable'"
```

### Check Cron Execution
```bash
ssh root@10.16.1.18 "tail -100 /var/log/ansible-automation/cron.log"
```

### Fix SSH Access

If hosts show as unreachable, add SSH keys:
```bash
# Via Proxmox guest agent
PUBKEY=$(ssh root@10.16.1.18 'cat /root/.ssh/id_ed25519.pub')
ssh scratchy "qm guest exec <VMID> -- bash -c 'mkdir -p /root/.ssh && chmod 700 /root/.ssh && echo \"$PUBKEY\" >> /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys'"
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Ansible Control Node                      │
│                   n100uck (10.16.1.18)                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐    ┌─────────────────────────────┐   │
│  │ Cron Scheduler    │───▶│ Daily Automation            │   │
│  │ - 2 AM Daily      │    │ ansible_daily_automation.sh │   │
│  │ - 1 AM Sunday     │    └──────────┬──────────────────┘   │
│  └──────────────────┘               │                       │
│                                     │                       │
│              ┌──────────────────────┴───────────────────┐   │
│              │                                          │   │
│         ┌────▼────────┐                    ┌───────────▼──┐│
│         │ Asset       │                    │ Patch Status ││
│         │ Discovery   │                    │ Report       ││
│         │             │                    │              ││
│         └────┬────────┘                    └───────┬──────┘│
│              │                                      │       │
│      ┌───────▼────────┐              ┌─────────────▼─────┐│
│      │ Update         │              │ HTML Reports      ││
│      │ Inventory      │              │ /opt/ansible/     ││
│      │                │              │ reports/          ││
│      └────────────────┘              └───────────────────┘│
└─────────────────────────────────────────────────────────────┘
                          │
           ┌──────────────┴──────────────┐
           │                             │
    ┌──────▼──────┐              ┌──────▼──────┐
    │  Proxmox    │              │  Managed    │
    │  Hosts      │              │  Systems    │
    │  - scratchy │              │  - 19 total │
    │  - itchy    │              │  - VMs      │
    └─────────────┘              │  - LXCs     │
                                 │  - Hosts    │
                                 └─────────────┘
```

## File Structure

```
/opt/ansible/
├── inventories/
│   └── homelab.yml              # Main inventory (auto-updated)
├── playbooks/
│   ├── patch_status_report.yml  # Status reporting playbook
│   └── quick_patch_all.yml      # Patching playbook
└── reports/
    └── patch-status-*.html      # Generated reports

/usr/local/bin/
├── ansible_auto_discovery.sh    # Asset discovery script
└── ansible_daily_automation.sh  # Master automation script

/var/log/ansible-automation/
├── daily-automation.log         # Daily automation logs
├── ansible-discovery.log        # Discovery logs
└── cron.log                     # Cron execution logs

/etc/cron.d/
└── ansible-automation           # Cron schedule
```

## Security Considerations

1. **SSH Keys**: All managed systems use SSH key authentication
2. **No Passwords**: Password authentication disabled on most systems
3. **Limited Scope**: Ansible user is root (required for system updates)
4. **Audit Trail**: All actions logged
5. **Manual Approval**: Automatic patching disabled by default
6. **Backup**: Inventory backed up before changes

## Performance

- **Patch Status Report**: ~10 seconds for 19 hosts
- **Full Patching Run**: ~6 minutes (depends on updates available)
- **Asset Discovery**: ~30-60 seconds
- **Report Generation**: <5 seconds

## Maintenance

### Regular Tasks
- Review patch status reports weekly
- Check automation logs monthly
- Verify inventory accuracy after infrastructure changes
- Test disaster recovery procedures quarterly

### Cleanup
Reports and logs are automatically cleaned:
- Patch reports: 30 days
- Automation logs: 90 days
- Discovery logs: 90 days

## Support

For issues or questions:
1. Check logs in `/var/log/ansible-automation/`
2. Verify connectivity with `ansible all -m ping`
3. Review cron execution logs
4. Test playbooks manually with `--check` mode

## Version History

- **v1.0** (2025-11-20) - Initial release
  - Patch status reporting
  - Asset auto-discovery
  - Daily automation
  - Zero-downtime patching
  - 19 hosts managed

## License

MIT License - See repository root for details

## Author

180 Homelab Infrastructure Team
