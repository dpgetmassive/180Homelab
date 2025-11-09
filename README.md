# Homelab Documentation

Comprehensive documentation for the rova.getmassive.com.au homelab infrastructure.

**Last Updated:** 2025-11-09

## Quick Links

- [Infrastructure Inventory](INVENTORY.md) - All hosts, IPs, and specifications
- [Network Documentation](NETWORK.md) - Network topology and configuration
- [Services Catalog](SERVICES.md) - All running services and access URLs
- [Ansible Guide](ansible/README.md) - Automation and management
- [Service Guides](services/) - Individual service documentation

## Infrastructure Overview

### Management
- **Ansible Control Node:** 10.25.1.25 (ansible)
- **Proxmox Host:** 10.25.1.5 (pve-rover01)
- **Firewall:** 10.16.1.1 (opnsense01)

### Key Services
- **Reverse Proxy:** Traefik (rova-docka) - *.rova.getmassive.com.au
- **Media Server:** Plex (rover-plexd)
- **Monitoring:** CheckMK (rova-checkmk), Beszel (rova-beszel)
- **Container Management:** Portainer (rova-docka)

### Statistics
- **Total Hosts:** 17 (1 firewall, 1 proxmox, 15 LXC containers)
- **Network Segments:** 2 (10.25.1.0/24 homelab, 10.16.1.0/24 management)
- **Public Domain:** *.rova.getmassive.com.au (Cloudflare + Traefik)

## Quick Start

### Access Ansible Control Node
```bash
ssh root@10.25.1.25
```

### Check All Hosts Status
```bash
ansible all -m ping
```

### Update All Hosts
```bash
ansible-playbook /root/update-hosts.yml
```

## Emergency Contacts

- **Primary Admin:** dp@getmassive.com.au
- **Firewall Web UI:** https://10.16.1.1
- **Proxmox Web UI:** https://10.25.1.5:8006

## Repository Structure

```
homelab-docs/
├── README.md                 # This file
├── INVENTORY.md             # Complete host inventory
├── NETWORK.md               # Network documentation
├── SERVICES.md              # Service catalog
├── ansible/
│   └── README.md           # Ansible usage guide
└── services/
    ├── traefik.md          # Traefik/reverse proxy
    └── docker.md           # Docker infrastructure
```

## Maintenance Schedule

- **Updates:** Managed via Ansible, run as needed
- **Backups:** (To be documented)
- **Certificate Renewal:** Automatic via Traefik + Let's Encrypt

## Notes

- All LXC containers run Debian 12 (Bookworm)
- Firewall runs OPNsense on FreeBSD 14.1
- SSH key authentication configured for all hosts
- Ansible manages infrastructure from 10.25.1.25
