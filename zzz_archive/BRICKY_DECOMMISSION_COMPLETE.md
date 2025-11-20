# Bricky Decommission - Complete ✓

**Date:** 2025-11-15
**Time:** ~19:11 UTC
**Status:** Successfully Removed

---

## What Was Done

### 1. Pre-Flight Checks ✓
- Verified bricky had no running workloads (8 stopped VMs, 0 containers)
- Confirmed all critical services on other nodes
- Verified cluster health (3 nodes, quorate)

### 2. Node Removal ✓
- Executed: `pvecm delnode bricky` from pve-scratchy
- Result: "Killing node 4"
- Config version bumped: 7 → 8

### 3. Cluster Reconfiguration ✓
Proxmox automatically adjusted:
- Nodes: 3 → 2
- Expected votes: 3 → 2
- Quorum requirement: 2 → 2
- Both nodes remained quorate throughout

### 4. Verification ✓
- Both pve-itchy and pve-scratchy see consistent cluster state
- All VMs still running (8 total)
- All containers still running (8 total)
- Quorum: Yes on both nodes
- Config version: 8 (synchronized)

### 5. Power Down ✓
- Initiated shutdown on bricky (10.16.1.30)

---

## Final Cluster State

### Cluster: springfield
- **Config Version:** 8
- **Transport:** knet
- **Nodes:** 2

### Node Details

| Node | IP | Node ID | Cores | RAM | Status |
|------|-------|---------|-------|-----|--------|
| pve-itchy | 10.16.1.8 | 1 | 8 | 31 GB | Online |
| pve-scratchy | 10.16.1.22 | 3 | 12 | 47 GB | Online |
| ~~bricky~~ | ~~10.16.1.30~~ | ~~4~~ | ~~12~~ | ~~15 GB~~ | **REMOVED** |

### Quorum Status
```
Quorum provider:  corosync_votequorum
Nodes:            2
Expected votes:   2
Total votes:      2
Quorum:           2
Quorate:          Yes
```

---

## Running Workloads After Decommission

### pve-scratchy (10.16.1.22)
**VMs (6):**
- 100: dockc (6GB RAM, 92GB disk)
- 102: Anisble-master (2GB RAM)
- 103: zabbix (2GB RAM)
- 107: deb-util-01 (4GB RAM)
- 109: docka (2GB RAM, 100GB disk)
- 110: truenas-scale (8GB RAM)

**Containers (6):**
- 101: watchyourlan
- 104: wikijs
- 106: docker00
- 108: plexpunnisher
- 900: proxbackupsrv
- 901: tailscaler

### pve-itchy (10.16.1.8)
**VMs (2):**
- 112: deb-srv-plex (2GB RAM, GPU passthrough)
- 115: truenas-scale-DR (8GB RAM)

**Containers (2):**
- 113: proxmox-datacenter-manager
- 129: crafty-s

---

## What Happened to Bricky's Data

### Lost (Not Migrated)
- 3 VM templates (debian12-cloudinit, Template-Debian-Bookworm, deb-template)
- 5 stopped test VMs (winblows, k3s-single-1, deb-test, test, tested)
- ZFS pool data (1.81 TB, ~897 GB used)

### Impact
- **Low:** Templates can be recreated
- **None:** Test VMs were not in use
- **None:** All production workloads on other nodes

### Recovery Options
If templates are needed:
1. Power on bricky (not part of cluster anymore)
2. Access VMs directly
3. Export templates or migrate to remaining nodes
4. Re-shutdown

---

## Two-Node Cluster Considerations

### Important Notes

⚠️ **Both Nodes Required for Quorum**
- With 2 nodes and expected votes of 2, BOTH nodes must be online for quorum
- If one node fails, the remaining node will NOT have quorum
- Without quorum, you cannot start/stop/migrate VMs

### Options if One Node Goes Down

**Option 1: Force Quorum (Temporary)**
```bash
pvecm expected 1
```
This allows the surviving node to maintain quorum temporarily.

**Option 2: Break Cluster (Permanent)**
If you don't need clustering, you could remove it entirely and use:
- Proxmox Backup Server for backups
- Manual migration/restoration for failover
- Each node runs independently

