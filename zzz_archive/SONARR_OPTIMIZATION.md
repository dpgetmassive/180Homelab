# Sonarr Quality Optimization - November 2025

**Date:** 2025-11-15
**Objective:** Configure Sonarr to prevent downloading oversized media files (4-5 GB episodes)

---

## Problem Statement

After 8 months offline, Sonarr was downloading excessively large files:
- TV episodes: 4+ GB instead of 2 GB
- Movies (future): 50-60 GB instead of 3-5 GB
- Cause: No size limits, accepting 4K/REMUX releases, season packs

---

## Changes Made

### 1. Quality Profile Updates

**Updated all 119 series** from mixed profiles to standardized HD profiles:

**Before:**
- 37 series on Profile 1 (Any) - includes SD qualities
- 5 series on Profile 4 (HD-1080p only)
- 89 series on Profile 6 (HD-720p/1080p)

**After:**
- 0 series on Profile 1
- 5 series on Profile 4 (HD-1080p only)
- 114 series on Profile 6 (HD-720p/1080p)

### 2. Quality Size Limits

Set maximum file sizes **per minute of content** for each quality level:

| Quality | Min (MB/min) | Max (MB/min) | Preferred (MB/min) | Example: 45min episode |
|---------|--------------|--------------|-------------------|----------------------|
| SDTV | 2 | 100 | 95 | ~4.5 GB |
| HDTV-720p | 2 | 35 | 30 | ~1.6 GB |
| WEBDL-720p | 2 | 35 | 30 | ~1.6 GB |
| WEBRip-720p | 2 | 35 | 30 | ~1.6 GB |
| Bluray-720p | 2 | 50 | 40 | ~2.3 GB |
| HDTV-1080p | 3 | 55 | 45 | ~2.5 GB |
| WEBDL-1080p | 3 | 55 | 45 | ~2.5 GB |
| WEBRip-1080p | 3 | 55 | 45 | ~2.5 GB |
| Bluray-1080p | 4 | 65 | 55 | ~2.9 GB |

**Key Changes from defaults:**
- 720p: Reduced from 130 MB/min to 35 MB/min (5.85 GB → 1.6 GB per episode)
- 1080p: Reduced from 130 MB/min to 55 MB/min (5.85 GB → 2.5 GB per episode)

**Implementation:**
```python
# Quality Definition updates via API
size_limits = {
    'HDTV-720p': {'min': 2, 'max': 35, 'preferred': 30},
    'HDTV-1080p': {'min': 3, 'max': 55, 'preferred': 45},
    # ... etc
}
```

### 3. Release Profile Configuration

Created Release Profile (ID: 1) to block unwanted releases:

**Ignored Terms (always rejected):**
- `2160p`
- `4K`
- `UHD`
- `REMUX`
- `Bluray-REMUX`
- `BDRemux`
- `BD-Remux`
- `Season`
- `Complete`

**API Configuration:**
```json
{
  "enabled": true,
  "required": [],
  "ignored": [
    "2160p", "4K", "UHD", "REMUX",
    "Bluray-REMUX", "BDRemux", "BD-Remux",
    "Season", "Complete"
  ],
  "indexerId": 0,
  "tags": []
}
```

### 4. Indexer Configuration

**NZBgeek (Primary Usenet Indexer):**
- Base URL: `https://api.nzbgeek.info`
- API Path: `/api`
- Categories: 5030, 5040, 5045, 2030, 2040, 2045, 2050
- RSS: Enabled
- Automatic Search: Enabled
- Interactive Search: Enabled
- Priority: 25

---

## Limitations Discovered

### Season Pack Issue

**Problem:** Size limits don't effectively block season packs.

**Why:**
- Sonarr calculates "size per episode" for season packs differently
- Quality size limits primarily apply to individual episode releases
- Season packs bypass individual episode size restrictions

**Impact:**
- Backlog searches (8+ months) tend to find season packs
- Season packs can be 5-8 GB total (still better than 4K versions)
- Individual episodes for current/recent shows work better

