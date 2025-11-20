# Consolidated Homelab Architecture Plan
**Date:** 2025-11-15
**Goal:** Single primary host + standby with daily sync

---

## Target Architecture

### Primary Host: pve-scratchy (10.16.1.22)
**Role:** All production workloads run here 24/7

**Hardware:**
- 12 cores, 47 GB RAM
- ZFS pool (zedpool): 1.88 TB
- LVM (scratch-pve): 976 GB

**Workloads to Host:**
- All 8 VMs (currently 6 on scratchy, 2 on itchy)
- All 8 LXC containers (currently 6 on scratchy, 2 on itchy)
- TrueNAS Primary (VM 110) - 10.16.1.6
- TrueNAS DR (VM 115) - 10.16.1.20 (migrate from itchy)

### Standby Host: pve-itchy (10.16.1.8)
**Role:** Replication target, powered on once daily

**Hardware:**
- 8 cores, 31 GB RAM
- LVM (itchy-lvm-2): 976 GB

**Schedule:**
- **Wake:** Daily at 2:00 AM (WOL)
- **Receive replication** from pve-scratchy
- **Power down:** After replication completes (~3:00 AM)
- **Total uptime:** ~1 hour/day

**Purpose:**
- Disaster recovery target
- Can be manually powered on for failover
- Maintains recent copy of all VMs/containers

---

## Simplified Backup/Replication Strategy

### Daily Schedule (All at Night)

**2:00 AM - Wake Standby**
- WOL packet to pve-itchy
- Wait for boot (~3 minutes)

**2:05 AM - Start Replication**
- Proxmox Backup Server (PBS) replication from scratchy to itchy
- OR ZFS send/receive for critical VMs
- Estimated time: 30-45 minutes

**2:50 AM - Backup to TrueNAS**
- PBS/vzdump backs up critical VMs to TrueNAS NFS
- Estimated time: 10-20 minutes

**3:00 AM - Power Down Standby**
- Verify replication completed
- Graceful shutdown of pve-itchy
- Standby offline until next cycle

### What Gets Replicated Daily
1. All VM disks (incremental)
2. All container rootfs (incremental)
3. VM/CT configurations
4. Cluster configuration backup

### What Gets Backed Up Daily
1. Critical VMs (TrueNAS, Docker hosts, DNS)
2. Database dumps (MariaDB, InfluxDB)
3. Docker volume data
4. Configuration files

---

## Migration Plan - Phase by Phase

### Phase 1: Preparation (Tonight - 30 mins)
**Goal:** Prepare for migration, no service disruption

1. **Verify current backups**
   ```bash
   # Check PBS has recent backups
   ssh root@10.16.1.41 "proxmox-backup-manager backup list"
   ```

2. **Check storage capacity on pve-scratchy**
   ```bash
   # Ensure enough space for 2 more VMs + 2 CTs
   # Need: ~100 GB for VMs (Plex 64GB + TrueNAS DR 32GB)
   #       ~26 GB for CTs (10GB + 16GB)
   # Total: ~126 GB
   ```

3. **Document current IPs** (no changes planned)
   - All services keep their current IPs
   - No network reconfiguration needed

4. **Create migration checklist**
   - Order of operations
   - Rollback procedures
   - Validation steps

### Phase 2: Migrate Non-Critical Workloads (15 mins downtime each)
**Goal:** Move low-priority VMs/CTs first to test process

**Step 1: Migrate CT 129 (crafty-s - Minecraft servers)**
- Downtime acceptable: Yes (gaming server)
- Method: `pct migrate`
- Size: 16 GB
- Estimated time: 5-10 minutes

**Step 2: Migrate CT 113 (proxmox-datacenter-manager)**
- Downtime acceptable: Yes (management tool)
- Method: `pct migrate`
- Size: 10 GB
- Estimated time: 5 minutes

**Validation:**
- CTs start successfully
- Can access services
- No configuration loss

### Phase 3: Migrate VM 112 (deb-srv-plex) - Media Server
**Downtime:** ~20-30 minutes acceptable

**Challenge:** GPU passthrough (Intel GVT-g)
- Current: `hostpci0: 0000:00:02.0,mdev=i915-GVTg_V5_4`
- Need to verify pve-scratchy has compatible Intel GPU

**Options:**
- **If scratchy has iGPU:** Reconfigure passthrough, migrate VM
- **If no iGPU:** Run without GPU acceleration temporarily
- **Alternative:** Use CT 108 (plexpunnisher) instead

**Steps:**
1. Check if pve-scratchy has Intel GPU: `lspci | grep VGA`
2. Stop VM 112 on itchy
3. Migrate offline: `qm migrate 112 pve-scratchy --online 0`
4. Reconfigure GPU passthrough if available
5. Start and test

