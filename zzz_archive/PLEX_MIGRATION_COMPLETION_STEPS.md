# Plex Migration - Completion Steps

**Status:** Waiting for cluster quorum (pve-itchy to boot)

---

## Current Situation

1. **Plex migration is 90% complete:**
   - ✅ CT 108 backed up (4.1 GB)
   - ✅ VM 112 database backed up (7.5 GB)
   - ✅ VM 112 database copied to `/tmp/plex-vm112-migration.tar.gz` (6.5 GB)
   - ⚠️ **Manual transfer needed** to complete migration

2. **DNS issue discovered:**
   - CT 108 is configured with DNS 10.16.1.50 (NPM - not a DNS server)
   - This causes 5+ second timeouts for external lookups
   - **This is why the Plex UI was sluggish**

3. **Cluster quorum issue:**
   - pve-itchy (10.16.1.8) is offline
   - Need quorum to make config changes through Proxmox API
   - Currently booting pve-itchy to restore quorum

---

## Once pve-itchy is Online (Quorum Restored)

### Step 1: Fix DNS on CT 108

Run in pve-scratchy Shell:

```bash
pct set 108 --nameserver 10.16.1.1,1.1.1.1
pct set 108 --searchdomain gm.local
```

### Step 2: Complete Plex Migration

**Option A: HTTP Server Method (Easiest)**

In VM 112 console:
```bash
cd /tmp
python3 -m http.server 8888 &
```

In CT 108 console (after starting it):
```bash
cd /tmp
wget http://10.16.1.18:8888/plex-vm112-migration.tar.gz
cd "/var/lib/plexmediaserver/Library/Application Support"
tar xzf /tmp/plex-vm112-migration.tar.gz
chown -R plex:plex "Plex Media Server"
systemctl start plexmediaserver
```

**Option B: SCP Method**

From your Mac:
```bash
# Copy from VM 112 to local
scp dp@10.16.1.18:/tmp/plex-vm112-migration.tar.gz ~/Downloads/

# Copy to CT 108
scp ~/Downloads/plex-vm112-migration.tar.gz root@10.16.1.36:/tmp/

# SSH to CT 108 and extract
ssh root@10.16.1.36
cd "/var/lib/plexmediaserver/Library/Application Support"
tar xzf /tmp/plex-vm112-migration.tar.gz
chown -R plex:plex "Plex Media Server"
systemctl start plexmediaserver
```

### Step 3: Test Plex

```bash
# Check Plex is running
ssh root@10.16.1.36 "systemctl status plexmediaserver"

# Open in browser
open http://10.16.1.36:32400/web
```

**Verify:**
- Libraries visible
- Watch history preserved (check a TV series)
- No DNS timeouts (should be fast now)

### Step 4: Fix DNS on Other Affected Containers

```bash
# On pve-scratchy Shell:
pct set 101 --nameserver 10.16.1.1,1.1.1.1
pct set 129 --nameserver 10.16.1.1,1.1.1.1
pct set 901 --nameserver 10.16.1.1,1.1.1.1

# Restart containers
pct restart 101
pct restart 129
pct restart 901
```

### Step 5: Power Off VM 112 (After Validation)

Once Plex on CT 108 is confirmed working:

```bash
# On pve-itchy (or through cluster UI):
qm shutdown 112
```

---

## Rollback Plan (If Something Goes Wrong)

If Plex doesn't work properly on CT 108:

```bash
# Stop Plex
pct exec 108 -- systemctl stop plexmediaserver

# Remove migrated database
pct exec 108 -- rm -rf "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server"

# Restore old database
pct exec 108 -- mv "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server.old" "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server"

# Start Plex
pct exec 108 -- systemctl start plexmediaserver
```

**Result:** CT 108 back to pre-migration state (working, but without watch history)

---

## Files & Locations

```
VM 112 (10.16.1.18):
├── /var/lib/plexmediaserver/... (original, 7.5 GB) ✅
├── /tmp/plex-export/Plex Media Server/ (copy, 7.5 GB) ✅
└── /tmp/plex-vm112-migration.tar.gz (compressed, 6.5 GB) ✅ READY FOR TRANSFER

CT 108 (10.16.1.36):
├── /var/lib/plexmediaserver/.../Plex Media Server.old (backup, 4.1 GB) ✅
└── /tmp/plex-ct108-backup-*.tar.gz (full backup, 4.1 GB) ✅

Proxmox Host (10.16.1.22):
└── Multiple temp files from transfer attempts
```

---

## Why We Hit These Issues

1. **File transfer**: Proxmox `qm guest exec` can't reliably pipe large binary files (6.5 GB)
2. **DNS misconfiguration**: 10.16.1.50 (NPM) doesn't run DNS, causing timeouts
3. **Cluster quorum**: 2-node cluster needs both nodes online for configuration changes

**All issues have workarounds** - nothing is broken, just needs manual completion!

---

## Summary

**What's working:**
- ✅ All backups created safely
- ✅ VM 112 database ready for transfer
- ✅ Easy rollback available
- ✅ GPU acceleration already configured on CT 108

**What needs to be done:**
- ⏳ Wait for pve-itchy to boot (in progress)
- ⏳ Fix DNS settings (2 minutes)
- ⏳ Complete file transfer (10 minutes)
- ⏳ Test Plex (5 minutes)

**Total time remaining:** ~20 minutes after quorum restored