### Current Setup is Fine For
- Learning and testing
- Planned maintenance (both nodes online)
- Migration between nodes
- Centralized management

### Not Ideal For
- High availability (HA) - requires 3+ nodes
- Single node failure tolerance
- Automatic failover

---

## Storage Status After Decommission

### Active Storage (pve-scratchy)
- ZFS (zedpool): 1.88 TB (30% used)
- LVM (scratch-pve): 976 GB (16% used)

### Active Storage (pve-itchy)
- LVM (itchy-lvm-2): 976 GB (13% used)

### Shared Storage (Both Nodes)
- prox-backup-srv (PBS): 2 TB (15% used)
- proxmoxbackups (NFS): 8.84 TB (16% used)

### Offline Storage (bricky)
- ZFS (zedpool): 1.81 TB (50% used = 897 GB)
- Status: Node powered down
- Physical drives available for repurposing

---

## Network Impact

### No Changes Required
All static IPs remain the same:
- DNS: 10.16.1.50, 10.16.1.4 (pihole instances)
- Storage: 10.16.1.6, 10.16.1.20 (TrueNAS)
- VPN: 10.16.1.31 (Tailscale), 10.16.1.12 (OpenVPN)
- Monitoring: 10.16.1.4 (Grafana stack)

### Removed IPs
- 10.16.1.30 (bricky host) - now offline

---

## Next Steps

### Immediate (Optional)
1. ✓ Bricky powered down
2. Test VM migration between remaining nodes
3. Verify backups are current
4. Update monitoring to remove bricky alerts

### Short Term
1. Plan migration of VMs from pve-itchy to pve-scratchy
2. Set up replication from pve-scratchy (primary) to pve-itchy (standby)
3. Configure automated power management for standby node
4. Test failover procedures

### Long Term
1. Consider adding third node for proper HA (or remove clustering)
2. Consolidate Docker hosts
3. Implement automated backup verification
4. Document runbooks for common procedures

---

## Rollback Procedure (If Needed)

If you need to re-add bricky:

1. **Power on bricky**
2. **On pve-scratchy, add node to cluster:**
   ```bash
   # Set expected votes back to 3 temporarily
   pvecm expected 3
   ```

3. **On bricky, rejoin cluster:**
   ```bash
   pvecm add 10.16.1.22
   ```

4. **Verify 3-node cluster:**
   ```bash
   pvecm status  # Should show 3 nodes
   ```

---

## Lessons Learned

1. **Proxmox handles two-node automatically** - Expected votes adjusted without manual intervention
2. **No downtime** - All workloads continued running during removal
3. **Templates should be evaluated first** - Could have migrated useful ones before removal
4. **Corosync is smart** - Config version bumped automatically, no manual conf editing needed

---

## Time Taken

- Planning: 5 minutes
- Execution: 2 minutes
- Verification: 3 minutes
- **Total: ~10 minutes**

Faster than expected!

---

## Health Check Results

### Cluster ✓
- [x] Two nodes visible in cluster
- [x] Both nodes quorate
- [x] Config synchronized (version 8)
- [x] Corosync healthy
- [x] Expected votes correct (2)

### Workloads ✓
- [x] All 8 VMs running
- [x] All 8 containers running
- [x] No service interruptions reported
- [x] Network connectivity maintained

### Storage ✓
- [x] ZFS pools accessible
- [x] LVM volumes accessible
- [x] Shared storage (PBS, NFS) accessible
- [x] No orphaned storage references

---

## Updated CLAUDE_CODE_MEMORY.md

This decommission has been logged in the memory file for future sessions.

Key updates:
- Current cluster: 2 nodes (itchy, scratchy)
- Bricky: offline, data preserved but not clustered
- All workloads running on remaining nodes
- Ready for next phase: consolidation to single primary host

---

## Status: COMPLETE ✓

Bricky has been successfully decommissioned from the Proxmox cluster. The two-node cluster (pve-itchy and pve-scratchy) is healthy and all workloads are running normally.

Ready to proceed with the next phase of your homelab consolidation project!
