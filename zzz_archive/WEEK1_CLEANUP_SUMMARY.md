# Week 1 Cleanup Summary

**Date:** 2025-11-16
**Status:** ✅ Complete

---

## Services Removed

### VM 109 (docka @ 10.16.1.12) - 5 services removed ✅

| Service | Container Name | Reason | Status |
|---------|----------------|--------|--------|
| Vaultwarden | vaultwarden | No longer needed | ✅ Removed |
| CUPS Printing | cups | No longer needed | ✅ Removed |
| OpenVPN-AS | openvpn-as | No longer needed | ✅ Removed |
| Nexterm | nexterm-nexterm-1 | No longer needed | ✅ Removed |
| Pi-hole Dev | pihole | Consolidate with production | ✅ Removed |

**VM 109 Status:** Only Portainer EE remaining (will remove after full migration)

### VM 100 (dockc @ 10.16.1.4) - 4 services removed ✅

| Service | Container Name | Reason | Status |
|---------|----------------|--------|--------|
| Minecraft Server | minecraft-server-dad-mc-1 | No longer needed | ✅ Removed |
| Homepage Dashboard | homepage | Duplicate (keeping Homer) | ✅ Removed |
| Code-server | code-server | No longer needed | ✅ Removed |
| Watchtower | watchtower | Manual updates preferred | ✅ Removed |

**VM 100 Status:** 20 containers remaining (down from 24)

---

## Current Container Inventory

### VM 100 (dockc @ 10.16.1.4) - 20 containers

**To Keep in Docker:**
- twingate-opal-python (will migrate to LXC using community script)
- cloudflared-tunnel (will migrate to LXC using community script)

**To Migrate to LXC:**
- uptime-kuma → CT 201
- gotify → CT 205
- homer → CT 204
- transmission → CT 208
- sonarr → CT 206
- sabnzbd → CT 207
- speedtest-tracker → CT 209
- speedtest2-db-1 (with speedtest)
- pihole → CT 203
- loki-stack-grafana-1 → CT 202
- loki-stack-prometheus-1 → CT 202
- loki-stack-loki-1 → CT 202
- loki-stack-influxdb-1 → CT 202
- loki-stack-promtail-1 → CT 202
- loki-stack-unpoller-1 → CT 202
- loki-stack-telegraf-1 → CT 202 (fix restart issue)

**To Remove Later:**
- traefik (after NPM fully operational)
- portainer (after migration complete)

### VM 109 (docka @ 10.16.1.12) - 1 container

**To Remove Later:**
- portainer (Portainer EE - after migration complete)

**VM 109 Decommission:** Ready to power off after Portainer removed

---

## Resource Impact

### Before Cleanup:
- VM 100: 24 containers
- VM 109: 6 containers
- **Total: 30 containers**

### After Cleanup:
- VM 100: 20 containers (-4)
- VM 109: 1 container (-5)
- **Total: 21 containers (-9)**

### RAM Impact:
- **Freed:** Estimated 1-2 GB RAM from removed containers
- **VM 109:** Nearly empty, ready for decommission

---

## Next Steps

### Immediate (Week 2):

1. **Migrate Cloudflared to LXC**
   - Use community script: https://community-scripts.github.io/ProxmoxVE/scripts?id=cloudflared
   - Create CT 210 @ 10.16.1.60
   - Configure tunnel credentials
   - Test public access to status.gmdojo.tech
   - Remove Docker container

2. **Migrate Twingate to LXC**
   - Use community script: https://community-scripts.github.io/ProxmoxVE/scripts?id=twingate-connector
   - Create CT 211 @ 10.16.1.61
   - Configure connector
   - Test zero-trust access
   - Remove Docker container

3. **Begin Phase 2 Service Migrations**
   - Uptime Kuma → CT 201
   - Homer Dashboard → CT 204
   - Gotify → CT 205

### Medium-term (Weeks 3-7):

4. **Migrate Monitoring Stack** (Weeks 3-4)
5. **Migrate Pi-hole** (Weeks 4-5)
6. **Migrate Media Services** (Weeks 6-7)

### Long-term (Week 8+):

7. **Plex Database Migration**
   - Migrate watch history from VM 112 → CT 108
   - Power off VM 112
   - Delete VM 112 after 1 week

8. **Decommission VMs**
   - VM 109: Power off after Cloudflared/Twingate migrated
   - VM 100: Reduce to minimal size or decommission after all migrations
   - VM 112: Delete after Plex database migrated

9. **Remove Traefik & Portainer**
   - Stop Traefik after all NPM proxies working
   - Remove both Portainer instances
   - Clean up old domain references

---

## Benefits Realized

### Week 1 Accomplishments:

✅ **9 unused services removed** (5 from VM 109, 4 from VM 100)
✅ **~1-2 GB RAM freed**
✅ **VM 109 nearly empty** (ready for decommission)
✅ **Cleaner infrastructure** (easier to see what's actually used)
✅ **Risk reduced** (fewer attack surfaces)

### Next Phase Benefits:

📋 **Better isolation** (each service in own LXC)
📋 **Easier management** (individual snapshots, backups, restarts)
📋 **Resource visibility** (clear per-service resource usage)
📋 **Simplified architecture** (fewer Docker hosts)

---

## Updated LXC Allocation Plan

| VMID | Service | IP | RAM | Disk | Week |
|------|---------|----|----|------|------|
| 200 | nginx-proxy-manager | 10.16.1.50 | 1 GB | 8 GB | ✅ Phase 1 |
| 201 | uptime-kuma | 10.16.1.51 | 512 MB | 5 GB | Week 2 |
| 202 | monitoring-stack | 10.16.1.52 | 4 GB | 50 GB | Week 3-4 |
| 203 | pihole | 10.16.1.53 | 512 MB | 5 GB | Week 4-5 |
| 204 | homer | 10.16.1.54 | 256 MB | 2 GB | Week 2 |
| 205 | gotify | 10.16.1.55 | 256 MB | 2 GB | Week 2 |
| 206 | sonarr | 10.16.1.56 | 1 GB | 20 GB | Week 6 |
| 207 | sabnzbd | 10.16.1.57 | 512 MB | 10 GB | Week 6 |
| 208 | transmission | 10.16.1.58 | 512 MB | 10 GB | Week 6 |
| 209 | speedtest-tracker | 10.16.1.59 | 512 MB | 5 GB | Week 7 |
| 210 | cloudflared | 10.16.1.60 | 256 MB | 2 GB | Week 2 ⭐ NEW |
| 211 | twingate-connector | 10.16.1.61 | 256 MB | 2 GB | Week 2 ⭐ NEW |

---

## Success Metrics

### Week 1 Goals: ✅ Complete

- [x] Remove 9+ unused services
- [x] Free up 1-2 GB RAM
- [x] Prepare VM 109 for decommission
- [x] Identify all remaining services to migrate

### Overall Migration Goals:

- [ ] 13 services migrated to LXC
- [ ] 3 VMs decommissioned (100, 109, 112)
- [ ] Traefik removed (old proxy)
- [ ] Both Portainer instances removed
- [ ] Old domain (`*.local.getmassive.com.au`) deprecated
- [ ] New domain (`*.gmdojo.tech`) fully operational
- [ ] Better resource isolation and management

---

**Status:** Week 1 complete, ready for Week 2
**Next Action:** Migrate Cloudflared and Twingate to LXCs using community scripts
