# Plex Database Migration Plan

**Date:** 2025-11-16
**Goal:** Migrate Plex watch history/metadata from VM 112 to CT 108 (plexpunnisher)

---

## Current Situation

**Source:** VM 112 (deb-srv-plex) - Has current watch history and metadata
**Target:** CT 108 (plexpunnisher @ 10.16.1.36) - Already running Plex Media Server

**Problem:** CT 108 is running Plex, but VM 112 has the up-to-date watch progress for TV series.

---

## Migration Strategy

### Option 1: Database Merge (Recommended)

Merge the watch history from VM 112 into CT 108's existing Plex database.

**Steps:**

1. **Backup both Plex databases**
   ```bash
   # VM 112 (if we can access it)
   ssh root@<VM112-IP> "systemctl stop plexmediaserver"
   ssh root@<VM112-IP> "tar czf /tmp/plex-vm112-backup.tar.gz /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/"

   # CT 108 (plexpunnisher)
   ssh root@10.16.1.22 "pct exec 108 -- systemctl stop plexmediaserver"
   ssh root@10.16.1.22 "pct exec 108 -- tar czf /tmp/plex-ct108-backup.tar.gz /var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/"
   ```

2. **Identify VM 112's IP address**
   ```bash
   ssh root@10.16.1.22 "qm guest cmd 112 network-get-interfaces" | grep ip-address
   ```

3. **Copy VM 112 database to local machine**
   ```bash
   scp root@<VM112-IP>:/var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db /tmp/plex-vm112.db
   ```

4. **Copy CT 108 database to local machine**
   ```bash
   scp root@10.16.1.36:/var/lib/plexmediaserver/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db /tmp/plex-ct108.db
   ```

5. **Analyze databases**
   ```bash
   sqlite3 /tmp/plex-vm112.db "SELECT COUNT(*) FROM metadata_item_views;"
   sqlite3 /tmp/plex-ct108.db "SELECT COUNT(*) FROM metadata_item_views;"
   ```

6. **Use Plex's built-in migration (safest)**
   - Stop Plex on CT 108
   - Replace entire database from VM 112 → CT 108
   - Start Plex on CT 108
   - Let Plex rescan and match existing media
   - **Note:** This assumes both are using the same library structure

### Option 2: Manual Watch History Export/Import

Use Plex Trakt sync or similar tools to export/import watch history.

**Steps:**

1. **Install Trakt.tv plugin on VM 112 Plex**
2. **Sync watch history to Trakt**
3. **Install Trakt.tv plugin on CT 108 Plex**
4. **Import watch history from Trakt**

**Note:** Requires Trakt.tv account (free)

### Option 3: Fresh Start (Not Recommended)

Accept loss of watch history and start fresh on CT 108.

---

## Recommended Approach

**Use Option 1 - Database Replacement**

Since CT 108 is already running and you want to preserve watch history:

1. **Stop Plex on both systems**
2. **Backup both databases** (safety)
3. **Copy VM 112's entire Plex database directory** to CT 108
4. **Start Plex on CT 108**
5. **Verify libraries and watch history**
6. **Test with a few TV series** to confirm watch progress preserved
7. **If successful, power off VM 112**
8. **Monitor for 1 week**
9. **Delete VM 112**

---

## Database Locations

**Standard Plex Database Path:**
```
/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/
```

**Key files to migrate:**
- `Plug-in Support/Databases/com.plexapp.plugins.library.db` (main database)
- `Plug-in Support/Databases/com.plexapp.plugins.library.blobs.db` (metadata)
- `Plug-in Support/Preferences.xml` (settings)
- `Media/` (thumbnails, artwork)

---

## Pre-Migration Checklist

- [ ] Identify VM 112's IP address
- [ ] Verify SSH access to VM 112
- [ ] Verify Plex is stopped on VM 112
- [ ] Create backup of CT 108 Plex database
- [ ] Verify same Plex version on both systems
- [ ] Document library paths on both systems
- [ ] Verify TrueNAS media mounts are same on both

---

## Post-Migration Validation

- [ ] All libraries visible in CT 108 Plex
- [ ] Watch history preserved (check a few TV shows)
- [ ] Recently watched/recently added working
- [ ] Plex dashboard showing correct statistics
- [ ] Remote access working (if configured)
- [ ] Mobile apps can connect
- [ ] No errors in Plex logs

---

## Rollback Plan

If migration fails:
1. Stop Plex on CT 108
2. Restore backup: `tar xzf /tmp/plex-ct108-backup.tar.gz`
3. Start Plex on CT 108
4. Start Plex on VM 112 (temporary fallback)

---

## Timeline

**Estimated time:** 1-2 hours

**Recommended window:** During low usage period (late evening/early morning)

**Downtime:** ~30 minutes (while copying database)

---

**Status:** Ready to execute when user has time
**Next Step:** Identify VM 112's IP address and verify access
