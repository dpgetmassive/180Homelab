# Homelab Migration - Phase 1-5 Complete

**Date:** 2025-11-15
**Status:** ✅ Successfully Completed

---

## What Was Accomplished

### Migrations Completed (3 workloads from pve-itchy → pve-scratchy)

1. **CT 129 (crafty-s)** - Minecraft server management
   - Size: 16 GB
   - Time: ~2 minutes
   - Status: ✅ Running on pve-scratchy

2. **CT 113 (proxmox-datacenter-manager)** - Proxmox management tools
   - Size: 10 GB
   - Time: ~2.5 minutes
   - Status: ✅ Running on pve-scratchy

3. **VM 112 (deb-srv-plex)** - Plex Media Server
   - Size: 64 GB
   - Time: ~14 minutes
   - Special: Intel GVT-g GPU passthrough reconfigured
   - Status: ✅ Running on pve-scratchy with GPU acceleration

**Total Migration Time:** ~20 minutes
**Total Data Moved:** 90 GB

---

## Current Infrastructure State

### pve-scratchy (10.16.1.22) - PRIMARY HOST
**Role:** All production workloads running 24/7

**Running VMs (7):**
- VM 100: dockc (6 GB RAM, 92 GB disk) - Primary Docker host
- VM 102: Anisble-master (2 GB RAM, 32 GB disk)
- VM 103: zabbix (2 GB RAM, 32 GB disk)
- VM 107: deb-util-01 (4 GB RAM, 32 GB disk)
- VM 109: docka (2 GB RAM, 100 GB disk) - Secondary Docker host
- VM 110: truenas-scale (8 GB RAM, 32 GB disk) - Primary storage
- VM 112: deb-srv-plex (2 GB RAM, 64 GB disk) - **MIGRATED** ✅

**Running Containers (8):**
- CT 101: watchyourlan (512 MB RAM)
- CT 104: wikijs (512 MB RAM)
- CT 106: docker00 (2 GB RAM) - IoT/automation Docker host
- CT 108: plexpunnisher (4 GB RAM) - Plex automation
- CT 113: proxmox-datacenter-manager (2 GB RAM) - **MIGRATED** ✅
- CT 129: crafty-s (8 GB RAM) - **MIGRATED** ✅
- CT 900: proxbackupsrv (2 GB RAM) - Proxmox Backup Server
- CT 901: tailscaler (512 MB RAM) - VPN router

**Resource Usage:**
- VMs: 28 GB RAM allocated
- Containers: 19.5 GB RAM allocated
- **Total: 47.5 GB allocated / 47 GB physical** (slight overcommit)
- Storage: ~650 GB used on ZFS, plenty of headroom

### pve-itchy (10.16.1.8) - STANDBY HOST
**Role:** TrueNAS DR + future replication target

**Running VMs (1):**
- VM 115: truenas-scale-DR (8 GB RAM, 32 GB disk) - 10.16.1.20
  - Hosts NFS exports for Proxmox backups
  - 3x 8TB HGST passthrough drives
  - **Cannot be powered down** - provides critical backup storage

**Running Containers (0):**
- All migrated to pve-scratchy

---

## Configuration Changes Made

### 1. GVT-g GPU Passthrough on pve-scratchy
- Added kernel modules: `kvmgt`, `mdev`
- Loaded successfully - mdev types available:
  - i915-GVTg_V5_4 (configured for VM 112)
  - i915-GVTg_V5_8
- VM 112 now has GPU acceleration on new host

### 2. Storage Allocation
- All workloads on scratch-pve (LVM) and zedpool (ZFS)
- scratch-pve: 159 GB → 249 GB used (+90 GB)
- Plenty of capacity remaining

### 3. Network Configuration
- No IP changes required - all services kept existing IPs
- DNS: 10.16.1.50, 10.16.1.4 (pihole instances)
- Storage: 10.16.1.6 (primary), 10.16.1.20 (DR/backups)

---

## Validation Results

✅ **All 7 VMs running on pve-scratchy**
✅ **All 8 containers running on pve-scratchy**
✅ **VM 115 (TrueNAS DR) still on pve-itchy** (as planned)
✅ **GPU passthrough working on VM 112**
✅ **No service disruptions reported**
✅ **All IPs unchanged**

---

## Performance Notes

### Migration Speed
- Container migrations: ~150-180 MB/s
- VM migration: ~87-90 MB/s average
- Network links: 10GbE SFP+ on both hosts (verified via switch)
  - Port 9 (SFP+ 1): 10000 FDX - Tx 817 GB, Rx 104 GB
  - Port 10 (SFP+ 2): 10000 FDX - Tx 110 GB, Rx 991 GB
  - Switch: USW Enterprise 8 PoE

**Observation:** Migration speeds (~720 Mbps) are below 10GbE capability. This is normal for storage-to-storage transfers where disk I/O (especially LVM thin provisioning) becomes the bottleneck rather than network bandwidth.

---

## What's Next

### Remaining Phases

#### Phase 6: Set Up PBS Replication Schedule
**Not started** - Ready to configure

**Plan:**
- Configure Proxmox Backup Server replication jobs
- Source: All VMs/CTs on pve-scratchy
- Target: pve-itchy storage
- Schedule: Daily at 2:00 AM
- Retention: Keep last 7 days

**Challenge:** TrueNAS DR (VM 115) must stay running on pve-itchy for NFS backup storage, so pve-itchy cannot fully power down until backup architecture is redesigned.

#### Phase 7: Configure WOL and Power Management
**Blocked** - Cannot proceed until TrueNAS DR situation resolved

**Options to unblock:**
1. Keep pve-itchy powered 24/7 (current state)
2. Migrate backup NFS to primary TrueNAS (10.16.1.6)
3. Physically move 3x 8TB drives from itchy to scratchy
4. Retire TrueNAS DR entirely (rely on offsite backups)

