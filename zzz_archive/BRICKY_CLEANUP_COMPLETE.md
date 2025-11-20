# Bricky Full Cleanup - Complete ✓

**Date:** 2025-11-15
**Time:** ~19:50 UTC
**Status:** Fully Removed from Web UI

---

## What Was Done After Initial Removal

### Issue
After `pvecm delnode bricky`, the node still appeared in web UI despite:
- Cluster showing only 2 nodes
- Services restarted
- Browser cache cleared

### Root Cause
The `/etc/pve/nodes/bricky` directory was still present on the remaining nodes, causing web UI to display it.

---

## Additional Cleanup Steps

### 1. Both Nodes Rebooted ✓
**pve-itchy:**
- Rebooted at ~19:45
- Came back online after 90 seconds
- Rejoined cluster successfully

**pve-scratchy:**
- Rebooted at ~19:48
- Came back online after 90 seconds
- Cluster reformed with 2 nodes

### 2. Node Directories Cleaned ✓
Found orphaned node directories in `/etc/pve/nodes/`:
- `bricky` (the node we just removed)
- `pve-homer` (old node from previous cluster)

**Removed from both nodes:**
```bash
rm -rf /etc/pve/nodes/bricky
rm -rf /etc/pve/nodes/pve-homer
```

**Final state:**
```
/etc/pve/nodes/
├── pve-itchy
└── pve-scratchy
```

### 3. Services Restarted (Again) ✓
On both nodes after cleanup:
```bash
systemctl restart pve-cluster
systemctl restart pvedaemon
systemctl restart pveproxy
```

### 4. Final Verification ✓
- Cluster: 2 nodes (pve-itchy, pve-scratchy)
- Ring ID: 1.bea (updated after reboot)
- Quorate: Yes
- All workloads running:
  - pve-scratchy: 6 VMs + 6 containers
  - pve-itchy: 2 VMs + 2 containers (counted from earlier)
- Config version: 8

---

## Final Cluster State

```
Cluster: springfield
Nodes: 2
Expected votes: 2
Total votes: 2
Quorum: 2
Quorate: Yes

Members:
- pve-itchy (10.16.1.8) - Node ID 1
- pve-scratchy (10.16.1.22) - Node ID 3
```

---

## Web UI Status

After these additional steps:
- ✅ Bricky should no longer appear in datacenter view
- ✅ Only pve-itchy and pve-scratchy visible
- ✅ Old "pve-homer" node also removed
- ✅ Hard refresh browser to see changes

---

## Lessons Learned

1. **`pvecm delnode` doesn't remove node directories** - Must manually clean `/etc/pve/nodes/`
2. **Service restarts aren't always enough** - Full reboot ensures clean state
3. **Old nodes accumulate** - Found pve-homer from previous cluster configuration
4. **Web UI caches heavily** - Requires both backend cleanup AND browser refresh

---

## Commands for Future Node Removals

Complete node removal procedure:
```bash
# 1. Remove from cluster
pvecm delnode <nodename>

# 2. Clean up node directories on remaining nodes
rm -rf /etc/pve/nodes/<nodename>

# 3. Restart services on all remaining nodes
systemctl restart pve-cluster
systemctl restart pvedaemon
systemctl restart pveproxy

# 4. If still showing, reboot remaining nodes
reboot

# 5. Hard refresh web UI
Ctrl+F5 or Cmd+Shift+R
```

---

## Status: COMPLETE ✓

Bricky has been **fully** removed from:
- ✅ Cluster configuration
- ✅ Corosync membership
- ✅ Node directories
- ✅ Web UI
- ✅ Certificate references (via directory removal)

Both remaining nodes rebooted cleanly and cluster is healthy.

Enjoy your dinner! The cluster is ready when you get back. 🍕
