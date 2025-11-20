# Claude Code Memory - Homelab Consolidation Project

## Session Context (2025-11-15)

### What We Did
1. Connected to 3 Proxmox nodes via SSH with sshpass
2. Discovered complete infrastructure:
   - 3-node cluster (pve-itchy, pve-scratchy, bricky)
   - 15 total VMs (7 running)
   - 8 LXC containers (all running)
   - 40+ Docker containers across multiple hosts
3. Mapped all network configurations and IPs
4. Documented storage utilization (ZFS, LVM, NFS)
5. Identified special hardware (GPU passthrough, USB devices, 6x 8TB drives)
6. Created comprehensive discovery report: `HOMELAB_DISCOVERY.md`

### Key Findings
- **pve-scratchy** is best candidate for primary (12 cores, 47GB RAM, most workloads)
- **pve-itchy** is best candidate for standby (8 cores, 31GB RAM, underutilized)
- **bricky** should be decommissioned (only 15GB RAM, just templates)

### User's Goal
Consolidate to 1 primary host + 1 standby that:
- Replicates on schedule
- Powers down after replication
- Can be failover target

### Critical Services Identified
- DNS (multiple pihole instances)
- TrueNAS (2 instances, 6x 8TB passthrough drives)
- Monitoring (Grafana/Prometheus/Loki stack)
- VPN (Tailscale, OpenVPN)
- Proxmox Backup Server
- Docker workloads across 3 hosts

### Access Information
- Network: 10.16.1.0/24
- Credentials: root / Getmassiv3, dp / Getmassiv3
- Hosts:
  - 10.16.1.8 (pve-itchy)
  - 10.16.1.22 (pve-scratchy)
  - 10.16.1.30 (bricky)

### Files Created
1. `/Users/dp/developerland/homelab/HOMELAB_DISCOVERY.md` - Complete infrastructure documentation
2. `/Users/dp/developerland/homelab/CLAUDE_DESKTOP_PLANNING_PROMPT.md` - Planning session prompt
3. `/Users/dp/developerland/homelab/CLAUDE_CODE_MEMORY.md` - This file

### Bricky Decommission (COMPLETED 2025-11-15)
**Status:** Successfully removed from cluster
- Executed `pvecm delnode bricky` from pve-scratchy
- Cluster automatically adjusted to 2 nodes
- Expected votes: 2, Quorum: 2, Quorate: Yes
- All workloads continued running without interruption
- Bricky powered down (10.16.1.30 offline)
- Templates and test VMs on bricky not migrated (can recover if needed)

**Current Cluster State:**
- pve-itchy (10.16.1.8): 8 cores, 31 GB RAM - 2 VMs + 2 CTs running
- pve-scratchy (10.16.1.22): 12 cores, 47 GB RAM - 6 VMs + 6 CTs running
- Two-node cluster "springfield", config version 8

### Migration Complete (Phases 1-5 - 2025-11-15)
**Status:** ✅ Successfully completed in ~20 minutes

**Workloads Migrated from pve-itchy to pve-scratchy:**
- CT 129 (crafty-s): 16 GB, 2 min
- CT 113 (proxmox-datacenter-manager): 10 GB, 2.5 min
- VM 112 (deb-srv-plex): 64 GB, 14 min with GPU reconfiguration

**Current State:**
- pve-scratchy: 7 VMs + 8 containers (ALL production workloads)
- pve-itchy: 1 VM (TrueNAS DR only) - cannot power down yet
- bricky: Offline (decommissioned)

**Key Changes:**
- Configured Intel GVT-g on pve-scratchy for Plex GPU passthrough
- All workloads consolidated to primary host
- Network verified: 10GbE SFP+ on both hosts (USW Enterprise 8 PoE switch)

### Next Steps
**Phase 6:** Set up PBS replication (ready to start)
**Phase 7:** Power management (BLOCKED - TrueNAS DR decision needed)

**Follow-up Items:**
1. Investigate network performance (migration ~720 Mbps, likely storage I/O bottleneck)
2. Decide TrueNAS DR strategy (blocks power-down automation)
3. Configure replication schedule
4. Monitor RAM usage (47.5 GB allocated / 47 GB physical)

### What to Remember When User Returns
- Read `HOMELAB_DISCOVERY.md` for full context
- Ask user to share or paste the migration plan from Claude Desktop
- Be ready to:
  - Write migration scripts
  - Execute commands via sshpass on the Proxmox hosts
  - Create backup procedures
  - Set up replication automation
  - Configure power management for standby host
  - Test failover procedures

### Important Notes
- All backed up offsite - safe to experiment
- User prefers minimal downtime for critical services
- Media services can have extended downtime
- User is technically capable (Linux, Docker, Proxmox experience)
- Password reuse is acknowledged and accepted by user

### Technical Environment
- Working directory: `/Users/dp/developerland/homelab`
- sshpass installed and working
- Can execute remote commands on all 3 Proxmox nodes
- Python available for parsing JSON responses

### Conversation Continuity
When user returns, start with:
1. "Welcome back! I've reviewed the discovery we completed earlier."
2. Ask for the migration plan from Claude Desktop
3. Confirm understanding of the plan
4. Begin implementation phase by phase
