# Plex Database Migration - Live Progress

**Start Time:** 2025-11-16 21:16 (local time on pve-scratchy)
**Status:** IN PROGRESS

---

## Step-by-Step Progress

### ✅ Step 1: Stop Plex Services
- CT 108 (plexpunnisher): ✅ Stopped
- VM 112 (deb-srv-plex): ✅ Stopped

### ✅ Step 2: Backup Current Databases
- **CT 108 backup:** ✅ Complete - 4.1 GB
  - Location: `/tmp/plex-ct108-backup-20251116-211606.tar.gz` on CT 108
  - This is your rollback if things go wrong!

- **VM 112 backup:** 🔄 Running in background
  - Creating tar.gz of 7.5 GB database
  - Will take a few minutes

### 🔄 Step 3: Copy VM 112 Database to CT 108
- **Status:** Currently copying 7.5 GB from VM 112 → /tmp/plex-export/
- **Progress:** 3.1 GB copied so far (41% complete)
- **Estimated time:** ~5-10 more minutes

- **Old CT 108 database:** ✅ Renamed to `.old` (safety backup)

### ⏳ Step 4: Move Database to Final Location (Pending)
Will copy from VM 112's /tmp to CT 108's /var/lib/plexmediaserver/

### ⏳ Step 5: Start Plex and Validate (Pending)
- Start Plex on CT 108
- Check libraries visible
- Verify watch history preserved
- Test with a few TV shows

### ⏳ Step 6: Power Off VM 112 (Pending)
After successful validation

---

## Database Sizes

| Location | Size | Notes |
|----------|------|-------|
| VM 112 original | 7.5 GB | Source (has watch history) |
| CT 108 original | 4.1 GB | Target (backed up as .old) |
| CT 108 backup | 4.1 GB | Safety backup in /tmp |

---

## Safety Measures in Place

✅ **CT 108 full backup** created before any changes
✅ **Old CT 108 database** renamed to .old (can restore instantly)
✅ **VM 112 backup** being created (extra safety)
✅ **VM 112 Plex stopped** (no data corruption during copy)
✅ **CT 108 Plex stopped** (clean migration)

---

## Rollback Plan (if needed)

If something goes wrong, here's how to restore:

```bash
# Stop Plex
pct exec 108 -- systemctl stop plexmediaserver

# Remove new database
pct exec 108 -- rm -rf "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server"

# Restore old database
pct exec 108 -- mv "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server.old" "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server"

# Start Plex
pct exec 108 -- systemctl start plexmediaserver
```

---

## Expected Completion Time

- **Copying:** ~10 more minutes (3.1/7.5 GB done)
- **Moving to final location:** ~5 minutes
- **Starting & validation:** ~5 minutes
- **Total remaining:** ~20-25 minutes

---

**Current Status:** Copy operation in progress, all safety backups in place
**Next Update:** When copy completes (7.5 GB transferred)
