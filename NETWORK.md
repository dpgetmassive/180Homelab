# Network Documentation

Network topology and configuration for the homelab infrastructure.

**Last Updated:** 2025-11-09

## Network Overview

The homelab uses two main network segments with external access through Cloudflare and Traefik.

## Network Segments

### Management Network: 10.16.1.0/24
- **Gateway:** 10.16.1.1 (OPNsense)
- **Purpose:** Firewall management and administration

### Homelab Network: 10.25.1.0/24  
- **Gateway:** 10.25.1.1
- **DNS:** 10.25.1.15 (Pi-hole)
- **Purpose:** All homelab services and containers

## Public Domain: *.rova.getmassive.com.au

All services accessible via:
1. **Cloudflare DNS** - Manages domain records
2. **Cloudflare DDNS** (10.25.1.12) - Keeps IP updated
3. **Traefik** (10.25.1.12:80/443) - Reverse proxy with SSL
4. **Backend Services** - Routed based on hostname

### Published Services
- traefik-dashboard.rova → Traefik dashboard
- proxmox1.rova → Proxmox UI (10.25.1.5:8006)
- sonar.rova → Sonarr (10.25.1.16:8989)
- portainer.rova → Portainer (10.25.1.12:9443)
- sabnzb.rova → SABnzbd (10.25.1.14:7777)
- plex.rova → Plex (10.25.1.11:32400)
- cmk-mon.rova → CheckMK (10.25.1.22)

## SSL/TLS Configuration

- **Provider:** Let's Encrypt
- **Certificate:** Wildcard for *.rova.getmassive.com.au
- **Challenge Type:** DNS-01 via Cloudflare API
- **Renewal:** Automatic via Traefik
- **Storage:** /dockerland/traefik/acme.json

## Port Forwarding

External ports 80 and 443 forwarded to Traefik (10.25.1.12)

## See Also

- [INVENTORY.md](INVENTORY.md) - Complete host listing
- [SERVICES.md](SERVICES.md) - Service catalog with URLs
- [services/traefik.md](services/traefik.md) - Traefik configuration details
