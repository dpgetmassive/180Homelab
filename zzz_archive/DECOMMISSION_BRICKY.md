# Decommission Bricky - Step by Step Guide

## Current Status
- **Cluster:** springfield (3 nodes)
- **Node to Remove:** bricky (10.16.1.30, Node ID: 0x00000004)
- **Remaining Nodes:** pve-itchy (10.16.1.8), pve-scratchy (10.16.1.22)
- **Workloads on Bricky:** None running, 8 stopped VMs (3 templates, 5 test VMs)

## Pre-Decommission Decision

### Templates on Bricky
1. **VM 114:** deb-template (64GB)
2. **VM 6000:** debian12-cloudinit (20GB) - Cloud-init template
3. **VM 9000:** Template-Debian-Bookworm (3GB) - Likely the base template

### Test VMs (Can Delete)
- VM 116: winblows (8GB RAM, 64GB disk)
- VM 117: k3s-single-1 (2GB RAM, 64GB disk)
- VM 118: deb-test (2GB RAM, 64GB disk)
- VM 119: test (2GB RAM, 3GB disk)
- VM 120: tested (2GB RAM, 20GB disk)

### Decision Point
**Do you want to keep any templates?**
- If YES: Migrate templates to pve-scratchy first (87GB total)
- If NO: Skip migration, remove node directly

---

## Option A: Keep Templates (Recommended)

### Step 1: Migrate Templates to pve-scratchy

```bash
# Migrate the cloud-init template (most useful)
ssh root@10.16.1.30 "qm migrate 6000 pve-scratchy --online 0 --targetstorage zedpool"

# Migrate the base Debian Bookworm template
ssh root@10.16.1.30 "qm migrate 9000 pve-scratchy --online 0 --targetstorage zedpool"

# Optional: Migrate deb-template if needed
ssh root@10.16.1.30 "qm migrate 114 pve-scratchy --online 0 --targetstorage zedpool"
```

### Step 2: Verify Migrations
```bash
ssh root@10.16.1.22 "qm list | grep -E '6000|9000|114'"
```

---

## Option B: Skip Template Migration

If you don't need the templates, proceed directly to node removal.

---

## Decommission Procedure (Both Options)

### Step 3: Remove Node from Cluster (Run from pve-scratchy or pve-itchy)

```bash
# From pve-scratchy
ssh root@10.16.1.22 "pvecm delnode bricky"
```

This command will:
- Remove bricky from the cluster configuration
- Update all remaining nodes
- Automatically adjust corosync

### Step 4: Verify Cluster Status

```bash
ssh root@10.16.1.22 "pvecm status"
```

Expected output:
- Nodes: 2
- Quorate: Yes (if two_node is configured)
- Membership should show only itchy and scratchy

### Step 5: Configure Two-Node Cluster

**Check current corosync config:**
```bash
ssh root@10.16.1.22 "cat /etc/pve/corosync.conf"
```

**Edit corosync.conf on both remaining nodes:**

```bash
# On pve-scratchy
ssh root@10.16.1.22 "cp /etc/pve/corosync.conf /etc/pve/corosync.conf.backup"
```

You need to add/modify the quorum section. The config should include:

```
quorum {
  provider: corosync_votequorum
  two_node: 1
}
```

**Manual edit required:**
Since /etc/pve/corosync.conf is managed by pmxcfs, you should edit it through the cluster:

```bash
# On pve-scratchy, get current config
ssh root@10.16.1.22 "pvecm expected 2"
```

This sets expected votes to 2, which is the proper way for a two-node cluster.

### Step 6: Reload Corosync (if needed)

```bash
# On both nodes
ssh root@10.16.1.22 "systemctl reload corosync"
ssh root@10.16.1.8 "systemctl reload corosync"
```

### Step 7: Verify Two-Node Cluster Health

```bash
# Check cluster status
ssh root@10.16.1.22 "pvecm status"

# Should show:
# Nodes: 2
# Expected votes: 2
# Quorate: Yes

# Check corosync
ssh root@10.16.1.22 "corosync-quorumtool"
```

### Step 8: Clean Up Bricky Storage References

Check if any VMs are trying to use bricky's storage:

```bash
# On pve-scratchy
ssh root@10.16.1.22 "pvesm status | grep -v bricky"
```

Remove any storage references to bricky if they appear.

### Step 9: Optional - Wipe Bricky

If you want to completely reset bricky for other uses:

```bash
# SSH directly to bricky and remove cluster config
ssh root@10.16.1.30 "systemctl stop pve-cluster corosync"
ssh root@10.16.1.30 "pmxcfs -l"  # Local mode
ssh root@10.16.1.30 "rm /etc/corosync/*"
ssh root@10.16.1.30 "rm /etc/pve/corosync.conf"
ssh root@10.16.1.30 "killall pmxcfs"
ssh root@10.16.1.30 "systemctl start pve-cluster"
```

### Step 10: Power Down Bricky

```bash
ssh root@10.16.1.30 "shutdown -h now"
```

---

## Rollback Procedure

If something goes wrong:

1. **If cluster loses quorum:**
   ```bash
   # On remaining node, force quorum
   ssh root@10.16.1.22 "pvecm expected 1"
   ```

2. **Re-add bricky to cluster:**
   ```bash
   # On bricky
   ssh root@10.16.1.30 "pvecm add 10.16.1.22"
   ```

3. **Reset expected votes:**
   ```bash
   ssh root@10.16.1.22 "pvecm expected 3"
   ```

---

## Post-Decommission State

### Final Cluster Configuration
- **Nodes:** 2 (pve-itchy, pve-scratchy)
- **Quorum:** Two-node mode enabled
- **Expected Votes:** 2
- **Quorum Required:** 2 (both nodes must be online)

### Important Notes for Two-Node Clusters
⚠️ **Warning:** In a two-node cluster, BOTH nodes must be online for the cluster to remain quorate.
- If one node fails, the cluster will lose quorum
- You won't be able to start/stop VMs without quorum
- Consider this when planning maintenance

### Alternative: Remove Clustering
If you don't need cluster features, you could remove clustering entirely and run standalone Proxmox nodes with PBS replication for backup/recovery.

---

## Verification Checklist

After decommission:
- [ ] Cluster shows 2 nodes
- [ ] Cluster is quorate
- [ ] Expected votes = 2
- [ ] All VMs/CTs on itchy and scratchy are running
- [ ] Web UI accessible on both remaining nodes
- [ ] No references to bricky in storage config
- [ ] Templates migrated (if Option A chosen)
- [ ] Bricky powered down

---

## Next Steps

1. Test VM migration between the two remaining nodes
2. Set up replication from pve-scratchy to pve-itchy
3. Configure automated failover/power management
4. Update documentation and monitoring

---

## Storage Notes

Bricky's ZFS pool (1.81TB, 50% used = 897GB) contains:
- Stopped test VMs you likely don't need
- If there's any other data, back it up first

The physical drives can be:
- Repurposed for the remaining nodes
- Added to TrueNAS pools
- Kept as cold storage backup

---

## Time Estimate

- **With template migration:** 30-60 minutes (depends on storage speed)
- **Without template migration:** 10-15 minutes
- **Template migration time:** ~87GB at typical Proxmox speeds (1-10 Gbps network)

---

## Risk Assessment

**Risk Level:** Low

**Why:**
- No running workloads on bricky
- Test VMs and templates are replaceable
- Cluster will remain functional with 2 nodes
- Easy rollback if needed
- All critical services on other nodes

**Gotcha:**
- Two-node clusters require both nodes online for quorum
- Consider this for future maintenance planning