**Workaround:**
- Release profile blocks terms "Season" and "Complete"
- Partial effectiveness (doesn't catch all season pack naming schemes)
- Manual queue management required for oversized downloads

---

## Expected Results

### For New Episodes (as they air):
✓ Individual releases within size limits (1.6-2.5 GB for HD)
✓ 4K/REMUX releases rejected
✓ Proper quality preferences (WEB-DL/WEBRip preferred over large Blurays)

### For Backlog Episodes:
⚠️ May still find season packs (5-8 GB for entire seasons)
⚠️ Individual episodes less commonly available for older content
✓ Still blocks 4K/REMUX (prevents 40-60 GB season packs)

### Size Comparison:
| Scenario | Old Behavior | New Behavior | Savings |
|----------|--------------|--------------|---------|
| 45min episode (1080p) | 5.85 GB | 2.5 GB | 57% |
| 10-episode season | 58.5 GB | 25 GB | 57% |
| 121 missing episodes | 601 GB | 255 GB | 58% |

---

## Configuration Files

### Sonarr Quality Definitions

**Location:** Set via API endpoint `/api/v3/qualitydefinition/{id}`

**Script:** `/tmp/sonarr_quality_defs_updated.json`

### Release Profile

**Location:** Set via API endpoint `/api/v3/releaseprofile/1`

**Current Configuration:**
```bash
curl -X GET "http://10.16.1.4:8989/api/v3/releaseprofile/1?apikey=API_KEY"
```

### Series Profile Assignments

**Script used:** `/tmp/update_sonarr_profiles.py`

Updates all series from Profile 1 (Any) to Profile 6 (HD-720p/1080p):
```python
series['qualityProfileId'] = 6
```

---

## Testing & Validation

### Initial Search Results:
- **121 missing episodes** across 16 series
- Found: 10 episodes (all season packs - removed)
- Re-search after configuration: Better results expected for individual episodes

### Series with Missing Content:
- Poker Face (2023): 12 episodes
- Star Wars: Andor: 12 episodes
- Hacks: 10 episodes
- The Last of Us: 7 episodes
- MobLand: 7 episodes
- Others: 73 episodes across 11 series

---

## Maintenance

### Monitoring Downloads:
```bash
# Check Sonarr queue
curl "http://10.16.1.4:8989/api/v3/queue?apikey=API_KEY" | jq

# Check SABnzbd queue
curl "http://10.16.1.4:8080/api?mode=queue&apikey=SAB_API_KEY&output=json" | jq
```

### Manual Quality Check:
1. Navigate to Sonarr → Series → Episodes
2. Click "Manual Search" for specific episodes
3. Review file sizes before grabbing
4. Reject season packs if individual episodes preferred

### Future Improvements:
1. Add additional indexers with better individual episode coverage
2. Consider migrating from Docker to LXC for better Proxmox integration
3. Implement Radarr with same quality settings for movies
4. Monitor RSS feeds for automatic quality improvements over time

---

## Related Services

### SABnzbd Configuration
- **Port:** 8080
- **API Key:** b97043f56c774b8d9ba78d26a34dbab4
- **Download Path:** Configured in SABnzbd settings
- **Integration:** Sonarr → Download Clients → SABnzbd

### Sonarr API Access
- **Port:** 8989
- **API Key:** f5696191fb0e49ec8e28babfa8ad2e15
- **Web UI:** http://10.16.1.4:8989

---

## Troubleshooting

### Downloads Still Too Large?

1. **Check Quality Profile:**
   ```bash
   curl "http://10.16.1.4:8989/api/v3/series/{id}?apikey=API_KEY" | jq '.qualityProfileId'
   ```

2. **Verify Quality Definitions:**
   ```bash
   curl "http://10.16.1.4:8989/api/v3/qualitydefinition?apikey=API_KEY" | jq
   ```

3. **Check Release Profile:**
   ```bash
   curl "http://10.16.1.4:8989/api/v3/releaseprofile?apikey=API_KEY" | jq
   ```

### Season Packs Still Downloading?

- Release profile blocking is partial
- Manually remove from queue via Sonarr UI
- Consider adding to blocklist to prevent re-download
- Wait for individual episode releases (RSS feeds)

---

**Status:** ✓ Configuration Complete
**Last Updated:** 2025-11-15
**Next Review:** Monitor for 2-4 weeks, adjust if needed