### Phase 4: Migrate VM 115 (truenas-scale-DR) - CRITICAL
**Downtime:** 10-15 minutes (backup NFS unavailable)

**Challenge:** Passthrough disks
- 3x 8TB HGST drives currently passed to pve-itchy
- **Cannot migrate with passthrough disks**

**Options:**

**Option A: Keep TrueNAS DR on pve-itchy (Recommended for now)**
- Don't migrate VM 115
- Keep pve-itchy powered on 24/7
- Postpone power-down automation until DR strategy decided
- Pros: No disruption, simple
- Cons: Can't power down itchy fully

**Option B: Physically move drives to pve-scratchy**

- Power down both hosts
- Move 3 drives from itchy to scratchy
- Reconfigure VM 115 with new disk IDs
- Migrate VM
- Pros: True consolidation
- Cons: Physical work, risk to data, both TrueNAS on one host

**Option C: Retire TrueNAS DR, use primary for backups**

- Reconfigure NFS exports to point to 10.16.1.6 (primary)
- Create backup dataset on primary TrueNAS
- Power down VM 115
- Pros: Simplified architecture
- Cons: Lose DR replica (but you have offsite backups)

**Recommendation:** Start with Option A, decide on drives later

### Phase 5: Test and Validate
**After migrations complete:**

1. **Verify all services running**
   ```bash
   # On pve-scratchy
   qm list | grep running  # Should show 8 VMs
   pct list | grep running # Should show 8 CTs
   ```

2. **Test critical services**
   - DNS: Can resolve domains?
   - Storage: TrueNAS accessible?
   - Monitoring: Grafana loading?
   - VPN: Tailscale connected?

3. **Check resource usage**
   ```bash
   pvecm status
   free -h
   df -h
   ```

4. **Verify backups still work**
   - PBS can reach storage
   - Test backup job runs

### Phase 6: Set Up Replication to Standby (Day 2)
**Once all workloads on pve-scratchy:**

1. **Configure PBS replication job**
   - Source: pve-scratchy VMs/CTs
   - Target: pve-itchy storage
   - Schedule: Daily 2:00 AM
   - Retention: Keep last 7 days

2. **Test manual replication**
   
   ```bash
   # Force a replication sync
   proxmox-backup-manager sync-job run <job-id>
   ```
   
3. **Verify replicated data**
   - Check storage usage on pve-itchy
   - Confirm backup files present

### Phase 7: Automate Power Management (Day 3)
**Set up wake-on-shutdown cycle:**

1. **Enable Wake-on-LAN on pve-itchy**
   ```bash
   # Install ethtool
   apt install ethtool
   
   # Enable WOL
   ethtool -s <interface> wol g
   
   # Make persistent
   echo 'NETDOWN=no' >> /etc/default/wakeonlan
   ```

2. **Create wake script on pve-scratchy**
   ```bash
   #!/bin/bash
   # /usr/local/bin/wake-standby.sh
   
   MAC_ADDRESS="<itchy-mac-address>"
   IP_ADDRESS="10.16.1.8"
   
   # Send WOL packet
   wakeonlan $MAC_ADDRESS
   
   # Wait for boot
   sleep 180
   
   # Verify online
   ping -c 3 $IP_ADDRESS
   ```

3. **Create replication script**
   ```bash
   #!/bin/bash
   # /usr/local/bin/replicate-to-standby.sh
   
   LOG="/var/log/replication.log"
   STANDBY="10.16.1.8"
   
   echo "[$(date)] Starting replication" >> $LOG
   
   # Run PBS replication jobs
   proxmox-backup-manager sync-job run-all
   
   # Wait for completion
   sleep 3600  # 1 hour max
   
   # Shutdown standby
   ssh root@$STANDBY "shutdown -h now"
   
   echo "[$(date)] Replication complete, standby powered down" >> $LOG
   ```

4. **Set up cron job**
   ```bash
   # On pve-scratchy
   crontab -e
   
   # Wake standby and replicate daily at 2 AM
   0 2 * * * /usr/local/bin/wake-standby.sh && /usr/local/bin/replicate-to-standby.sh
   ```

5. **Test the cycle**
   - Manually run wake script
   - Verify replication
   - Confirm auto-shutdown

---

## Resource Allocation After Consolidation

### pve-scratchy (Primary) - Expected Usage

**VMs (8 total):**
- VM 100 (dockc): 4 cores, 6 GB RAM
- VM 102 (Ansible): 2 cores, 2 GB RAM
- VM 103 (zabbix): 2 cores, 2 GB RAM
- VM 107 (deb-util): 2 cores, 4 GB RAM
- VM 109 (docka): 2 cores, 2 GB RAM
- VM 110 (truenas-scale): 4 cores, 8 GB RAM
- VM 112 (plex): 4 cores, 2 GB RAM
- VM 115 (truenas-DR): 4 cores, 8 GB RAM

