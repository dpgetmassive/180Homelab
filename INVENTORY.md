# Infrastructure Inventory

Complete inventory of all hosts in the homelab infrastructure.

**Last Updated:** 2025-11-09

## Summary

| Category | Count |
|----------|-------|
| Firewall | 1 |
| Hypervisor | 1 |
| LXC Containers | 15 |
| **Total Hosts** | **17** |

## Firewall

| Hostname | IP Address | OS | Purpose | Status |
|----------|------------|-----|---------|--------|
| opnsense01 | 10.16.1.1 | FreeBSD 14.1-RELEASE-p6 | Network firewall/router | Active |

## Hypervisor

| Hostname | IP Address | OS | CPU | RAM | Storage | Status |
|----------|------------|-----|-----|-----|---------|--------|
| pve-rover01 | 10.25.1.5 | Proxmox VE | N/A | N/A | local+data | Active |

## LXC Containers

### Media Services

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| rover-plexd | 10.25.1.11 | Debian 12 | 2 CPU, 2GB RAM | Plex Media Server | Active |
| rover-sabnzbd-old | 10.25.1.53 | Debian 12 | 2 CPU, 2GB RAM | SABnzbd (legacy) | Active |
| rova-sabnzbd | 10.25.1.14 | Debian 12 | 2 CPU, 2GB RAM | SABnzbd | Active |
| rova-transmission | 10.25.1.13 | Debian 12 | 2 CPU, 1GB RAM | Transmission BitTorrent | Active |

### Arr Services

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| rova-sonarr | 10.25.1.16 | Debian 12 | 2 CPU, 1GB RAM | TV show automation | Active |
| rova-radarr | 10.25.1.24 | Debian 12 | 2 CPU, 1GB RAM | Movie automation | Active |
| rova-filerr | 10.25.1.10 | Debian 12 | 1 CPU, 512MB RAM | File management | Active |

### Networking

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| rova-pihole | 10.25.1.15 | Debian 12 | 1 CPU, 512MB RAM | DNS + Ad blocking | Active |
| rova-tailscale | 10.25.1.18 | Debian 12 | 1 CPU, 512MB RAM | VPN mesh network | Active |
| rova-cloudflared | 10.25.1.19 | Debian 12 | 2 CPU, 512MB RAM | Cloudflare tunnel | Active |

### Monitoring

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| rova-beszel | 10.25.1.20 | Debian 12 | 1 CPU, 512MB RAM | Lightweight monitoring | Active |
| rova-checkmk | 10.25.1.22 | Debian 12 | 2 CPU, 2GB RAM | Infrastructure monitoring | Active |

### Utilities

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| rova-glance | 10.25.1.23 | Debian 12 | 1 CPU, 512MB RAM | Dashboard | Active |
| rova-docka | 10.25.1.12 | Debian 12 | 2 CPU, 2GB RAM | Docker host (Traefik, Portainer) | Active |
| rova-vscode-srv | 10.25.1.21 | Debian 12 | 1 CPU, 512MB RAM | VS Code Server | Active |

### Management

| Hostname | IP Address | OS | Resources | Purpose | Status |
|----------|------------|-----|-----------|---------|--------|
| ansible | 10.25.1.25 | Debian 12 | 2 CPU, 2GB RAM | Ansible control node | Active |

## Access Methods

### SSH Access
All hosts configured with SSH key authentication:
```bash
ssh root@<hostname/ip>
```

### Ansible Management
All hosts managed via Ansible from 10.25.1.25:
```bash
ansible all -m ping
ansible <group> -a command
```

## Ansible Groups

| Group | Hosts |
|-------|-------|
| firewall | opnsense01 |
| proxmox | pve-rover01 |
| media | rover-plexd, rover-sabnzbd-old, rova-sabnzbd, rova-transmission |
| arr_services | rova-sonarr, rova-radarr, rova-filerr |
| networking | rova-pihole, rova-tailscale, rova-cloudflared |
| monitoring | rova-beszel, rova-checkmk |
| utilities | rova-glance, rova-docka, rova-vscode-srv |
| lxc_containers | All LXC containers |
| homelab | proxmox + lxc_containers |

## Storage Configuration

All LXC containers use Proxmox storage:
- **local:** Template storage, ISOs
- **data:** LVM-thin pool for container disks

## Notes

- All LXC containers run unprivileged
- Nesting enabled where required (Docker hosts)
- SSH keys deployed from ansible host (10.25.1.25)
- Root access configured for all infrastructure hosts