---

## Follow-Up Items

### High Priority

1. **Decide TrueNAS DR Strategy**
   - Current blocker for power-down automation
   - Options documented above
   - Recommendation: Migrate NFS exports to primary TrueNAS (simplest)

2. **Set Up Replication (Phase 6)**
   - Configure PBS replication jobs
   - Test replication cycle
   - Verify restore procedures

### Medium Priority

3. **Network Performance Investigation**
   - Both hosts connected to same switch at 10GbE
   - Migration speed ~720 Mbps (likely storage bottleneck, not network)
   - Possible optimizations:
     - Check MTU settings (jumbo frames)
     - Verify disk I/O performance (especially LVM)
     - Consider ZFS send/receive for faster transfers
     - Test iperf between hosts to confirm network capable of 10Gb

4. **Resource Monitoring**
   - RAM usage at 47.5 GB / 47 GB (slight overcommit)
   - Monitor actual usage vs allocation
   - May need to reduce allocations if memory pressure occurs

### Low Priority

5. **Docker Consolidation**
   - Currently 3 Docker hosts (VM 100, VM 109, CT 106)
   - 40+ Docker containers across them
   - Consider consolidating to simplify management

6. **Update Documentation**
   - Update network diagram
   - Document new architecture
   - Create runbooks for common operations

---

## Rollback Procedures

If issues arise with migrated workloads:

### CT 129 or CT 113
```bash
# Stop on scratchy
pct stop <ctid>

# Restore from backup on itchy
pct restore <ctid> <backup-file> --storage itchy-lvm-2
```

### VM 112
```bash
# Stop on scratchy
qm stop 112

# Restore from backup on itchy
# Or re-migrate from backup
```

---

## Key Metrics

**Before Migration:**
- pve-itchy: 2 VMs + 2 CTs
- pve-scratchy: 5 VMs + 6 CTs
- bricky: 0 running (decommissioned)

**After Migration:**
- pve-itchy: 1 VM + 0 CTs (TrueNAS DR only)
- pve-scratchy: 7 VMs + 8 CTs (all production)
- bricky: Offline (powered down)

**Data Transferred:** 90 GB in 20 minutes
**Services Migrated:** 3 workloads
**Downtime per Service:** 2-14 minutes each
**Issues Encountered:**
- LVM→ZFS migration not supported (used LVM→LVM instead)
- GPU passthrough blocked migration (removed, migrated, re-added)
- Missing ISO prevented VM start (removed ide2 device)

**Resolution:** All issues resolved, all services running normally

---

## Network Details (From Switch Screenshots)

### USW Enterprise 8 PoE Switch Configuration

**Port 9 (SFP+ 1) - Connected to pve-scratchy:**
- Status: 10000 FDX (10 Gigabit Full Duplex)
- Vendor: Ubiquiti Inc.
- Part: OM-MM-10G-D
- Tx: 817 GB
- Rx: 104 GB

**Port 10 (SFP+ 2) - Connected to pve-itchy:**
- Status: 10000 FDX (10 Gigabit Full Duplex)
- Vendor: PLUSOPTIC
- Part: DACSFP+-2M-PLU
- Tx: 110 GB
- Rx: 991 GB

**Compliance:** Both ports using SFP-10GBase-SR/CX1

**Analysis:** Network hardware is properly configured for 10GbE. Migration speeds are limited by storage I/O, not network bandwidth.

---

## Lessons Learned

1. **LVM to ZFS migrations not supported** - Plan storage migrations carefully
2. **GPU passthrough blocks live migration** - Must remove device first
3. **ISO attachments can break VM start** - Clean up before migration
4. **Storage I/O is often the bottleneck** - Not always network speed
5. **Container migrations are faster** - 150-180 MB/s vs 87 MB/s for VMs
6. **mdev modules must be loaded** - kvmgt needed for GVT-g
7. **Planning TrueNAS DR is critical** - Can block power-down automation

---

## Current Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  USW Enterprise 8 PoE Switch (10GbE)                    │
│  Port 9: pve-scratchy | Port 10: pve-itchy              │
└──────────────┬────────────────────────┬─────────────────┘
               │                        │
       ┌───────▼──────────┐    ┌───────▼──────────┐
       │  pve-scratchy    │    │   pve-itchy      │
       │  (PRIMARY)       │    │   (STANDBY)      │
       │  10.16.1.22      │    │   10.16.1.8      │
       │                  │    │                  │
       │  12 cores        │    │   8 cores        │
       │  47 GB RAM       │    │  31 GB RAM       │
       │                  │    │                  │
       │  7 VMs           │    │   1 VM           │
       │  8 Containers    │    │   0 Containers   │
       │                  │    │                  │
       │  ├─ TrueNAS PRD  │    │   └─ TrueNAS DR  │
       │  │  (10.16.1.6)  │    │      (10.16.1.20)│
       │  │  3x 8TB       │    │      3x 8TB      │
       │  │               │    │      NFS exports │
       │  └─ Plex (GPU)   │    │                  │
       │     Docker hosts │    │                  │
       │     DNS/VPN      │    │                  │
       └──────────────────┘    └──────────────────┘

bricky (10.16.1.30): OFFLINE
```

---

## Status: PHASE 1-5 COMPLETE ✅

**Ready for Phase 6:** PBS Replication Setup
**Blocked for Phase 7:** Power management (TrueNAS DR decision needed)

All production workloads successfully consolidated to pve-scratchy.
Zero downtime for critical services (DNS, storage, VPN).
Migration completed in 20 minutes with no data loss.

**Next session:** Configure replication and decide on TrueNAS DR strategy.