**Total VM allocation:** 24 cores, 34 GB RAM

**Containers (8 total):**
- CT 101 (watchyourlan): 1 core, 0.5 GB RAM
- CT 104 (wikijs): 1 core, 0.5 GB RAM
- CT 106 (docker00): 2 cores, 2 GB RAM
- CT 108 (plexpunnisher): 4 cores, 4 GB RAM
- CT 113 (proxmox-datacenter-mgr): 2 cores, 2 GB RAM
- CT 129 (crafty-s): 4 cores, 8 GB RAM
- CT 900 (proxbackupsrv): 2 cores, 2 GB RAM
- CT 901 (tailscaler): 1 core, 0.5 GB RAM

**Total CT allocation:** 17 cores, 19.5 GB RAM

**Grand Total:**
- **Cores:** 41 allocated (on 12 physical cores = 3.4x overcommit)
- **RAM:** 53.5 GB allocated (on 47 GB physical = 1.1x overcommit)

**Status:** ⚠️ **Slight RAM overcommit**

- Actual usage typically lower than allocation
- Monitor during migration
- May need to reduce allocations if issues arise

### Storage After Consolidation

**ZFS Pool (zedpool - 1.88 TB):**
- Current: 558 GB used (30%)
- Add from itchy: ~100 GB (VMs + CTs)
- Projected: ~660 GB used (35%)
- **Status:** ✅ Plenty of space

**LVM (scratch-pve - 976 GB):**
- Current: 159 GB used (16%)
- **Status:** ✅ Available for overflow

---

## Rollback Procedures

### If Migration Fails

**For VMs:**
```bash
# Stop on target
qm stop <vmid>

# Start on source
qm start <vmid>

# Delete from target if needed
qm destroy <vmid>
```

**For Containers:**
```bash
# Stop on target
pct stop <ctid>

# Start on source (if not deleted)
pct start <ctid>

# Restore from backup if deleted
pct restore <ctid> <backup-file>
```

### If Primary Host Fails
1. Power on pve-itchy manually
2. Boot VMs from latest replication
3. Update DNS if needed
4. Restore services incrementally

---

## Migration Execution Checklist

### Pre-Migration
- [ ] Verify all backups current (< 24 hours old)
- [ ] Check storage capacity on pve-scratchy
- [ ] Document all service IPs
- [ ] Test SSH access to all nodes
- [ ] Notify users of planned downtime (if any)

### During Migration
- [ ] Migrate CT 129 (crafty-s)
- [ ] Migrate CT 113 (proxmox-datacenter-manager)
- [ ] Test migrated containers
- [ ] Migrate VM 112 (plex) - if GPU compatible
- [ ] Decide on VM 115 (TrueNAS DR) strategy
- [ ] Verify all services running
- [ ] Test critical paths (DNS, storage, VPN)

### Post-Migration
- [ ] Monitor resource usage on pve-scratchy
- [ ] Verify all services accessible
- [ ] Update monitoring/alerting
- [ ] Configure PBS replication
- [ ] Test replication job
- [ ] Set up WOL + power management
- [ ] Test automated cycle
- [ ] Update documentation

---

## Timeline Estimate

**Phase 1 (Prep):** 30 minutes
**Phase 2 (Non-critical):** 30 minutes
**Phase 3 (Plex):** 30 minutes
**Phase 4 (TrueNAS decision):** TBD
**Phase 5 (Validation):** 30 minutes
**Phase 6 (Replication setup):** 1 hour
**Phase 7 (Automation):** 1 hour

**Total active work:** ~4-5 hours
**Can be done across multiple sessions**

---

## Key Decisions Needed

1. **TrueNAS DR Strategy:**
   - Keep on itchy (prevents full power-down)
   - Move drives to scratchy (physical work, risk)
   - Retire and use primary only (simplest)

2. **Plex GPU:****Plex GPU:**
   - Check if scratchy has Intel iGPU
   - Decide if GPU acceleration required
   - Alternative: Use plexpunnisher CT

3. **Replication Method:**
   - PBS replication (recommended, built-in)
   - ZFS send/receive (more complex)
   - vzdump to shared storage (simplest)

4. **Power Schedule:**
   - Daily at 2 AM (proposed)
   - Different time?
   - Keep itchy powered 24/7 initially?

---

## Next Steps

**Ready to proceed?**

1. Answer the key decisions above
2. Start with Phase 1 (prep and checks)
3. Execute Phase 2 (migrate non-critical workloads)
4. Evaluate and continue based on results

**Or:**
- Want me to check GPU availability first?
- Need more detail on any phase?
- Want to adjust the schedule?
